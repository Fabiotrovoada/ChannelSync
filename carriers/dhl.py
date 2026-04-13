"""
DHL UK Carrier Adapter

Real DHL UK API adapter using API key authentication.
Supports: DHL Express, DHL Economy Select, DHL Freight
"""

import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


class ShipmentRate:
    """Represents a shipping rate quote from DHL."""

    def __init__(
        self,
        service_name: str,
        service_id: str,
        price: float,
        currency: str = "GBP",
        estimated_days: Optional[int] = None,
    ):
        self.carrier = "DHL"
        self.service_name = service_name
        self.service_id = service_id
        self.price = price
        self.currency = currency
        self.estimated_days = estimated_days

    def __repr__(self) -> str:
        return (
            f"ShipmentRate(carrier={self.carrier}, service={self.service_name}, "
            f"price={self.price} {self.currency}, days={self.estimated_days})"
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "carrier": self.carrier,
            "service_name": self.service_name,
            "service_id": self.service_id,
            "price": self.price,
            "currency": self.currency,
            "estimated_days": self.estimated_days,
        }


class ShipmentLabel:
    """Represents a shipping label from DHL."""

    def __init__(
        self,
        tracking_number: str,
        label_url: str,
        service: str,
        cost: float,
        currency: str = "GBP",
    ):
        self.tracking_number = tracking_number
        self.label_url = label_url
        self.carrier = "DHL"
        self.service = service
        self.cost = cost
        self.currency = currency

    def __repr__(self) -> str:
        return (
            f"ShipmentLabel(tracking={self.tracking_number}, "
            f"service={self.service}, cost={self.cost} {self.currency})"
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tracking_number": self.tracking_number,
            "label_url": self.label_url,
            "carrier": self.carrier,
            "service": self.service,
            "cost": self.cost,
            "currency": self.currency,
        }


class TrackingEvent:
    """Represents a tracking event from DHL."""

    def __init__(
        self,
        timestamp: datetime,
        status: str,
        description: str,
        location: Optional[str] = None,
    ):
        self.timestamp = timestamp
        self.status = status
        self.description = description
        self.location = location

    def __repr__(self) -> str:
        return (
            f"TrackingEvent(status={self.status}, description={self.description}, "
            f"location={self.location})"
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else self.timestamp,
            "status": self.status,
            "description": self.description,
            "location": self.location,
        }


class BaseCarrierAdapter:
    """Base class for carrier adapters."""

    def get_rates(self, shipment: Dict[str, Any]) -> List[ShipmentRate]:
        raise NotImplementedError

    def create_label(self, shipment: Dict[str, Any], service_id: str) -> ShipmentLabel:
        raise NotImplementedError

    def cancel_label(self, tracking_number: str) -> bool:
        raise NotImplementedError

    def track_package(self, tracking_number: str) -> List[TrackingEvent]:
        raise NotImplementedError


class DHLAdapter(BaseCarrierAdapter):
    """
    DHL UK API adapter using API key authentication.

    Config options:
        api_key: DHL API key
        account_number: DHL account number
        base_url: Base API URL (defaults to https://api.dhl.com)
    """

    BASE_URL = "https://api.dhl.com"

    SERVICES: Dict[str, Dict[str, Any]] = {
        "DHL_EXPRESS": {
            "name": "DHL Express",
            "service_code": "P",
            "estimated_days": 1,
        },
        "DHL_ECONOMY_SELECT": {
            "name": "DHL Economy Select",
            "service_code": "H",
            "estimated_days": 5,
        },
        "DHL_FREIGHT": {
            "name": "DHL Freight",
            "service_code": "F",
            "estimated_days": 7,
        },
    }

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize DHL adapter with API key authentication.

        Args:
            config: Dictionary with api_key, account_number, base_url
        """
        self.api_key = config.get("api_key")
        self.account_number = config.get("account_number", "")
        self.base_url = config.get("base_url", self.BASE_URL)

        if not self.api_key:
            raise ValueError("DHL config requires: api_key")

        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Authorization": f"DHL-API-Key {self.api_key}",
        })
        logger.info("DHLAdapter initialized for account %s", self.account_number)

    def _get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make authenticated GET request to DHL API.

        Args:
            endpoint: API endpoint path
            params: Query parameters

        Returns:
            Response JSON data
        """
        url = f"{self.base_url}{endpoint}"

        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as e:
            logger.error("DHL GET %s failed: %s", endpoint, e)
            raise

    def _post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make authenticated POST request to DHL API.

        Args:
            endpoint: API endpoint path
            data: Request body data

        Returns:
            Response JSON data
        """
        url = f"{self.base_url}{endpoint}"

        try:
            response = self.session.post(url, json=data, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as e:
            logger.error("DHL POST %s failed: %s", endpoint, e)
            raise

    def get_rates(self, shipment: Dict[str, Any]) -> List[ShipmentRate]:
        """
        Get available shipping rates for a shipment.

        Args:
            shipment: Dictionary with keys:
                - weight: float (kg)
                - destination: dict with postcode, country
                - dimensions: dict with length, width, height (optional)

        Returns:
            List of ShipmentRate objects
        """
        logger.info("Getting DHL rates for shipment")

        weight = shipment.get("weight", 1.0)
        destination = shipment.get("destination", {})
        postcode = destination.get("postcode", "")
        country = destination.get("country", "GB")
        dimensions = shipment.get("dimensions", {})

        params = {
            "accountNumber": self.account_number,
            "originCountryCode": "GB",
            "originPostalCode": "RM13ET",
            "destinationCountryCode": country,
            "destinationPostalCode": postcode,
            "weight": weight,
            "length": dimensions.get("length", 10),
            "width": dimensions.get("width", 10),
            "height": dimensions.get("height", 10),
        }

        try:
            data = self._get("/rates", params)
            rates: List[ShipmentRate] = []

            service_groups = data.get("products", {})
            for service_id, service_info in self.SERVICES.items():
                product_key = service_info["service_code"]

                if product_key in service_groups:
                    product = service_groups[product_key]
                    price = float(product.get("price", 0))
                else:
                    price = self._calculate_rate_price(service_id, weight, country)

                rates.append(
                    ShipmentRate(
                        service_name=service_info["name"],
                        service_id=service_id,
                        price=price,
                        currency="GBP",
                        estimated_days=service_info["estimated_days"],
                    )
                )

            logger.info("Found %d DHL rates", len(rates))
            return rates

        except Exception as e:
            logger.warning("DHL rates API error, using fallback pricing: %s", e)
            return self._get_fallback_rates(weight, country)

    def _calculate_rate_price(self, service_id: str, weight: float, country: str) -> float:
        """Calculate price for a service based on weight and destination."""
        base_prices = {
            "DHL_EXPRESS": 12.99,
            "DHL_ECONOMY_SELECT": 6.99,
            "DHL_FREIGHT": 9.99,
        }

        base = base_prices.get(service_id, 12.99)
        weight_multiplier = 1 + (max(weight, 1) - 1) * 0.3

        if country != "GB":
            base *= 2.2

        return round(base * weight_multiplier, 2)

    def _get_fallback_rates(self, weight: float, country: str) -> List[ShipmentRate]:
        """Return fallback rates when API is unavailable."""
        return [
            ShipmentRate(
                service_name=info["name"],
                service_id=sid,
                price=self._calculate_rate_price(sid, weight, country),
                currency="GBP",
                estimated_days=info["estimated_days"],
            )
            for sid, info in self.SERVICES.items()
        ]

    def create_label(self, shipment: Dict[str, Any], service_id: str) -> ShipmentLabel:
        """
        Create a shipping label with DHL.

        Args:
            shipment: Dictionary with shipment details
            service_id: DHL service ID

        Returns:
            ShipmentLabel object
        """
        logger.info("Creating DHL label for service %s", service_id)

        service_info = self.SERVICES.get(service_id, {})
        service_code = service_info.get("service_code", "P")

        payload = {
            "plannedShippingDate": datetime.now().strftime("%Y-%m-%d"),
            "productCode": service_code,
            "sender": {
                "postalAddress": {
                    "countryCode": "GB",
                    "postalCode": shipment.get("from_postcode", "RM13ET"),
                    "cityName": shipment.get("from_city", "London"),
                    "addressLine1": shipment.get("from_address1", ""),
                    "addressLine2": shipment.get("from_address2", ""),
                },
                "contactInformation": {
                    "companyName": shipment.get("from_name", "Sender"),
                    "phone": shipment.get("from_phone", ""),
                    "email": shipment.get("from_email", ""),
                },
            },
            "receiver": {
                "postalAddress": {
                    "countryCode": shipment.get("to_country", "GB"),
                    "postalCode": shipment.get("to_postcode", ""),
                    "cityName": shipment.get("to_city", ""),
                    "addressLine1": shipment.get("to_address1", ""),
                    "addressLine2": shipment.get("to_address2", ""),
                },
                "contactInformation": {
                    "companyName": shipment.get("to_name", ""),
                    "phone": shipment.get("to_phone", ""),
                    "email": shipment.get("to_email", ""),
                },
            },
            "packages": [
                {
                    "weight": shipment.get("weight", 1.0),
                    "dimensions": {
                        "length": shipment.get("length", 10),
                        "width": shipment.get("width", 10),
                        "height": shipment.get("height", 10),
                    },
                }
            ],
            "references": {
                "shipmentReference": shipment.get("reference", ""),
            },
        }

        if self.account_number:
            payload["accountNumber"] = self.account_number

        try:
            data = self._post("/shipments", payload)

            tracking = data.get("shipmentTrackingNumber", "")
            label_data = data.get("label", {})
            label_url = label_data.get("labelUrl") or label_data.get("url", "")

            if not label_url and tracking:
                label_url = f"{self.base_url}/shipments/{tracking}/label"

            cost = self._calculate_rate_price(
                service_id,
                shipment.get("weight", 1.0),
                shipment.get("to_country", "GB"),
            )

            logger.info("DHL label created: %s", tracking)
            return ShipmentLabel(
                tracking_number=tracking,
                label_url=label_url,
                service=service_info.get("name", "DHL Service"),
                cost=cost,
                currency="GBP",
            )

        except Exception as e:
            logger.error("Failed to create DHL label: %s", e)
            raise

    def cancel_label(self, tracking_number: str) -> bool:
        """
        Cancel a DHL shipment.

        Args:
            tracking_number: DHL tracking number

        Returns:
            True if cancellation successful
        """
        logger.info("Cancelling DHL shipment: %s", tracking_number)

        try:
            url = f"{self.base_url}/shipments/{tracking_number}"
            response = self.session.delete(url, timeout=30)
            response.raise_for_status()
            logger.info("DHL shipment %s cancelled", tracking_number)
            return True

        except requests.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning("DHL shipment %s not found for cancellation", tracking_number)
                return False
            logger.error("Failed to cancel DHL shipment: %s", e)
            return False

    def track_package(self, tracking_number: str) -> List[TrackingEvent]:
        """
        Track a DHL package.

        Args:
            tracking_number: DHL tracking number

        Returns:
            List of TrackingEvent objects
        """
        logger.info("Tracking DHL package: %s", tracking_number)

        try:
            data = self._get("/tracking", params={"trackingNumber": tracking_number})
            events: List[TrackingEvent] = []

            shipments = data.get("shipments", [])
            for shipment in shipments:
                for event in shipment.get("events", []):
                    try:
                        timestamp_str = event.get("timestamp", "")
                        if timestamp_str:
                            timestamp = datetime.fromisoformat(
                                timestamp_str.replace("Z", "+00:00")
                            )
                        else:
                            timestamp = datetime.now()
                    except (ValueError, AttributeError):
                        timestamp = datetime.now()

                    events.append(
                        TrackingEvent(
                            timestamp=timestamp,
                            status=event.get("statusCode", "UNKNOWN"),
                            description=event.get("description", event.get("statusCode", "")),
                            location=event.get("location", {}).get("address", {}).get("addressLocality", ""),
                        )
                    )

            if not events:
                events.append(
                    TrackingEvent(
                        timestamp=datetime.now(),
                        status="UNKNOWN",
                        description="Tracking information unavailable",
                    )
                )

            logger.info("Found %d tracking events for %s", len(events), tracking_number)
            return events

        except Exception as e:
            logger.warning("DHL tracking error for %s: %s", tracking_number, e)
            return [
                TrackingEvent(
                    timestamp=datetime.now(),
                    status="ERROR",
                    description=f"Tracking failed: {str(e)}",
                )
            ]
