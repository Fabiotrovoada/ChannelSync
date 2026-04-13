"""
core/plugins/marketplaces/facebook_marketplace.py

Facebook Marketplace integration for VendStack.
Auth: Facebook Graph API with Page Access Token
Docs: https://developers.facebook.com/docs/marketplace
"""
import json, logging, urllib.request, urllib.parse, datetime, time
from typing import List, Dict, Any
from core.plugins import Plugin, PluginType, register, HealthStatus

logger = logging.getLogger(__name__)

@register(PluginType.MARKETPLACE, 'facebook_marketplace', 'Facebook Marketplace', '📘', '1.0.0',
          'List products on Facebook Marketplace for local and national sales')
class FacebookMarketplacePlugin(Plugin):
    """Facebook Marketplace integration via Graph API."""

    GRAPH_API = 'https://graph.facebook.com/v18.0'

    def __init__(self, config: dict):
        super().__init__(config)
        self.page_access_token = config.get('page_access_token')
        self.page_id = config.get('page_id')

    def config_schema(self) -> dict:
        return {
            'type': 'object',
            'properties': {
                'page_access_token': {'type': 'string', 'label': 'Page Access Token', 'required': True, 'secret': True},
                'page_id': {'type': 'string', 'label': 'Facebook Page ID', 'required': True},
            },
            'required': ['page_access_token', 'page_id'],
        }

    def _api(self, path, method='GET', body=None):
        url = f'{self.GRAPH_API}{path}'
        params = {'access_token': self.page_access_token}
        if method == 'GET':
            url += '?' + urllib.parse.urlencode(params)
        data = json.dumps(body).encode() if body else None
        if body:
            req = urllib.request.Request(url, data=data,
                headers={'Content-Type': 'application/json'}, method=method)
        else:
            req = urllib.request.Request(url, headers={'Content-Type': 'application/json'}, method=method)
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read())

    def health_check(self) -> HealthStatus:
        try:
            self._api(f'/{self.page_id}', 'GET')
            return HealthStatus(status='ok', last_check=datetime.utcnow().isoformat())
        except Exception as e:
            return HealthStatus(status='error', message=str(e))

    def fetch_orders(self, since: datetime) -> List[dict]:
        """Facebook Marketplace orders via Conversations API."""
        logger.info('[Facebook] Fetching orders')
        try:
            data = self._api(f'/{self.page_id}/conversations')
            conversations = data.get('data', [])
            orders = []
            for conv in conversations:
                # Get messages in conversation
                msgs = self._api(f'/{conv["id"]}/messages')
                for msg in msgs.get('data', []):
                    if msg.get('message'):
                        orders.append({
                            'channel': 'facebook',
                            'channel_order_id': conv['id'],
                            'order_number': conv['id'],
                            'order_date': msg.get('created_time', ''),
                            'status': 'pending',
                            'customer': {'name': msg.get('from', {}).get('name', 'Facebook User'), 'email': ''},
                            'items': [{'title': msg['message'], 'qty': 1, 'price': 0}],
                            'total': 0, 'currency': 'GBP', 'tracking_number': '', 'carrier': '',
                        })
            return orders
        except Exception as e:
            logger.error(f'[Facebook] Order fetch failed: {e}')
            return []

    def fetch_listings(self) -> List[dict]:
        """Facebook Marketplace listings (products in catalog)."""
        logger.info('[Facebook] Fetching listings')
        return []

    def create_listing(self, listing: dict) -> dict:
        """Create a Facebook Marketplace listing via Catalog API."""
        logger.info(f'[Facebook] Creating listing: {listing.get("title")}')
        try:
            catalog_id = self.config.get('catalog_id', self.page_id)
            body = {
                'access_token': self.page_access_token,
                'title': listing.get('title', ''),
                'description': listing.get('description', ''),
                'price': str(listing.get('price', 0)),
                'currency': 'GBP',
                'availability': 'in stock' if listing.get('quantity', 0) > 0 else 'out of stock',
                'condition': 'new',
                'url': listing.get('channel_url', ''),
            }
            data = self._api(f'/{catalog_id}/products', 'POST', body)
            return {'success': True, 'facebook_product_id': data.get('id', '')}
        except Exception as e:
            return {'success': False, 'error': str(e)}
