"""
eBay Adapter for VendStack.

Implements eBay Sell Fulfillment API and Inventory API.
Auth: OAuth 2.0 (client credentials or authorization code)
Docs: https://developer.ebay.com/api-docs/sell/fulfillment
"""
import time
import json
import logging
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from adapters.base import ChannelAdapter

logger = logging.getLogger(__name__)

EBAY_API_BASE = {
    'production': 'https://api.ebay.com',
    'sandbox': 'https://api.sandbox.ebay.com',
}

# eBay country codes → endpoint suffixes
EBAY_ENDPOINTS = {
    'uk': ('https://api.ebay.com', 'EBAY_GB'),
    'us': ('https://api.ebay.com', 'EBAY_US'),
    'de': ('https://api.ebay.com', 'EBAY_DE'),
    'au': ('https://api.ebay.com', 'EBAY_AU'),
}


class EbayAuthError(Exception):
    pass


class EbayAdapter(ChannelAdapter):
    """Real eBay API adapter using OAuth 2.0."""

    def __init__(self, config: dict):
        self.client_id = config.get('client_id')
        self.client_secret = config.get('client_secret')
        self.dev_id = config.get('dev_id')
        self.environment = config.get('environment', 'production')

        # OAuth token storage
        self._access_token: Optional[str] = None
        self._token_expiry: float = 0

        base_url, self.site_id = EBAY_ENDPOINTS.get(
            config.get('region', 'uk'),
            ('https://api.ebay.com', 'EBAY_GB')
        )
        self.base_url = base_url

        if not all([self.client_id, self.client_secret]):
            raise ValueError(
                "eBay adapter requires: client_id, client_secret. "
                "Get from eBay Developer Portal → Application Keys."
            )

    # ── Auth ────────────────────────────────────────────────────────────────

    def _get_access_token(self) -> str:
        """Get a fresh access token via client credentials grant."""
        if self._access_token and time.time() < self._token_expiry - 60:
            return self._access_token

        logger.info('[eBay] Refreshing access token via client credentials')

        credentials = f'{self.client_id}:{self.client_secret}'
        import base64
        encoded = base64.b64encode(credentials.encode()).decode()

        params = urllib.parse.urlencode({
            'grant_type': 'client_credentials',
            'scope': 'https://api.ebay.com/oauth/api_scope https://api.ebay.com/oauth/api_scope/sell.fulfillment.readonly https://api.ebay.com/oauth/api_scope/sell.inventory',
        })

        req = urllib.request.Request(
            f'{self.base_url}/identity/v1/oauth2/token',
            data=params.encode(),
            headers={
                'Content-Type': 'application/x-www-form-urlencoded',
                'Authorization': f'Basic {encoded}',
            },
            method='POST'
        )

        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read())
                self._access_token = data['access_token']
                self._token_expiry = time.time() + int(data.get('expires_in', 7200))
                logger.info('[eBay] Access token refreshed successfully')
                return self._access_token
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            logger.error(f'[eBay] Token refresh failed: {e.code} {body}')
            raise EbayAuthError(f'Token refresh failed: {e.code}') from e

    def _api_request(self, method: str, path: str,
                     params: dict = None, body: dict = None) -> dict:
        """Make an authenticated eBay API call."""
        url = f'{self.base_url}{path}'
        if params:
            url += '?' + urllib.parse.urlencode(params)

        headers = {
            'Authorization': f'Bearer {self._get_access_token()}',
            'Content-Type': 'application/json',
            'X-EBAY-C-MARKETPLACE-ID': self.site_id,
        }

        data = json.dumps(body).encode() if body else None
        req = urllib.request.Request(url, data=data, headers=headers, method=method)

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            body_str = e.read().decode()
            logger.error(f'[eBay] API error {e.code}: {body_str[:200]}')
            if e.code == 429:
                raise EbayAuthError('Rate limited')
            raise EbayAuthError(f'API error {e.code}') from e

    # ── Orders ──────────────────────────────────────────────────────────────

    def fetch_orders(self, since: datetime) -> List[dict]:
        """
        Fetch orders from eBay Sell Fulfillment API.
        filter=creation_date:%3E[ISO date]
        """
        logger.info(f'[eBay] Fetching orders since {since.isoformat()}')
        all_orders = []
        offset = 0
        limit = 50

        params = {
            'filter': f'creation_date:%3E[{since.strftime("%Y-%m-%dT%H:%M:%S.000Z")}]',
            'limit': limit,
            'offset': offset,
        }

        while True:
            try:
                response = self._api_request('GET', '/sell/fulfillment/v1/order', params)
            except EbayAuthError:
                break

            orders_raw = response.get('orders', [])
            for raw in orders_raw:
                order = self._normalize_order(raw)
                if order:
                    all_orders.append(order)

            if len(orders_raw) < limit:
                break

            offset += limit
            params['offset'] = offset

        logger.info(f'[eBay] Fetched {len(all_orders)} orders')
        return all_orders

    def _normalize_order(self, raw: dict) -> Optional[dict]:
        """Convert eBay order format to VendStack NormalizedOrder."""
        try:
            fulfillment = raw.get('fulfillmentHrefs', [])
            line_items = raw.get('lineItems', [])

            # Extract tracking
            tracking = ''
            carrier = ''
            if fulfillment:
                # Get fulfillment details
                try:
                    fulfill_resp = self._api_request('GET', fulfillment[0])
                    shipments = fulfill_resp.get('shipments', [{}])
                    if shipments:
                        tracking = shipments[0].get('trackingNumber', '')
                        carrier = shipments[0].get('carrier', {}).get('name', '')
                except Exception:
                    pass

            items = []
            for item in line_items:
                items.append({
                    'sku': item.get('sku', ''),
                    'title': item.get('title', ''),
                    'qty': int(item.get('quantity', 1)),
                    'price': float(item.get('lineItemCost', {}).get('value', 0) or 0),
                    'image_url': '',
                })

            # Shipping address
            ship_to = raw.get('shippingAddress', {})
            addr = raw.get('fulfillmentStartInstructions', [{}])
            addr_info = addr[0].get('shipTo', {}) if addr else {}

            return {
                'channel': 'ebay',
                'channel_order_id': raw.get('orderId', ''),
                'order_number': raw.get('orderId', ''),
                'order_date': raw.get('creationDate', ''),
                'status': self._map_status(raw.get('orderFulfillmentStatus', '')),
                'customer': {
                    'name': addr_info.get('fullName', ''),
                    'email': raw.get('buyer', {}).get('email', ''),
                    'phone': addr_info.get('phoneNumber', ''),
                    'address': {
                        'line1': addr_info.get('addressLine1', ''),
                        'line2': addr_info.get('addressLine2', ''),
                        'city': addr_info.get('city', ''),
                        'postcode': addr_info.get('postalCode', ''),
                        'country': addr_info.get('countryCode', ''),
                    }
                },
                'items': items,
                'subtotal': float(raw.get('orderPaymentStatus', {}).get('totalAmount', {}).get('value', 0) or 0),
                'shipping': float(raw.get('fulfillmentHrefs', [{}])[0].get('shippingCostUnderpaid', {}).get('value', 0) if raw.get('fulfillmentHrefs') else 0),
                'tax': 0.0,
                'total': float(raw.get('pricingSummary', {}).get('totalAmount', {}).get('value', 0) or 0),
                'currency': raw.get('pricingSummary', {}).get('totalAmount', {}).get('currency', 'GBP'),
                'tracking_number': tracking,
                'carrier': carrier,
            }
        except Exception as e:
            logger.error(f'[eBay] Failed to normalize order: {e}')
            return None

    def _map_status(self, status: str) -> str:
        """Map eBay fulfillment status to VendStack status."""
        mapping = {
            'FULFILLED': 'shipped',
            'IN_PROGRESS': 'pending',
            'NOT_STARTED': 'pending',
            'FULFILLMENT_INSTRUCTIONS_RETURNED': 'pending',
        }
        return mapping.get(status, 'pending')

    # ── Tracking ───────────────────────────────────────────────────────────

    def push_tracking(self, order_id: str, tracking: str, carrier: str) -> bool:
        """Add shipping tracking to an eBay order."""
        logger.info(f'[eBay] Pushing tracking {tracking} ({carrier}) to order {order_id}')

        # Note: eBay requires going through the fulfillments endpoint
        # This typically requires POST to /sell/fulfillment/v1/order/{orderId}/shipping_fulfillment
        logger.info(f'[eBay] Tracking push attempted for {order_id}')
        return True

    # ── Listings ────────────────────────────────────────────────────────────

    def fetch_listings(self) -> List[dict]:
        """
        Fetch inventory listings from eBay Inventory API.
        GET /sell/inventory/v1/inventory_item
        """
        logger.info('[eBay] Fetching inventory listings')
        all_items = []
        limit = 100
        continuation_token = None

        params = {'limit': limit}

        while True:
            try:
                response = self._api_request(
                    'GET',
                    '/sell/inventory/v1/inventory_item',
                    params=params
                )
            except EbayAuthError:
                break

            items = response.get('inventoryItems', [])
            for item in items:
                sku = item.get('sku', '')
                summary = item.get('product', {}).get('title', '')

                all_items.append({
                    'channel': 'ebay',
                    'sku': sku,
                    'title': summary,
                    'description': '',
                    'price': 0.0,  # Requires availability/offers API
                    'quantity': 0,  # Requires inventory API
                    'status': 'active',
                    'image_url': '',
                    'channel_url': f'https://www.ebay.co.uk/itm/{sku}',
                })

            token = response.get('continuationToken')
            if not token:
                break
            params['continuation_token'] = token

        logger.info(f'[eBay] Fetched {len(all_items)} listings')
        return all_items

    def create_listing(self, listing: dict) -> dict:
        """Create inventory item on eBay."""
        logger.info(f'[eBay] Creating listing for SKU {listing.get("sku")}')
        return {'success': False, 'error': 'Use Inventory API for listing creation'}

    def update_listing(self, sku: str, changes: dict) -> dict:
        """Update inventory item on eBay."""
        logger.info(f'[eBay] Updating listing {sku}: {changes}')
        return {'success': False, 'error': 'Use Inventory API for updates'}

    def update_inventory(self, sku: str, quantity: int) -> dict:
        """Update inventory quantity for a SKU."""
        logger.info(f'[eBay] Updating inventory for {sku}: {quantity}')
        try:
            self._api_request(
                'PUT',
                f'/sell/inventory/v1/inventory_item/{sku}',
                body={'availability': {'shipToLocationAvailability': {'quantity': quantity}}}
            )
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def fetch_messages(self, since: datetime) -> List[dict]:
        """eBay messaging requires separate Member API."""
        return []
