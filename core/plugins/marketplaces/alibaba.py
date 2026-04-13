"""
core/plugins/marketplaces/alibaba.py

Alibaba.com integration for VendStack.
Auth: OAuth 2.0 ( Alibaba Open Platform )
Docs: https://open.alibaba.com/
"""
import json, logging, urllib.request, urllib.parse, datetime, time
from typing import List, Dict, Any
from core.plugins import Plugin, PluginType, register, HealthStatus

logger = logging.getLogger(__name__)

@register(PluginType.MARKETPLACE, 'alibaba', 'Alibaba', '🏭', '1.0.0',
          'B2B marketplace — sell in bulk to international buyers via Alibaba.com')
class AlibabaPlugin(Plugin):
    """Alibaba.com open platform API integration."""

    API_BASE = 'https://gw.open.aliyun.com/api'
    AUTH_URL = 'https://gw.open.aliyun.com/oauth/api'

    def __init__(self, config: dict):
        super().__init__(config)
        self.app_key = config.get('app_key')
        self.app_secret = config.get('app_secret')
        self.access_token = config.get('access_token', '')
        self.token_expiry = 0

    def config_schema(self) -> dict:
        return {
            'type': 'object',
            'properties': {
                'app_key': {'type': 'string', 'label': 'App Key (from Alibaba Open Platform)', 'required': True},
                'app_secret': {'type': 'string', 'label': 'App Secret', 'required': True, 'secret': True},
                'access_token': {'type': 'string', 'label': 'Access Token', 'required': False, 'secret': True},
            },
            'required': ['app_key', 'app_secret'],
        }

    def _sign(self, params: dict) -> str:
        import hmac, hashlib
        sorted_params = sorted(params.items())
        string_to_sign = ''.join(f'{k}{v}' for k, v in sorted_params)
        sign = hmac.new(self.app_secret.encode(), string_to_sign.encode(), hashlib.sha1).digest()
        return sign.hex().upper()

    def _api(self, method, api_name, params=None):
        params = params or {}
        params.update({'app_key': self.app_key, 'timestamp': datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'), 'v': '2.0', 'format': 'json', 'sign_method': 'hmac'})
        params['sign'] = self._sign(params)
        url = f'{self.API_BASE}/{api_name}'
        data = urllib.parse.urlencode(params).encode()
        req = urllib.request.Request(url, data=data, method=method.upper())
        with urllib.request.urlopen(req, timeout=25) as resp:
            return json.loads(resp.read())

    def health_check(self) -> HealthStatus:
        try:
            self._api('POST', 'alibaba.aliexpress.message.template.list')
            return HealthStatus(status='ok', last_check=datetime.utcnow().isoformat())
        except Exception as e:
            return HealthStatus(status='error', message=str(e))

    def fetch_orders(self, since: datetime) -> List[dict]:
        logger.info('[Alibaba] Fetching orders')
        return []

    def fetch_listings(self) -> List[dict]:
        logger.info('[Alibaba] Fetching product listings')
        return []

    def create_listing(self, listing: dict) -> dict:
        return {'success': False, 'error': 'Alibaba listing management via seller portal'}
