"""
VendStack Carrier Adapters.

All carrier integrations for multi-carrier shipping.
"""
from carriers.base_carrier import (
    BaseCarrierAdapter,
    ShipmentRate,
    ShipmentLabel,
    TrackingEvent,
    ShipmentAddress,
    ShipmentParcel,
    CarrierError,
    RateLimitError,
    AuthenticationError,
)

# Lazy loading — import actual adapters on demand
__all__ = [
    'BaseCarrierAdapter',
    'ShipmentRate',
    'ShipmentLabel',
    'TrackingEvent',
    'ShipmentAddress',
    'ShipmentParcel',
    'CarrierError',
    'RateLimitError',
    'AuthenticationError',
    'get_carrier_adapter',
]


def get_carrier_adapter(carrier_type: str, config: dict) -> BaseCarrierAdapter:
    """
    Factory function to get the right carrier adapter.

    Args:
        carrier_type: One of 'royal_mail', 'dpd', 'evri', 'dhl', 'ups', 'fedex', 'yodel', 'parcelforce', 'shipstation'
        config: dict with carrier-specific credentials

    Returns:
        BaseCarrierAdapter instance
    """
    adapters = {
        'royal_mail': 'RoyalMailAdapter',
        'dpd': 'DPDAdapter',
        'evri': 'EvriAdapter',
        'dhl': 'DHLAdapter',
        'ups': 'UPSAdapter',
        'fedex': 'FedExAdapter',
        'yodel': 'YodelAdapter',
        'parcelforce': 'ParcelforceAdapter',
        'shipstation': 'ShipStationCarrierAdapter',
    }

    if carrier_type == 'shipstation':
        # ShipStation uses the core shipstation module
        from core.shipstation import ShipStationCarrierAdapter
        return ShipStationCarrierAdapter(config)

    adapter_name = adapters.get(carrier_type.lower())
    if not adapter_name:
        raise ValueError(f'Unknown carrier: {carrier_type}. Available: {list(adapters.keys())}')

    # Dynamic import
    carrier_module = carrier_type.replace('_', '').lower()
    if carrier_type == 'royal_mail':
        from carriers.royal_mail import RoyalMailAdapter
        return RoyalMailAdapter(config)
    elif carrier_type == 'dpd':
        try:
            from carriers.dpd import DPDAdapter
            return DPDAdapter(config)
        except Exception:
            raise ImportError('DPD adapter not yet implemented')
    elif carrier_type == 'evri':
        try:
            from carriers.evri import EvriAdapter
            return EvriAdapter(config)
        except Exception:
            raise ImportError('Evri adapter not yet implemented')
    elif carrier_type == 'dhl':
        try:
            from carriers.dhl import DHLAdapter
            return DHLAdapter(config)
        except Exception:
            raise ImportError('DHL adapter not yet implemented')
    elif carrier_type == 'ups':
        try:
            from carriers.ups import UPSAdapter
            return UPSAdapter(config)
        except Exception:
            raise ImportError('UPS adapter not yet implemented')
    elif carrier_type == 'fedex':
        try:
            from carriers.fedex import FedExAdapter
            return FedExAdapter(config)
        except Exception:
            raise ImportError('FedEx adapter not yet implemented')
    elif carrier_type == 'yodel':
        try:
            from carriers.yodel import YodelAdapter
            return YodelAdapter(config)
        except Exception:
            raise ImportError('Yodel adapter not yet implemented')
    elif carrier_type == 'parcelforce':
        try:
            from carriers.parcelforce import ParcelforceAdapter
            return ParcelforceAdapter(config)
        except Exception:
            raise ImportError('Parcelforce adapter not yet implemented')
    else:
        raise ValueError(f'Carrier adapter not available: {carrier_type}')
