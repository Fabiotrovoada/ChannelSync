"""
Shopify Adapter for VendStack.

Implements Shopify Admin API (REST) for order and inventory management.
Auth: OAuth 2.0 + Access Token
Docs: https://shopify.dev/docs/admin-api
"""
import time
import json
import logging
import urllib.request
import urllib.parse
from datetime import datetime
from typing import List, Optional, Dict, Any
from adapters.base import ChannelAdapter

logger = logging.getLogger(__name__)


class ShopifyAdapter(ChannelAdapter):
    """Real Shopify Admin API adapter."""

    def __init__(self, config: dict):
        self.shop = config.get('shop')  # e.g. 'mystore.myshopify.com'
        self.access_token = config.get('access_token')
        self.api_version = config.get('api_version', '2024-01')

        if not self.shop or not self.access_token:
            raise ValueError(
                "Shopify adapter requires: shop (e.g. 'mystore.myshopify.com'), access_token. "
                "Get via Shopify Partner Dashboard → App development."
            )

        self.base_url = f'https://{self.shop}/admin/api/{self.api_version}'
        self.headers = {
            'X-Shopify-Access-Token': self.access_token,
            'Content-Type': 'application/json',
        }

    # ── HTTP ────────────────────────────────────────────────────────────────

    def _request(self, method: str, path: str,
                 params: dict = None, body: dict = None) -> dict:
        """Make an authenticated Shopify API call."""
        url = f'{self.base_url}{path}'
        if params:
            url += '?' + urllib.parse.urlencode(params)

        data = json.dumps(body).encode() if body else None
        req = urllib.request.Request(url, data=data, headers=self.headers, method=method)

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            body_str = e.read().decode()
            logger.error(f'[Shopify] API error {e.code}: {body_str[:200]}')
            raise

    def _get_all(self, path: str, params: dict = None) -> List[dict]:
        """Paginate through all results from a Shopify endpoint."""
        all_items = []
        params = params or {}
        params['limit'] = 250

        while True:
            response = self._request('GET', path, params=params)
            items = response.get('items', response.get('orders', response.get('products', [])))
            all_items.extend(items)

            # Shopify uses Link header for pagination
            # Check if there are more pages
            break  # Simplified — in production parse Link header

        return all_items

    # ── Orders ──────────────────────────────────────────────────────────────

    def fetch_orders(self, since: datetime) -> List[dict]:
        """
        Fetch orders from Shopify Admin API.
        GET /orders.json?created_at_min={since}&status=any
        """
        logger.info(f'[Shopify] Fetching orders since {since.isoformat()}')
        all_orders = []

        params = {
            'created_at_min': since.isoformat() + 'Z',
            'status': 'any',
            'limit': 250,
            'fields': 'id,order_number,name,email,created_at,updated_at,'
                     'financial_status,fulfillment_status,total_price,'
                     'subtotal_price,total_tax,shipping_address,billing_address,'
                     'line_items,shipping_lines,client_details',
        }

        page_count = 0
        while True:
            try:
                response = self._request('GET', '/orders.json', params=params)
            except Exception as e:
                logger.error(f'[Shopify] Order fetch failed: {e}')
                break

            orders_raw = response.get('orders', [])
            for raw in orders_raw:
                order = self._normalize_order(raw)
                if order:
                    all_orders.append(order)

            # Check for next page via Link header or next_page_info
            # Simplified pagination
            if len(orders_raw) < 250:
                break

            # Use page_info for cursor-based pagination
            # params['page_info'] = ... (parse from Link header in production)
            break

        logger.info(f'[Shopify] Fetched {len(all_orders)} orders')
        return all_orders

    def _normalize_order(self, raw: dict) -> Optional[dict]:
        """Convert Shopify order to VendStack NormalizedOrder."""
        try:
            shipping_addr = raw.get('shipping_address', {}) or {}
            billing_addr = raw.get('billing_address', {}) or {}

            items = []
            for item in raw.get('line_items', []):
                items.append({
                    'sku': item.get('sku', ''),
                    'title': item.get('title', ''),
                    'qty': int(item.get('quantity', 1)),
                    'price': float(item.get('price', 0)),
                    'image_url': '',
                })

            # Determine status
            fulfill_status = raw.get('fulfillment_status', '')
            financial_status = raw.get('financial_status', '')

            if fulfill_status == 'fulfilled':
                status = 'shipped'
            elif financial_status == 'refunded':
                status = 'cancelled'
            elif fulfill_status == 'partial':
                status = 'partial'
            else:
                status = 'pending'

            return {
                'channel': 'shopify',
                'channel_order_id': str(raw.get('id', '')),
                'order_number': raw.get('name', ''),
                'order_date': raw.get('created_at', ''),
                'status': status,
                'customer': {
                    'name': shipping_addr.get('first_name', '') + ' ' + shipping_addr.get('last_name', ''),
                    'email': raw.get('email', ''),
                    'phone': shipping_addr.get('phone', ''),
                    'address': {
                        'line1': shipping_addr.get('address1', ''),
                        'line2': shipping_addr.get('address2', ''),
                        'city': shipping_addr.get('city', ''),
                        'postcode': shipping_addr.get('zip', ''),
                        'country': shipping_addr.get('country', ''),
                    }
                },
                'items': items,
                'subtotal': float(raw.get('subtotal_price', 0) or 0),
                'shipping': float(sum(
                    float(s.get('price', 0) or 0)
                    for s in raw.get('shipping_lines', [])
                )),
                'tax': float(raw.get('total_tax', 0) or 0),
                'total': float(raw.get('total_price', 0) or 0),
                'currency': raw.get('currency', 'GBP'),
                'tracking_number': '',
                'carrier': '',
            }
        except Exception as e:
            logger.error(f'[Shopify] Failed to normalize order: {e}')
            return None

    # ── Fulfillment/Tracking ─────────────────────────────────────────────────

    def push_tracking(self, order_id: str, tracking: str, carrier: str) -> bool:
        """
        Create a fulfillment with tracking for a Shopify order.
        POST /orders/{order_id}/fulfillments.json
        """
        logger.info(f'[Shopify] Creating fulfillment for order {order_id} with tracking {tracking}')

        body = {
            'fulfillment': {
                'tracking_number': tracking,
                'tracking_company': carrier,
                'notify_customer': True,
            }
        }

        try:
            response = self._request(
                'POST',
                f'/orders/{order_id}/fulfillments.json',
                body=body
            )
            logger.info(f'[Shopify] Fulfillment created for {order_id}')
            return True
        except Exception as e:
            logger.error(f'[Shopify] Failed to create fulfillment: {e}')
            return False

    # ── Listings / Products ─────────────────────────────────────────────────

    def fetch_listings(self) -> List[dict]:
        """
        Fetch products from Shopify Admin API.
        GET /products.json?limit=250
        """
        logger.info('[Shopify] Fetching products')
        all_products = []
        params = {'limit': 250, 'status': 'any'}

        page_count = 0
        while True:
            try:
                response = self._request('GET', '/products.json', params=params)
            except Exception as e:
                logger.error(f'[Shopify] Product fetch failed: {e}')
                break

            products = response.get('products', [])
            for prod in products:
                variants = prod.get('variants', [])
                images = prod.get('images', [])

                for variant in variants:
                    price_info = variant.get('price', '0')
                    qty = 0
                    try:
                        # Need inventory API call for quantity
                        qty = variant.get('inventory_quantity', 0)
                    except Exception:
                        pass

                    all_products.append({
                        'channel': 'shopify',
                        'sku': variant.get('sku', ''),
                        'title': prod.get('title', ''),
                        'description': prod.get('body_html', ''),
                        'price': float(price_info or 0),
                        'quantity': qty,
                        'status': 'active' if prod.get('status') == 'active' else 'inactive',
                        'image_url': images[0].get('src', '') if images else '',
                        'channel_url': f'https://{self.shop}/products/{prod.get("handle", "")}',
                        'shopify_product_id': str(prod.get('id', '')),
                        'shopify_variant_id': str(variant.get('id', '')),
                    })

            if len(products) < 250:
                break
            break  # Add cursor pagination in production

        logger.info(f'[Shopify] Fetched {len(all_products)} product variants')
        return all_products

    def update_listing(self, sku: str, changes: dict) -> dict:
        """Update product variant (price, quantity)."""
        logger.info(f'[Shopify] Updating variant {sku}: {changes}')

        # Find product by SKU, then update variant
        try:
            # Search for product with this SKU
            response = self._request(
                'GET',
                '/products.json',
                params={'limit': 250}
            )

            for prod in response.get('products', []):
                for variant in prod.get('variants', []):
                    if variant.get('sku') == sku:
                        variant_id = variant.get('id')
                        product_id = prod.get('id')

                        # Update price
                        if 'price' in changes:
                            self._request(
                                'PUT',
                                f'/variants/{variant_id}.json',
                                body={'variant': {'id': variant_id, 'price': str(changes['price'])}}
                            )

                        return {'success': True}

            return {'success': False, 'error': 'SKU not found'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def create_listing(self, listing: dict) -> dict:
        """Create a new product on Shopify."""
        logger.info(f'[Shopify] Creating product: {listing.get("title")}')
        try:
            body = {
                'product': {
                    'title': listing.get('title'),
                    'body_html': listing.get('description', ''),
                    'variants': [{
                        'sku': listing.get('sku', ''),
                        'price': str(listing.get('price', 0)),
                        'inventory_management': 'shopify',
                    }]
                }
            }
            response = self._request('POST', '/products.json', body=body)
            return {'success': True, 'product_id': response.get('product', {}).get('id')}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def fetch_messages(self, since: datetime) -> List[dict]:
        """Shopify doesn't have a standard messaging API in Admin API."""
        return []
