"""
WooCommerce Adapter for VendStack.

Implements WooCommerce REST API (v3) for orders, products, and inventory.
Auth: REST API with Consumer Key + Secret (OAuth 1.0a or Application Password)
Docs: https://woocommerce.github.io/woocommerce-rest-api-docs/
"""
import time
import hmac
import hashlib
import base64
import json
import logging
import urllib.request
import urllib.parse
import secrets
from datetime import datetime
from typing import List, Optional, Dict, Any
from adapters.base import ChannelAdapter

logger = logging.getLogger(__name__)


class WooCommerceAdapter(ChannelAdapter):
    """Real WooCommerce REST API adapter."""

    def __init__(self, config: dict):
        self.url = config.get('url', '').rstrip('/')  # e.g. 'https://shop.example.com'
        self.consumer_key = config.get('consumer_key')
        self.consumer_secret = config.get('consumer_secret')
        self.version = config.get('version', 'wc/v3')

        if not all([self.url, self.consumer_key, self.consumer_secret]):
            raise ValueError(
                "WooCommerce adapter requires: url, consumer_key, consumer_secret. "
                "Generate in WP Admin → WooCommerce → Settings → Advanced → REST API."
            )

        self.api_url = f'{self.url}/wp-json/{self.version}'

    # ── Auth (OAuth 1.0a) ────────────────────────────────────────────────────

    def _oauth_sign(self, method: str, path: str, params: dict = None) -> str:
        """Generate OAuth 1.0a Authorization header."""
        params = params or {}
        oauth_params = {
            'oauth_consumer_key': self.consumer_key,
            'oauth_timestamp': int(time.time()),
            'oauth_nonce': secrets.token_hex(8),
            'oauth_signature_method': 'HMAC-SHA256',
            'oauth_version': '1.0',
        }

        # Combine params
        all_params = {**params, **oauth_params}
        sorted_params = sorted(all_params.items())

        # Create signature base string
        base_string = (
            method.upper() + '&' +
            urllib.parse.quote(path, safe='') + '&' +
            urllib.parse.quote('&'.join(
                f'{urllib.parse.quote(str(k), safe="")}={urllib.parse.quote(str(v), safe="")}'
                for k, v in sorted_params
            ), safe='')
        )

        # Create signing key
        signing_key = f'{self.consumer_secret}&'

        # Generate signature
        signature = hmac.new(
            signing_key.encode(),
            base_string.encode(),
            hashlib.sha256
        ).digest()
        oauth_params['oauth_signature'] = base64.b64encode(signature).decode()

        # Build Authorization header
        auth_header = 'OAuth ' + ', '.join(
            f'{urllib.parse.quote(str(k), safe="")}="{urllib.parse.quote(str(v), safe="")}"'
            for k, v in sorted(oauth_params.items())
        )
        return auth_header

    def _request(self, method: str, path: str,
                 params: dict = None, body: dict = None) -> dict:
        """Make an authenticated WooCommerce API call."""
        url = f'{self.api_url}{path}'
        if params:
            url += '?' + urllib.parse.urlencode(params)

        auth_header = self._oauth_sign(method.upper(), url)

        headers = {
            'Authorization': auth_header,
            'Content-Type': 'application/json',
        }

        data = json.dumps(body).encode() if body else None
        req = urllib.request.Request(url, data=data, headers=headers, method=method.upper())

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            body_str = e.read().decode()
            logger.error(f'[WooCommerce] API error {e.code}: {body_str[:200]}')
            raise

    # ── Orders ──────────────────────────────────────────────────────────────

    def fetch_orders(self, since: datetime) -> List[dict]:
        """
        Fetch orders from WooCommerce REST API.
        GET /orders?after={ISO date}&status=processing,completed,etc.
        """
        logger.info(f'[WooCommerce] Fetching orders since {since.isoformat()}')
        all_orders = []
        page = 1
        per_page = 100

        params = {
            'after': since.strftime('%Y-%m-%dT%H:%M:%S'),
            'per_page': per_page,
            'page': page,
        }

        while True:
            try:
                # Build URL manually for OAuth signing
                url = f'{self.api_url}/orders'
                if params:
                    url += '?' + urllib.parse.urlencode({k: str(v) for k, v in params.items()})

                auth_header = self._oauth_sign('GET', url)
                req = urllib.request.Request(
                    url,
                    headers={'Authorization': auth_header, 'Content-Type': 'application/json'},
                    method='GET'
                )

                with urllib.request.urlopen(req, timeout=30) as resp:
                    orders_raw = json.loads(resp.read())
            except Exception as e:
                logger.error(f'[WooCommerce] Order fetch failed: {e}')
                break

            if not orders_raw:
                break

            for raw in orders_raw:
                order = self._normalize_order(raw)
                if order:
                    all_orders.append(order)

            if len(orders_raw) < per_page:
                break

            page += 1
            params['page'] = page

        logger.info(f'[WooCommerce] Fetched {len(all_orders)} orders')
        return all_orders

    def _normalize_order(self, raw: dict) -> Optional[dict]:
        """Convert WooCommerce order to VendStack NormalizedOrder."""
        try:
            billing = raw.get('billing', {}) or {}
            shipping = raw.get('shipping', {}) or {}

            items = []
            for item in raw.get('line_items', []):
                items.append({
                    'sku': item.get('sku', ''),
                    'title': item.get('name', ''),
                    'qty': int(item.get('quantity', 1)),
                    'price': float(item.get('price', 0) or 0),
                    'image_url': '',
                })

            status_map = {
                'pending': 'pending',
                'on-hold': 'pending',
                'auto-draft': 'draft',
                'processing': 'pending',
                'completed': 'shipped',
                'cancelled': 'cancelled',
                'refunded': 'cancelled',
                'failed': 'cancelled',
            }

            return {
                'channel': 'woocommerce',
                'channel_order_id': str(raw.get('id', '')),
                'order_number': raw.get('number', str(raw.get('id', ''))),
                'order_date': raw.get('date_created', ''),
                'status': status_map.get(raw.get('status', ''), 'pending'),
                'customer': {
                    'name': f"{billing.get('first_name', '')} {billing.get('last_name', '')}",
                    'email': billing.get('email', ''),
                    'phone': billing.get('phone', ''),
                    'address': {
                        'line1': shipping.get('address_1', ''),
                        'line2': shipping.get('address_2', ''),
                        'city': shipping.get('city', ''),
                        'postcode': shipping.get('postcode', ''),
                        'country': shipping.get('country', ''),
                    }
                },
                'items': items,
                'subtotal': float(raw.get('subtotal', 0) or 0),
                'shipping': float(raw.get('shipping_total', 0) or 0),
                'tax': float(raw.get('total_tax', 0) or 0),
                'total': float(raw.get('total', 0) or 0),
                'currency': raw.get('currency', 'GBP'),
                'tracking_number': '',
                'carrier': '',
                'woo_order_id': raw.get('id'),
            }
        except Exception as e:
            logger.error(f'[WooCommerce] Failed to normalize order: {e}')
            return None

    # ── Tracking ───────────────────────────────────────────────────────────

    def push_tracking(self, order_id: str, tracking: str, carrier: str) -> bool:
        """
        Add tracking info to a WooCommerce order.
        WooCommerce doesn't have native tracking — store as order meta.
        Also update status to completed.
        """
        logger.info(f'[WooCommerce] Adding tracking to order {order_id}: {tracking} ({carrier})')

        try:
            # Update order with tracking meta and set to completed
            body = {
                'status': 'completed',
                'meta_data': [
                    {'key': '_tracking_number', 'value': tracking},
                    {'key': '_tracking_carrier', 'value': carrier},
                ]
            }
            self._request('PUT', f'/orders/{order_id}', body=body)
            return True
        except Exception as e:
            logger.error(f'[WooCommerce] Failed to update tracking: {e}')
            return False

    # ── Products / Listings ─────────────────────────────────────────────────

    def fetch_listings(self) -> List[dict]:
        """
        Fetch products from WooCommerce.
        GET /products?per_page=100
        """
        logger.info('[WooCommerce] Fetching products')
        all_products = []
        page = 1
        per_page = 100

        while True:
            try:
                url = f'{self.api_url}/products'
                params = {'per_page': per_page, 'page': page}
                url_with_params = url + '?' + urllib.parse.urlencode({k: str(v) for k, v in params.items()})

                auth_header = self._oauth_sign('GET', url_with_params)
                req = urllib.request.Request(
                    url_with_params,
                    headers={'Authorization': auth_header},
                    method='GET'
                )

                with urllib.request.urlopen(req, timeout=30) as resp:
                    products = json.loads(resp.read())
            except Exception as e:
                logger.error(f'[WooCommerce] Product fetch failed: {e}')
                break

            if not products:
                break

            for prod in products:
                images = prod.get('images', [])
                price = prod.get('price', '0')

                for variant in prod.get('variations', []):
                    var_price = variant.get('price', price)
                    all_products.append({
                        'channel': 'woocommerce',
                        'sku': variant.get('sku', prod.get('sku', '')),
                        'title': prod.get('name', ''),
                        'description': prod.get('description', ''),
                        'price': float(var_price or 0),
                        'quantity': variant.get('stock_quantity', prod.get('stock_quantity', 0)) or 0,
                        'status': 'active' if prod.get('status') == 'publish' else 'inactive',
                        'image_url': images[0].get('src', '') if images else '',
                        'channel_url': prod.get('permalink', ''),
                        'woo_product_id': str(prod.get('id', '')),
                        'woo_variation_id': str(variant.get('id', '')),
                    })

                # Simple product (no variations)
                if not prod.get('variations'):
                    all_products.append({
                        'channel': 'woocommerce',
                        'sku': prod.get('sku', ''),
                        'title': prod.get('name', ''),
                        'description': prod.get('description', ''),
                        'price': float(price or 0),
                        'quantity': prod.get('stock_quantity', 0) or 0,
                        'status': 'active' if prod.get('status') == 'publish' else 'inactive',
                        'image_url': images[0].get('src', '') if images else '',
                        'channel_url': prod.get('permalink', ''),
                        'woo_product_id': str(prod.get('id', '')),
                    })

            if len(products) < per_page:
                break
            page += 1

        logger.info(f'[WooCommerce] Fetched {len(all_products)} products')
        return all_products

    def update_listing(self, sku: str, changes: dict) -> dict:
        """Update product (price, stock) by SKU."""
        logger.info(f'[WooCommerce] Updating product {sku}: {changes}')

        try:
            # Find product by SKU
            url = f'{self.api_url}/products'
            params = {'sku': sku, 'per_page': 100}
            url_with_params = url + '?' + urllib.parse.urlencode(params)

            auth_header = self._oauth_sign('GET', url_with_params)
            req = urllib.request.Request(url_with_params, headers={'Authorization': auth_header}, method='GET')

            with urllib.request.urlopen(req, timeout=20) as resp:
                products = json.loads(resp.read())

            if not products:
                return {'success': False, 'error': 'SKU not found'}

            prod = products[0]
            prod_id = prod['id']

            update_body = {}
            if 'price' in changes:
                update_body['regular_price'] = str(changes['price'])
            if 'quantity' in changes:
                update_body['stock_quantity'] = changes['quantity']

            if update_body:
                self._request('PUT', f'/products/{prod_id}', body=update_body)

            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def create_listing(self, listing: dict) -> dict:
        """Create a new product in WooCommerce."""
        logger.info(f'[WooCommerce] Creating product: {listing.get("title")}')
        try:
            body = {
                'name': listing.get('title'),
                'type': 'simple',
                'regular_price': str(listing.get('price', 0)),
                'description': listing.get('description', ''),
                'sku': listing.get('sku', ''),
                'stock_quantity': listing.get('quantity', 0),
                'manage_stock': True,
            }
            response = self._request('POST', '/products', body=body)
            return {'success': True, 'product_id': response.get('id')}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def fetch_messages(self, since: datetime) -> List[dict]:
        """WooCommerce doesn't have a messaging API."""
        return []
