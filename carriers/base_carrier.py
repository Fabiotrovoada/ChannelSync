"""
VendStack Carrier Adapters — Base Classes.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class CarrierError(Exception):
    """Base exception for carrier operations."""
    pass


class RateLimitError(CarrierError):
    """Rate limited by carrier API."""
    pass


class AuthenticationError(CarrierError):
    """Authentication failed with carrier."""
    pass


@dataclass
class ShipmentRate:
    """Represents a shipping rate quote."""
    carrier: str
    service_name: str
    service_id: str
    price: float
    currency: str = 'GBP'
    estimated_days: Optional[int] = None
    delivery_date: Optional[str] = None
    max_weight_kg: Optional[float] = None

    def to_dict(self) -> dict:
        return {
            'carrier': self.carrier,
            'service_name': self.service_name,
            'service_id': self.service_id,
            'price': self.price,
            'currency': self.currency,
            'estimated_days': self.estimated_days,
            'delivery_date': self.delivery_date,
        }


@dataclass
class ShipmentLabel:
    """Represents a purchased shipping label."""
    tracking_number: str
    label_url: str
    carrier: str
    service: str
    cost: float
    currency: str = 'GBP'

    def to_dict(self) -> dict:
        return {
            'tracking_number': self.tracking_number,
            'label_url': self.label_url,
            'carrier': self.carrier,
            'service': self.service,
            'cost': self.cost,
            'currency': self.currency,
        }


@dataclass
class TrackingEvent:
    """A single tracking event."""
    timestamp: str
    status: str
    description: str
    location: str = ''

    def to_dict(self) -> dict:
        return {
            'timestamp': self.timestamp,
            'status': self.status,
            'description': self.description,
            'location': self.location,
        }


@dataclass
class ShipmentAddress:
    """Standardized shipment address."""
    name: str
    company: str = ''
    address1: str = ''
    address2: str = ''
    city: str = ''
    postcode: str = ''
    country: str = 'GB'
    phone: str = ''
    email: str = ''

    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'company': self.company,
            'address1': self.address1,
            'address2': self.address2,
            'city': self.city,
            'postcode': self.postcode,
            'country': self.country,
            'phone': self.phone,
            'email': self.email,
        }


@dataclass
class ShipmentParcel:
    """A parcel within a shipment."""
    weight: float  # kg
    length: float = 0  # cm
    width: float = 0   # cm
    height: float = 0  # cm
    description: str = ''
    value: float = 0  # GBP, for customs

    def to_dict(self) -> dict:
        return {
            'weight': self.weight,
            'length': self.length,
            'width': self.width,
            'height': self.height,
            'description': self.description,
            'value': self.value,
        }


class BaseCarrierAdapter(ABC):
    """
    Abstract base class for all carrier integrations.

    All carriers must implement these methods:
    - get_rates(shipment) → List[ShipmentRate]
    - create_label(shipment, service_id) → ShipmentLabel
    - cancel_label(tracking_number) → bool
    - track_package(tracking_number) → List[TrackingEvent]
    """

    carrier_name: str = 'base'

    def __init__(self, config: dict):
        self.config = config
        self._validate_config()

    def _validate_config(self):
        """Check required config keys. Override in subclass."""
        pass

    @abstractmethod
    def get_rates(self, shipment: dict) -> List[ShipmentRate]:
        """
        Get available shipping rates for a shipment.

        Args:
            shipment: dict with keys:
                - from: ShipmentAddress dict
                - to: ShipmentAddress dict
                - parcels: list of ShipmentParcel dicts
                - order_id: str
                - value: float (customs value)

        Returns:
            List of ShipmentRate objects
        """
        raise NotImplementedError

    @abstractmethod
    def create_label(self, shipment: dict, service_id: str) -> ShipmentLabel:
        """
        Purchase a shipping label.

        Args:
            shipment: same as get_rates
            service_id: the service_id from a ShipmentRate

        Returns:
            ShipmentLabel object
        """
        raise NotImplementedError

    @abstractmethod
    def cancel_label(self, tracking_number: str) -> bool:
        """Cancel a label. Returns True if successful."""
        raise NotImplementedError

    @abstractmethod
    def track_package(self, tracking_number: str) -> List[TrackingEvent]:
        """Track a package by tracking number. Returns list of tracking events."""
        raise NotImplementedError

    def _standardize_address(self, addr: dict) -> ShipmentAddress:
        """Convert a dict address to ShipmentAddress."""
        if isinstance(addr, ShipmentAddress):
            return addr
        return ShipmentAddress(
            name=addr.get('name', ''),
            company=addr.get('company', ''),
            address1=addr.get('address1', addr.get('line1', '')),
            address2=addr.get('address2', addr.get('line2', '')),
            city=addr.get('city', ''),
            postcode=addr.get('postcode', ''),
            country=addr.get('country', 'GB'),
            phone=addr.get('phone', ''),
            email=addr.get('email', ''),
        )

    def _standardize_parcel(self, parcel: dict) -> ShipmentParcel:
        """Convert a dict parcel to ShipmentParcel."""
        if isinstance(parcel, ShipmentParcel):
            return parcel
        return ShipmentParcel(
            weight=float(parcel.get('weight', 1)),
            length=float(parcel.get('length', 0)),
            width=float(parcel.get('width', 0)),
            height=float(parcel.get('height', 0)),
            description=parcel.get('description', ''),
            value=float(parcel.get('value', 0)),
        )
