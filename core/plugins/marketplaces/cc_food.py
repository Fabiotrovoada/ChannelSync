"""
core/plugins/marketplaces/cc_food.py

C&C (Country Computing) / foodservice portal adapter.
Connect to UK foodservice and grocery aggregators.
Auth: API Key
"""
import json, logging, urllib.request, datetime
from typing import List, Dict, Any
from core.plugins import Plugin, PluginType, register, HealthStatus

logger = logging.getLogger(__name__)

@register(PluginType.MARKETPLACE, 'cc_food', 'C&C / Foodservice', '🍎', '1.0.0',
          'UK foodservice marketplace — sell to caterers and food businesses')
class CCFoodPlugin(Plugin):
    """C&C Foodservice portal integration."""

    BASE_URL = 'https://api.ccfood.co.uk/v1'

    def __init__(self, config: dict):
        super().__init__(config)
        self.api_key = config.get('api_key')

    def config_schema(self) -> dict:
        return {
            'type': 'object',
            'properties': {
                'api_key': {'type': 'string', 'label': 'API Key', 'required': True, 'secret': True},
                'base_url': {'type': 'string', 'label': 'API Base URL', 'default': 'https://api.ccfood.co.uk/v1'},
            },
            'required': ['api_key'],
        }

    def _headers(self) -> dict:
        return {'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'}

    def _api(self, path, method='GET', body=None):
        url = f"{self.config.get('base_url', self.BASE_URL)}{path}"
        data = json.dumps(body).encode() if body else None
        req = urllib.request.Request(url, data=data, headers=self._headers(), method=method)
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read())

    def health_check(self) -> HealthStatus:
        try:
            self._api('/products')
            return HealthStatus(status='ok', last_check=datetime.utcnow().isoformat())
        except Exception as e:
            return HealthStatus(status='error', message=str(e))

    def fetch_orders(self, since: datetime) -> List[dict]:
        return []

    def fetch_listings(self) -> List[dict]:
        return []
