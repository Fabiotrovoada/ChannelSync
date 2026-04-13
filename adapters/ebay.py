"""eBay API adapter (stub)."""
from adapters.base import ChannelAdapter


class EbayAdapter(ChannelAdapter):
    def fetch_orders(self, since):
        return []

    def push_tracking(self, order_id, tracking, carrier):
        return False

    def fetch_listings(self):
        return []

    def fetch_messages(self, since):
        return []
