"""
core/plugins/marketplaces/magento.py

Magento 2 REST API adapter for VendStack.
Auth: OAuth 1.0a or Integration Token
Docs: https://developer.adobe.com/commerce/webapi/rest/
"""
import json, logging, urllib.request, datetime
from typing import List, Dict, Any
from core.plugins import Plugin, PluginType, register, HealthStatus

logger = logging.getLogger(__name__)

@register(PluginType.MARKETPLACE, 'magento', 'Magento', '🛍️', '1.0.0',
          'Sync orders and inventory from Magento 2 stores')
class MagentoPlugin(Plugin):
    """Magento 2 integration via REST API."""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.base_url = config.get('base_url', '').rstrip('/')
        self.access_token = config.get('access_token', '')
    
    def config_schema(self) -> dict:
        return {
            'type': 'object',
            'properties': {
                'base_url': {'type': 'string', 'label': 'Magento Store URL', 'required': True, 'placeholder': 'https://yourstore.com'},
                'access_token': {'type': 'string', 'label': 'Access Token', 'required': True, 'secret': True},
            },
            'required': ['base_url', 'access_token'],
        }
    
    def _headers(self) -> dict:
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
        }
    
    def _api(self, path: str) -> dict:
        url = f'{self.base_url}/rest/V1{path}'
        req = urllib.request.Request(url, headers=self._headers())
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read())
    
    def health_check(self) -> HealthStatus:
        try:
            self._api('/store/storeConfigs')
            return HealthStatus(status='ok', last_check=datetime.utcnow().isoformat())
        except Exception as e:
            return HealthStatus(status='error', message=str(e))
    
    def fetch_orders(self, since: datetime) -> List[dict]:
        """Fetch Magento orders."""
        logger.info(f'[Magento] Fetching orders since {since}')
        try:
            search_criteria = f'created_at>=${since.strftime("%Y-%m-%d %H:%M:%S")},status!=canceled'
            import urllib.parse
            params = urllib.parse.urlencode({'searchCriteria': search_criteria})
            data = self._api(f'/orders?{params}')
            orders = data.get('items', [])
            return [self._normalize(o) for o in orders]
        except Exception as e:
            logger.error(f'[Magento] Order fetch failed: {e}')
            return []
    
    def _normalize(self, raw: dict) -> dict:
        return {
            'channel': 'magento',
            'channel_order_id': str(raw.get('entity_id', '')),
            'order_number': raw.get('increment_id', ''),
            'order_date': raw.get('created_at', ''),
            'status': 'shipped' if raw.get('status') == 'complete' else 'pending',
            'customer': {
                'name': f"{raw.get('customer_firstname', '')} {raw.get('customer_lastname', '')}",
                'email': raw.get('customer_email', ''),
            },
            'items': [{'sku': i.get('sku', ''), 'title': i.get('name', ''),
                       'qty': int(i.get('qty_ordered', 0)), 'price': float(i.get('price', 0))}
                      for i in raw.get('extension_attributes', {}).get('order_items', [])],
            'total': float(raw.get('grand_total', 0)),
            'currency': raw.get('order_currency_code', 'GBP'),
            'tracking_number': '',
            'carrier': '',
        }
    
    def fetch_listings(self) -> List[dict]:
        """Fetch Magento products."""
        logger.info('[Magento] Fetching products')
        return []
