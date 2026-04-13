# VendStack Plugin Architecture

## Overview

VendStack uses a **registry-based plugin system**. All integrations (marketplaces, carriers, 3PLs, services) plug into the same core interface. Adding a new integration requires zero changes to core code — just drop a Python module in the right directory and register it.

## Plugin Registry

Each plugin registers itself in `core/plugins/registry.py`:

```python
from core.plugins import Plugin, PluginType, register

@register(PluginType.MARKETPLACE, id='new_platform', name='New Platform')
class NewPlatformPlugin(Plugin):
    ...
```

## Plugin Types

```python
class PluginType(StrEnum):
    MARKETPLACE = 'marketplace'        # Amazon, eBay, Etsy, etc.
    CARRIER = 'carrier'                # Royal Mail, DPD, UPS, etc.
    AGGREGATOR = 'aggregator'         # ShipStation, Shipmate, etc.
    TPL = '3pl'                       # Third-party logistics
    DROPSHIP = 'dropship'             # Dropship suppliers
    ACCOUNTING = 'accounting'         # Xero, QuickBooks, FreeAgent
    PAYMENTS = 'payments'             # Stripe, Square, PayPal
    RETURNS = 'returns'              # Return Prime, Loop Returns
    REPRICER = 'repricer'            # Repricer, Feedvisor
    BARCODE = 'barcode'               # Barcode scanning hardware
    CRM = 'crm'                      # HubSpot, ActiveCampaign
    DATA = 'data'                     # Analytics, reporting
    IPAAS = 'ipaas'                   # Zapier, Make (Integromat)
    EDI = 'edi'                      # EDI providers
    MRP = 'mrp'                      # Manufacturing/resource planning
    SHIPPING_TOOL = 'shipping_tool'   # Shipping software
```

## Base Plugin Interface

```python
class Plugin(ABC):
    type: PluginType
    id: str                           # unique: 'amazon', 'dpd', 'xero'
    name: str                         # display: 'Amazon UK'
    version: str = '1.0.0'
    icon: str = '📦'                 # emoji icon for UI

    # Lifecycle
    def install(self, config: dict) -> bool: ...
    def uninstall(self) -> bool: ...

    # Health
    def health_check(self) -> HealthStatus: ...

    # Config UI schema (for Settings page)
    def config_schema(self) -> dict: ...

    # Integration-specific methods (defined per plugin type)
    # See below...
```

## Marketplace Plugins

```python
class MarketplacePlugin(Plugin):
    type = PluginType.MARKETPLACE

    async def fetch_orders(self, since: datetime) -> List[NormalizedOrder]: ...
    async def push_tracking(self, order_id: str, tracking: str, carrier: str) -> bool: ...
    async def fetch_listings(self) -> List[NormalizedListing]: ...
    async def create_listing(self, listing: dict) -> dict: ...
    async def update_listing(self, sku: str, changes: dict) -> dict: ...
    async def update_inventory(self, sku: str, qty: int) -> dict: ...
    async def fetch_messages(self, since: datetime) -> List[dict]: ...
```

## Carrier Plugins

```python
class CarrierPlugin(Plugin):
    type = PluginType.CARRIER

    async def get_rates(self, shipment: Shipment) -> List[ShipmentRate]: ...
    async def create_label(self, shipment: Shipment, service_id: str) -> ShipmentLabel: ...
    async def cancel_label(self, tracking: str) -> bool: ...
    async def track_package(self, tracking: str) -> List[TrackingEvent]: ...
```

## Aggregator Plugins

```python
class AggregatorPlugin(Plugin):
    """ShipStation, ShipMate, etc. — aggregates multiple carriers."""
    type = PluginType.AGGREGATOR

    async def get_rates(self, shipment: Shipment) -> List[ShipmentRate]: ...
    async def create_label(self, shipment: Shipment, carrier: str, service: str) -> ShipmentLabel: ...
    async def track_package(self, tracking: str) -> List[TrackingEvent]: ...
```

## 3PL Plugins

```python
class ThirdPartyLogisticsPlugin(Plugin):
    """Amazon FBA, Jewel Freight, etc."""
    type = PluginType.TPL

    async def send_inventory(self, sku: str, qty: int, to_warehouse: str) -> dict: ...
    async def get_stock_levels(self) -> List[dict]: ...
    async def create_fulfillment(self, order: NormalizedOrder) -> dict: ...
    async def get_tracking(self, fulfillment_id: str) -> List[TrackingEvent]: ...
```

## Accounting Plugins

```python
class AccountingPlugin(Plugin):
    type = PluginType.ACCOUNTING

    async def push_invoice(self, order: NormalizedOrder) -> dict: ...
    async def push_expense(self, expense: dict) -> dict: ...
    async def get_overdue_invoices(self) -> List[dict]: ...
    async def sync_contacts(self) -> dict: ...
```

## Payments Plugins

```python
class PaymentsPlugin(Plugin):
    type = PluginType.PAYMENTS

    async def get_balances(self) -> dict: ...
    async def get_transactions(self, since: datetime) -> List[dict]: ...
    async def initiate_payout(self, amount: float, currency: str) -> dict: ...
```

## Returns Plugins

```python
class ReturnsPlugin(Plugin):
    type = PluginType.RETURNS

    async def create_return_label(self, order_id: str, reason: str) -> dict: ...
    async def get_return_status(self, return_id: str) -> dict: ...
    async def process_refund(self, return_id: str) -> bool: ...
```

## Dropship Plugins

```python
class DropshipPlugin(Plugin):
    type = PluginType.DROPSHIP

    async def get_product_feed(self) -> List[dict]: ...
    async def place_dropship_order(self, sku: str, qty: int, address: Address) -> dict: ...
    async def get_dropship_tracking(self, order_id: str) -> List[TrackingEvent]: ...
```

## Plugin Discovery

Plugins are auto-discovered at startup:

```
core/plugins/
├── __init__.py           # Registry + base classes
├── marketplaces/
│   ├── __init__.py
│   ├── amazon.py
│   ├── ebay.py
│   ├── woocommerce.py
│   ├── shopify.py
│   ├── etsy.py
│   ├── walmart.py
│   ├── onbuy.py
│   ├── bigcommerce.py
│   ├── fruugo.py
│   ├── tiktok.py
│   └── magneto.py        # future
├── carriers/
│   ├── __init__.py
│   ├── royal_mail.py
│   ├── dpd.py
│   ├── evri.py
│   ├── dhl.py
│   ├── ups.py
│   ├── fedex.py
│   ├── yodel.py
│   ├── parcelforce.py
│   └── shipstation.py
├── aggregators/
│   ├── __init__.py
│   └── shipstation_agg.py
├── accounting/
│   ├── __init__.py
│   ├── xero.py
│   ├── quickbooks.py
│   └── freeagent.py
├── payments/
│   ├── __init__.py
│   ├── stripe.py
│   └── paypal.py
├── returns/
│   ├── __init__.py
│   └── loop_returns.py
├── repricer/
│   ├── __init__.py
│   └── repricer.py
├── tpl/
│   ├── __init__.py
│   └── amazon_fba.py
└── dropship/
    ├── __init__.py
    └── bJSd.py
```

## Registering a New Plugin

In each plugin file:

```python
from core.plugins import Plugin, PluginType, register

@register(PluginType.MARKETPLACE, id='new_platform', name='New Platform')
class NewPlatformPlugin(Plugin):
    type = PluginType.MARKETPLACE
    id = 'new_platform'
    name = 'New Platform'
    icon = '🆕'
    version = '1.0.0'

    def __init__(self, config: dict):
        self.config = config

    def health_check(self) -> HealthStatus:
        return HealthStatus.OK

    def config_schema(self) -> dict:
        return {
            'api_key': {'type': 'string', 'required': True, 'label': 'API Key'},
            'shop_url': {'type': 'string', 'required': True, 'label': 'Shop URL'},
        }

    async def fetch_orders(self, since: datetime) -> List[NormalizedOrder]:
        ...  # implementation
```

## Installing/Uninstalling Plugins

Merchants install plugins from Settings → Integrations:

```bash
POST /api/plugins/install
{ "plugin_id": "xero", "config": {"api_key": "..."} }

POST /api/plugins/uninstall
{ "plugin_id": "xero" }
```

## Priority Order

1. **Marketplaces** — Magento, PrestaShop
2. **Accounting** — Xero (most requested by UK small businesses)
3. **Payments** — Stripe (for balance tracking)
4. **3PL** — Amazon FBA
5. **Returns** — Loop Returns or ReturnPrime
6. **Repricer** — optional Phase 2
