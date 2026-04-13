"""
core/plugins/marketplaces/prestashop.py

PrestaShop 1.7+ REST API adapter.
Auth: API Key (from PrestaShop Back Office → Webservice)
Docs: https://devdocs.prestashop.com/1.7/webservice/
"""
import json, logging, urllib.request, urllib.parse, datetime
from typing import List, Dict, Any
from core.plugins import Plugin, PluginType, register, HealthStatus

logger = logging.getLogger(__name__)

@register(PluginType.MARKETPLACE, 'prestashop', 'PrestaShop', '🛒', '1.0.0',
          'Sync orders and products from PrestaShop stores')
class PrestaShopPlugin(Plugin):
    """PrestaShop REST API integration."""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.base_url = config.get('base_url', '').rstrip('/')
        self.api_key = config.get('api_key', '')
    
    def config_schema(self) -> dict:
        return {
            'type': 'object',
            'properties': {
                'base_url': {'type': 'string', 'label': 'PrestaShop URL', 'required': True, 'placeholder': 'https://yourstore.com'},
                'api_key': {'type': 'string', 'label': 'Webservice API Key', 'required': True, 'secret': True},
            },
            'required': ['base_url', 'api_key'],
        }
    
    def _api(self, resource: str, params: dict = None) -> dict:
        url = f'{self.base_url}/api/{resource}?output_format=JSON'
        if params:
            url += '&' + urllib.parse.urlencode(params)
        import base64
        credentials = base64.b64encode(f'{self.api_key}:'.encode()).decode()
        req = urllib.request.Request(url, headers={'Authorization': f'Basic {credentials}'})
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read())
    
    def health_check(self) -> HealthStatus:
        try:
            self._api('orders', {'limit': 1})
            return HealthStatus(status='ok', last_check=datetime.utcnow().isoformat())
        except Exception as e:
            return HealthStatus(status='error', message=str(e))
    
    def fetch_orders(self, since: datetime) -> List[dict]:
        logger.info(f'[PrestaShop] Fetching orders since {since}')
        try:
            filter_date = f'[created_at]>[{since.strftime("%Y-%m-%d %H:%M:%S")}]'
            data = self._api('orders', {'filter': filter_date, 'display': 'full'})
            orders = data.get('orders', [])
            return [self._normalize(o) for o in orders]
        except Exception as e:
            logger.error(f'[PrestaShop] Order fetch failed: {e}')
            return []
    
    def _normalize(self, raw: dict) -> dict:
        addr = raw.get('address', {})
        return {
            'channel': 'prestashop',
            'channel_order_id': str(raw.get('id', '')),
            'order_number': raw.get('reference', ''),
            'order_date': raw.get('date_add', ''),
            'status': 'shipped' if raw.get('current_state') == '4' else 'pending',
            'customer': {'name': addr.get('firstname', '') + ' ' + addr.get('lastname', ''),
                         'email': raw.get('email', '')},
            'items': [{'sku': p.get('product_reference', ''), 'title': p.get('product_name', ''),
                       'qty': int(p.get('product_quantity', 1)), 'price': float(p.get('unit_price_tax_incl', 0))}
                      for p in raw.get('associations', {}).get('order_rows', [])],
            'total': float(raw.get('total_paid', 0)),
            'currency': raw.get('currency', 'GBP'),
            'tracking_number': '',
            'carrier': '',
        }
    
    def fetch_listings(self) -> List[dict]:
        logger.info('[PrestaShop] Fetching products')
        return []
