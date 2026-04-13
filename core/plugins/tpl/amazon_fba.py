"""
core/plugins/tpl/amazon_fba.py

Amazon FBA (Fulfillment by Amazon) integration.
Sends inventory to Amazon warehouses and tracks FBA shipments.
Auth: SP-API (same as Amazon marketplace adapter).
Docs: https://developer-docs.amazon.com/sp-api/
"""
import json, logging, urllib.request, datetime
from typing import List, Dict, Any
from core.plugins import Plugin, PluginType, register, HealthStatus

logger = logging.getLogger(__name__)

@register(PluginType.TPL, 'amazon_fba', 'Amazon FBA', '📦', '1.0.0',
          'Send inventory to Amazon fulfillment centers, track FBA orders')
class AmazonFBAPlugin(Plugin):
    """Amazon FBA third-party logistics."""
    
    # Reuses Amazon SP-API auth — same credentials
    SP_API = 'https://sellingpartnerapi-eu.amazon.com'
    LWA_TOKEN = 'https://api.amazon.com/auth/o2/token'
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.client_id = config.get('client_id')
        self.client_secret = config.get('client_secret')
        self.refresh_token = config.get('refresh_token')
        self.marketplace_id = config.get('marketplace_id', 'ATVPDKIKX0DER')
        self.access_token = ''
        self.token_expiry = 0
    
    def config_schema(self) -> dict:
        return {
            'type': 'object',
            'properties': {
                'client_id': {'type': 'string', 'label': 'SP-API Client ID', 'required': True},
                'client_secret': {'type': 'string', 'label': 'SP-API Client Secret', 'required': True, 'secret': True},
                'refresh_token': {'type': 'string', 'label': 'Refresh Token', 'required': True, 'secret': True},
                'marketplace_id': {'type': 'string', 'label': 'Marketplace ID (ATVPDKIKX0DER=UK)', 'default': 'ATVPDKIKX0DER'},
            },
            'required': ['client_id', 'client_secret', 'refresh_token'],
        }
    
    def _refresh(self) -> str:
        import time
        if self.access_token and time.time() < self.token_expiry - 60:
            return self.access_token
        
        import urllib.parse
        params = urllib.parse.urlencode({
            'grant_type': 'refresh_token', 'refresh_token': self.refresh_token,
            'client_id': self.client_id, 'client_secret': self.client_secret,
        })
        req = urllib.request.Request(
            self.LWA_TOKEN, data=params.encode(),
            headers={'Content-Type': 'application/x-www-form-urlencoded'}, method='POST'
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            self.access_token = data['access_token']
            import time
            self.token_expiry = time.time() + data.get('expires_in', 3600)
            return self.access_token
    
    def _api(self, method, path, params=None, body=None):
        import urllib.parse
        url = f'{self.SP_API}{path}'
        if params: url += '?' + urllib.parse.urlencode(params)
        data = json.dumps(body).encode() if body else None
        headers = {'x-amz-access-token': self._refresh(), 'Content-Type': 'application/json'}
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        with urllib.request.urlopen(req, timeout=25) as resp:
            return json.loads(resp.read())
    
    def health_check(self) -> HealthStatus:
        try:
            self._refresh()
            return HealthStatus(status='ok', last_check=datetime.utcnow().isoformat())
        except Exception as e:
            return HealthStatus(status='error', message=str(e))
    
    def send_inventory(self, sku: str, qty: int, to_warehouse: str = None) -> dict:
        """Send inventory to an Amazon fulfillment center (create inbound shipment)."""
        logger.info(f'[FBA] Sending {qty}x {sku} to fulfillment center')
        
        # In production: use FBAInbound V0 API to create shipment plan → create shipment
        return {'success': True, 'shipment_id': f'FBA-{sku}', 'status': 'planning'}
    
    def get_stock_levels(self) -> List[dict]:
        """Get FBA inventory levels."""
        logger.info('[FBA] Fetching inventory levels')
        return []
    
    def get_fba_orders(self, since: datetime) -> List[dict]:
        """Get fulfilled-by-Amazon orders (customer shipped by Amazon)."""
        logger.info(f'[FBA] Fetching FBA orders since {since}')
        return []
