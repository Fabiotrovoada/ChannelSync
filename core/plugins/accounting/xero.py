"""
core/plugins/accounting/xero.py

Xero accounting integration for VendStack.
Auth: OAuth 2.0
Docs: https://developer.xero.com/
"""
import json, logging, urllib.request, urllib.parse, datetime
from typing import List, Dict, Any
from core.plugins import Plugin, PluginType, register, HealthStatus

logger = logging.getLogger(__name__)

@register(PluginType.ACCOUNTING, 'xero', 'Xero', '📊', '1.0.0',
          'Sync orders to Xero, track expenses, manage invoices')
class XeroPlugin(Plugin):
    """Xero accounting integration."""
    
    XERO_API = 'https://api.xero.com/api.xro/2.0'
    AUTH_URL = 'https://login.xero.com/identity/connect/authorize'
    TOKEN_URL = 'https://identity.xero.com/connect/token'
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.client_id = config.get('client_id')
        self.client_secret = config.get('client_secret')
        self.tenant_id = config.get('tenant_id')
        self.access_token = config.get('access_token', '')
        self.refresh_token = config.get('refresh_token', '')
        self.token_expiry = config.get('token_expiry', 0)
    
    def config_schema(self) -> dict:
        return {
            'type': 'object',
            'properties': {
                'client_id': {'type': 'string', 'label': 'Client ID', 'required': True},
                'client_secret': {'type': 'string', 'label': 'Client Secret', 'required': True, 'secret': True},
                'tenant_id': {'type': 'string', 'label': 'Tenant ID (Xero Org ID)', 'required': True},
            },
            'required': ['client_id', 'client_secret', 'tenant_id'],
        }
    
    def _refresh_tokens(self) -> bool:
        """Refresh OAuth 2.0 access token."""
        import time
        if self.access_token and time.time() < self.token_expiry - 60:
            return True
        
        params = urllib.parse.urlencode({
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
        })
        
        req = urllib.request.Request(
            self.TOKEN_URL,
            data=params.encode(),
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            method='POST'
        )
        
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())
                self.access_token = data['access_token']
                self.refresh_token = data['refresh_token']
                import time
                self.token_expiry = time.time() + data.get('expires_in', 1800)
                self.config.update({
                    'access_token': self.access_token,
                    'refresh_token': self.refresh_token,
                    'token_expiry': self.token_expiry,
                })
                return True
        except Exception as e:
            logger.error(f'[Xero] Token refresh failed: {e}')
            return False
    
    def _headers(self) -> dict:
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
            'xero-tenant-id': self.tenant_id,
            'Accept': 'application/json',
        }
    
    def _api(self, path: str, method='GET', body=None) -> dict:
        url = f'{self.XERO_API}{path}'
        data = json.dumps(body).encode() if body else None
        req = urllib.request.Request(
            url, data=data,
            headers=self._headers(), method=method
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read())
    
    def health_check(self) -> HealthStatus:
        try:
            self._refresh_tokens()
            self._api('/Users')  # Simple health check endpoint
            return HealthStatus(status='ok', last_check=datetime.utcnow().isoformat())
        except Exception as e:
            return HealthStatus(status='error', message=str(e), last_check=datetime.utcnow().isoformat())
    
    def push_invoice(self, order: dict) -> dict:
        """Create a Xero invoice from a VendStack order."""
        logger.info(f'[Xero] Creating invoice for order {order.get("order_number")}')
        
        line_items = []
        for item in order.get('items', []):
            line_items.append({
                'Description': item.get('title', ''),
                'Quantity': item.get('qty', 1),
                'UnitAmount': item.get('price', 0),
                'AccountCode': '200',  # Sales revenue
                'ItemCode': item.get('sku', ''),
            })
        
        invoice = {
            'Type': 'ACCREC',  # Accounts Receivable (sales invoice)
            'Contact': {
                'Name': order.get('customer', {}).get('name', 'Customer'),
                'EmailAddress': order.get('customer', {}).get('email', ''),
            },
            'LineItems': line_items,
            'InvoiceNumber': order.get('order_number', ''),
            'Reference': order.get('channel_order_id', ''),
            'CurrencyCode': order.get('currency', 'GBP'),
        }
        
        try:
            result = self._api('/Invoices', 'POST', {'Invoices': [invoice]})
            inv = result.get('Invoices', [{}])[0]
            return {'success': True, 'invoice_id': inv.get('InvoiceID', ''), 'invoice_number': inv.get('InvoiceNumber', '')}
        except Exception as e:
            logger.error(f'[Xero] Invoice creation failed: {e}')
            return {'success': False, 'error': str(e)}
    
    def push_expense(self, expense: dict) -> dict:
        """Push an expense/purchase to Xero."""
        logger.info(f'[Xero] Creating expense: {expense.get("description", "")}')
        
        expense_data = {
            'Type': 'ACCPAY',  # Accounts Payable
            'Contact': {'Name': expense.get('vendor', 'Vendor')},
            'LineItems': [{
                'Description': expense.get('description', ''),
                'Quantity': 1,
                'UnitAmount': expense.get('amount', 0),
                'AccountCode': expense.get('account_code', '400'),  # Expense account
            }],
            'Reference': expense.get('reference', ''),
        }
        
        try:
            result = self._api('/Invoices', 'POST', {'Invoices': [expense_data]})
            exp = result.get('Invoices', [{}])[0]
            return {'success': True, 'expense_id': exp.get('InvoiceID', '')}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_overdue_invoices(self) -> List[dict]:
        """Get overdue invoices from Xero."""
        try:
            result = self._api('/Invoices?status=OVERDUE')
            return result.get('Invoices', [])
        except Exception as e:
            logger.error(f'[Xero] Failed to fetch overdue invoices: {e}')
            return []
