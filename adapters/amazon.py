"""Amazon SP-API adapter (stub)."""
from adapters.base import ChannelAdapter


class AmazonAdapter(ChannelAdapter):
    def fetch_orders(self, since):
        # Phase 2: Implement Amazon SP-API order fetch
        return []

    def push_tracking(self, order_id, tracking, carrier):
        # Phase 2: Implement Amazon MWS tracking push
        return False

    def fetch_listings(self):
        return []

    def fetch_messages(self, since):
        return []
