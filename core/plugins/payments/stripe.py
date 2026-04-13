"""
core/plugins/payments/stripe.py

Stripe payment integration for VendStack.
Track Stripe balance, transactions, and payouts.
Auth: API Key (sk_live_... or sk_test_...)
Docs: https://stripe.com/docs/api
"""
import stripe, logging, datetime
from typing import List, Dict, Any
from core.plugins import Plugin, PluginType, register, HealthStatus

logger = logging.getLogger(__name__)

@register(PluginType.PAYMENTS, 'stripe', 'Stripe', '💳', '1.0.0',
          'Track Stripe balance, transactions, and payouts alongside orders')
class StripePlugin(Plugin):
    """Stripe payments integration."""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.api_key = config.get('api_key', '')
        stripe.api_key = self.api_key
    
    def config_schema(self) -> dict:
        return {
            'type': 'object',
            'properties': {
                'api_key': {'type': 'string', 'label': 'Stripe Secret Key', 'required': True, 'secret': True},
            },
            'required': ['api_key'],
        }
    
    def health_check(self) -> HealthStatus:
        try:
            stripe.Balance.retrieve()
            return HealthStatus(status='ok', last_check=datetime.utcnow().isoformat())
        except Exception as e:
            return HealthStatus(status='error', message=str(e))
    
    def get_balance(self) -> dict:
        """Get Stripe account balance."""
        try:
            balance = stripe.Balance.retrieve()
            return {
                'available': balance.available.amount / 100,
                'pending': balance.pending.amount / 100,
                'currency': balance.available.currency,
            }
        except Exception as e:
            logger.error(f'[Stripe] Balance fetch failed: {e}')
            return {'error': str(e)}
    
    def get_transactions(self, since: datetime) -> List[dict]:
        """Get Stripe charges/payments since date."""
        try:
            charges = stripe.Charge.list(created={'gte': int(since.timestamp())}, limit=100)
            return [{'id': c.id, 'amount': c.amount/100, 'currency': c.currency, 
                     'description': c.description, 'created': datetime.fromtimestamp(c.created).isoformat(),
                     'status': c.status} for c in charges.data]
        except Exception as e:
            logger.error(f'[Stripe] Transactions fetch failed: {e}')
            return []
    
    def get_payouts(self) -> List[dict]:
        """Get Stripe payouts to bank account."""
        try:
            payouts = stripe.Payout.list(limit=50)
            return [{'id': p.id, 'amount': p.amount/100, 'currency': p.currency,
                     'status': p.status, 'arrival_date': datetime.fromtimestamp(p.arrival_date).isoformat()} 
                    for p in payouts.data]
        except Exception as e:
            logger.error(f'[Stripe] Payouts fetch failed: {e}')
            return []
