"""
core/plugins/marketplaces/google_shopping.py

Google Shopping / Merchant Center API integration for VendStack.
Auth: OAuth 2.0 (Google Cloud) + Merchant Center ID
Docs: https://developers.google.com/shopping-content
"""
import json, logging, urllib.request, urllib.parse, datetime, time
from typing import List, Dict, Any
from core.plugins import Plugin, PluginType, register, HealthStatus

logger = logging.getLogger(__name__)

@register(PluginType.MARKETPLACE, 'google_shopping', 'Google Shopping', '🔍', '1.0.0',
          'List products on Google Shopping, sync prices and inventory from your Merchant Center')
class GoogleShoppingPlugin(Plugin):
    """Google Merchant Center + Shopping Content API."""

    CONTENT_API = 'https://shoppingcontent.googleapis.com/content/v2.1'
    AUTH_URL = 'https://oauth2.googleapis.com/token'

    def __init__(self, config: dict):
        super().__init__(config)
        self.client_id = config.get('client_id')
        self.client_secret = config.get('client_secret')
        self.refresh_token = config.get('refresh_token')
        self.merchant_id = config.get('merchant_id')
        self.access_token = ''
        self.token_expiry = 0

    def config_schema(self) -> dict:
        return {
            'type': 'object',
            'properties': {
                'client_id': {'type': 'string', 'label': 'Google OAuth Client ID', 'required': True},
                'client_secret': {'type': 'string', 'label': 'Client Secret', 'required': True, 'secret': True},
                'refresh_token': {'type': 'string', 'label': 'Refresh Token', 'required': True, 'secret': True},
                'merchant_id': {'type': 'string', 'label': 'Merchant Center ID', 'required': True},
            },
            'required': ['client_id', 'client_secret', 'refresh_token', 'merchant_id'],
        }

    def _refresh(self) -> str:
        if self.access_token and time.time() < self.token_expiry - 60:
            return self.access_token
        params = urllib.parse.urlencode({
            'grant_type': 'refresh_token', 'refresh_token': self.refresh_token,
            'client_id': self.client_id, 'client_secret': self.client_secret,
        })
        req = urllib.request.Request(self.AUTH_URL, data=params.encode(),
            headers={'Content-Type': 'application/x-www-form-urlencoded'}, method='POST')
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            self.access_token = data['access_token']
            self.token_expiry = time.time() + data.get('expires_in', 3600)
            return self.access_token

    def _api(self, method, path, body=None, params=None):
        url = f'{self.CONTENT_API}{path}'
        if params: url += '?' + urllib.parse.urlencode(params)
        data = json.dumps(body).encode() if body else None
        headers = {'Authorization': f'Bearer {self._refresh()}', 'Content-Type': 'application/json'}
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        with urllib.request.urlopen(req, timeout=25) as resp:
            return json.loads(resp.read())

    def health_check(self) -> HealthStatus:
        try:
            self._refresh()
            self._api('GET', f'/accounts/{self.merchant_id}')
            return HealthStatus(status='ok', last_check=datetime.utcnow().isoformat())
        except Exception as e:
            return HealthStatus(status='error', message=str(e), last_check=datetime.utcnow().isoformat())

    def fetch_orders(self, since: datetime) -> List[dict]:
        """Google Shopping doesn't have orders — this is a listing-only channel."""
        return []

    def fetch_listings(self) -> List[dict]:
        """Fetch products from Google Merchant Center."""
        logger.info('[GoogleShopping] Fetching products from Merchant Center')
        all_items = []
        page = 1
        while True:
            try:
                data = self._api('GET', f'/products', params={
                    'merchantId': self.merchant_id, 'pageSize': 250, 'pageToken': str(page)
                })
                items = data.get('resources', [])
                for item in items:
                    all_items.append({
                        'channel': 'google_shopping',
                        'sku': item.get('offerId', ''),
                        'title': item.get('title', ''),
                        'description': item.get('description', ''),
                        'price': float(item.get('price', {}).get('value', 0)),
                        'quantity': 0,
                        'status': 'active' if item.get('channel') == 'online' else 'inactive',
                        'image_url': item.get('imageLink', ''),
                        'channel_url': item.get('link', ''),
                        'google_product_id': item.get('id', ''),
                    })
                if not data.get('nextPageToken'):
                    break
                page += 1
            except Exception as e:
                logger.error(f'[GoogleShopping] Product fetch failed: {e}')
                break
        return all_items

    def create_listing(self, listing: dict) -> dict:
        """Submit a product to Google Merchant Center."""
        logger.info(f'[GoogleShopping] Creating listing: {listing.get("title")}')
        product = {
            'offerId': listing.get('sku', ''),
            'title': listing.get('title', ''),
            'description': listing.get('description', ''),
            'price': {'amount': str(listing.get('price', 0)), 'currency': 'GBP'},
            'availability': 'in stock' if listing.get('quantity', 0) > 0 else 'out of stock',
            'link': listing.get('channel_url', ''),
            'imageLink': listing.get('image_url', ''),
            'channel': 'online',
        }
        try:
            result = self._api('INSERT', f'/products/{self.merchant_id}', body={'product': product})
            return {'success': True, 'google_product_id': result.get('product', {}).get('id', '')}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def update_listing(self, sku: str, changes: dict) -> dict:
        return self.create_listing({**changes, 'sku': sku})
