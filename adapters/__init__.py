"""
VendStack Channel Adapters — all marketplace integrations.
"""
from adapters.amazon import AmazonAdapter
from adapters.ebay import EbayAdapter
from adapters.woocommerce import WooCommerceAdapter
from adapters.shopify import ShopifyAdapter
from adapters.etsy import EtsyAdapter
from adapters.walmart import WalmartAdapter
from adapters.onbuy import OnBuyAdapter
from adapters.bigcommerce import BigCommerceAdapter
from adapters.fruugo import FruugoAdapter
from adapters.tiktok import TikTokAdapter
from adapters.mirakl import MiraklAdapter

# All supported channel adapters
ADAPTERS = {
    'amazon': AmazonAdapter,
    'ebay': EbayAdapter,
    'woocommerce': WooCommerceAdapter,
    'woocommerce': WooCommerceAdapter,
    'shopify': ShopifyAdapter,
    'etsy': EtsyAdapter,
    'walmart': WalmartAdapter,
    'onbuy': OnBuyAdapter,
    'bigcommerce': BigCommerceAdapter,
    'fruugo': FruugoAdapter,
    'tiktok': TikTokAdapter,
    'mirakl': MiraklAdapter,
}


def get_adapter(channel_type: str, config: dict = None) -> 'ChannelAdapter':
    """
    Factory to get a channel adapter instance with config.

    Args:
        channel_type: 'amazon', 'ebay', 'woocommerce', 'shopify', etc.
        config: dict with channel credentials (client_id, api_key, etc.)

    Returns:
        ChannelAdapter subclass instance
    """
    adapter_cls = ADAPTERS.get(channel_type.lower())
    if not adapter_cls:
        raise ValueError(f'Unknown channel: {channel_type}. Available: {list(ADAPTERS.keys())}')

    if config is None:
        config = {}

    try:
        return adapter_cls(config)
    except Exception as e:
        raise ValueError(f'Failed to initialize {channel_type} adapter: {e}')


def get_all_channel_types() -> list:
    """Return list of all supported channel types."""
    return list(ADAPTERS.keys())


__all__ = [
    'ADAPTERS',
    'get_adapter',
    'get_all_channel_types',
    'AmazonAdapter',
    'EbayAdapter',
    'WooCommerceAdapter',
    'ShopifyAdapter',
    'EtsyAdapter',
    'WalmartAdapter',
    'OnBuyAdapter',
    'BigCommerceAdapter',
    'FruugoAdapter',
    'TikTokAdapter',
    'MiraklAdapter',
]
