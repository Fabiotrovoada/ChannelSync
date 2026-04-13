"""Abstract base class for channel adapters."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Any


class ChannelAdapter(ABC):
    """Base class all channel adapters must implement."""

    def configure(self, credentials: dict):
        """Store credentials for API calls."""
        self.credentials = credentials

    @abstractmethod
    def fetch_orders(self, since: str) -> List[Dict[str, Any]]:
        """Fetch orders since given ISO timestamp."""
        pass

    @abstractmethod
    def push_tracking(self, order_id: str, tracking: str, carrier: str) -> bool:
        """Push tracking number to channel."""
        pass

    @abstractmethod
    def fetch_listings(self) -> List[Dict[str, Any]]:
        """Fetch all product listings."""
        pass

    @abstractmethod
    def fetch_messages(self, since: str) -> List[Dict[str, Any]]:
        """Fetch customer messages."""
        pass
