from adapters.amazon import AmazonAdapter
from adapters.ebay import EbayAdapter
from adapters.woocommerce import WooCommerceAdapter
from adapters.shopify import ShopifyAdapter
from adapters.tiktok import TikTokAdapter
from adapters.mirakl import MiraklAdapter

ADAPTERS = {
    'amazon': AmazonAdapter,
    'ebay': EbayAdapter,
    'woocommerce': WooCommerceAdapter,
    'shopify': ShopifyAdapter,
    'tiktok': TikTokAdapter,
    'mirakl': MiraklAdapter,
}


def get_adapter(channel_type):
    cls = ADAPTERS.get(channel_type)
    if cls:
        return cls()
    return None
