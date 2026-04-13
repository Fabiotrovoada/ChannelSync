"""
core/plugins/marketplaces/morrisons.py

Morrisons Marketplace (via MCP) integration for VendStack.
Auth: API Key provided by Morrisons marketplace team
Docs: https://www.morrisonsmp.com/ (seller portal)
"""
import json, logging, urllib.request, datetime
from typing import List, Dict, Any
from core.plugins import Plugin, PluginType, register, HealthStatus

logger = logging.getLogger(__name__)

@register(PluginType.MARKETPLACE, 'morrisons', 'Morrisons', '🛒', '1.0.0',
          'UK grocery marketplace — list products on Morrisons online marketplace')
class MorrisonsPlugin(Plugin):
    """Morrisons Marketplace integration."""

    BASE_URL = 'https://api.morrisonsmp.com/v1'

    def __init__(self, config: dict):
        super().__init__(config)
        self.api_key = config.get('api_key')
        self.supplier_id = config.get('supplier_id')

    def config_schema(self) -> dict:
        return {
            'type': 'object',
            'properties': {
                'api_key': {'type': 'string', 'label': 'API Key (from Morrisons Seller Portal)', 'required': True, 'secret': True},
                'supplier_id': {'type': 'string', 'label': 'Supplier ID', 'required': True},
            },
            'required': ['api_key', 'supplier_id'],
        }

    def _headers(self) -> dict:
        return {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'Supplier-Id': self.supplier_id,
        }

    def _api(self, path, method='GET', body=None):
        url = f'{self.BASE_URL}{path}'
        data = json.dumps(body).encode() if body else None
        req = urllib.request.Request(url, data=data, headers=self._headers(), method=method)
        with urllib.request.urlopen(req, timeout=25) as resp:
            return json.loads(resp.read())

    def health_check(self) -> HealthStatus:
        try:
            self._api('/products')
            return HealthStatus(status='ok', last_check=datetime.utcnow().isoformat())
        except Exception as e:
            return HealthStatus(status='error', message=str(e))

    def fetch_orders(self, since: datetime) -> List[dict]:
        logger.info('[Morrisons] Fetching orders')
        try:
            data = self._api('/orders')
            orders = data.get('orders', [])
            return [self._normalize(o) for o in orders]
        except Exception as e:
            logger.error(f'[Morrisons] Order fetch failed: {e}')
            return []

    def _normalize(self, raw: dict) -> dict:
        return {
            'channel': 'morrisons',
            'channel_order_id': str(raw.get('orderId', '')),
            'order_number': raw.get('orderReference', ''),
            'order_date': raw.get('orderDate', ''),
            'status': 'shipped' if raw.get('status') == 'despatched' else 'pending',
            'customer': {'name': raw.get('customerName', ''), 'email': ''},
            'items': [{'title': i.get('productName', ''), 'sku': i.get('sku', ''),
                        'qty': i.get('quantity', 1), 'price': i.get('price', 0)}
                       for i in raw.get('items', [])],
            'total': float(raw.get('orderTotal', 0)),
            'currency': 'GBP',
            'tracking_number': '',
            'carrier': '',
        }

    def fetch_listings(self) -> List[dict]:
        logger.info('[Morrisons] Fetching products')
        return []

    def create_listing(self, listing: dict) -> dict:
        return {'success': False, 'error': 'Morrisons listing management via seller portal'}
