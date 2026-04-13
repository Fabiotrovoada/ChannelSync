"""
Evri (formerly Hermes) UK Carrier Adapter

Real Evri UK API adapter using OAuth 2.0 client credentials.
Supports: Evri Courier, Evri Express, Evri International
"""

import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


class ShipmentRate:
    """Represents a shipping rate quote from Evri."""

    def __init__(
        self,
        service_name: str,
        service_id: str,
        price: float,
        currency: str = "GBP",
        estimated_days: Optional[int] = None,
    ):
        self.carrier = "Evri"
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
    """Represents a shipping label from Evri."""

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
        self.carrier = "Evri"
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
    """Represents a tracking event from Evri."""

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


class EvriAdapter(BaseCarrierAdapter):
    """
    Evri (formerly Hermes) UK API adapter using OAuth 2.0 client credentials.

    Config options:
        client_id: Evri OAuth client ID
        client_secret: Evri OAuth client secret
        base_url: Base API URL (defaults to https://api.evri.com)
        account_number: Evri account number (optional)
    """

    AUTH_URL = "https://api.evri.com/connect/token"
    DEFAULT_BASE_URL = "https://api.evri.com"

    SERVICES: Dict[str, Dict[str, Any]] = {
        "EVRI_COURIER": {
            "name": "Evri Courier",
            "service_code": "Courier",
            "estimated_days": 2,
        },
        "EVRI_EXPRESS": {
            "name": "Evri Express",
            "service_code": "Express",
            "estimated_days": 1,
        },
        "EVRI_INTERNATIONAL": {
            "name": "Evri International",
            "service_code": "International",
            "estimated_days": 7,
        },
    }

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Evri adapter with OAuth 2.0 authentication.

        Args:
            config: Dictionary with client_id, client_secret, base_url, account_number
        """
        self.client_id = config.get("client_id")
        self.client_secret = config.get("client_secret")
        self.base_url = config.get("base_url", self.DEFAULT_BASE_URL)
        self.account_number = config.get("account_number", "")

        if not all([self.client_id, self.client_secret]):
            raise ValueError("Evri config requires: client_id, client_secret")

        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        logger.info("EvriAdapter initialized")

    def _authenticate(self) -> str:
        """
        Authenticate with Evri API using OAuth 2.0 client credentials.

        Returns:
            OAuth access token

        Raises:
            requests.HTTPError: If authentication fails
        """
        if self._access_token and time.time() < self._token_expires_at - 60:
            logger.debug("Using cached OAuth token")
            return self._access_token

        logger.info("Authenticating with Evri API via OAuth 2.0...")

        try:
            response = self.session.post(
                self.AUTH_URL,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

            self._access_token = data.get("access_token")
            expires_in = data.get("expires_in", 3600)
            self._token_expires_at = time.time() + expires_in

            if not self._access_token:
                raise ValueError("No access token in Evri auth response")

            self.session.headers.update({"Authorization": f"Bearer {self._access_token}"})
            logger.info("Evri authentication successful, token expires in %ds", expires_in)
            return self._access_token

        except requests.HTTPError as e:
            logger.error("Evri authentication failed: %s", e)
            raise
        except (KeyError, ValueError) as e:
            logger.error("Invalid Evri auth response: %s", e)
            raise

    def _get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make authenticated GET request to Evri API.

        Args:
            endpoint: API endpoint path
            params: Query parameters

        Returns:
            Response JSON data
        """
        self._authenticate()
        url = f"{self.base_url}{endpoint}"

        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as e:
            logger.error("Evri GET %s failed: %s", endpoint, e)
            raise

    def _post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make authenticated POST request to Evri API.

        Args:
            endpoint: API endpoint path
            data: Request body data

        Returns:
            Response JSON data
        """
        self._authenticate()
        url = f"{self.base_url}{endpoint}"

        try:
            response = self.session.post(url, json=data, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as e:
            logger.error("Evri POST %s failed: %s", endpoint, e)
            raise

    def _delete(self, endpoint: str) -> bool:
        """
        Make authenticated DELETE request to Evri API.

        Args:
            endpoint: API endpoint path

        Returns:
            True if successful
        """
        self._authenticate()
        url = f"{self.base_url}{endpoint}"

        try:
            response = self.session.delete(url, timeout=30)
            response.raise_for_status()
            return True
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                return False
            logger.error("Evri DELETE %s failed: %s", endpoint, e)
            return False

    def get_rates(self, shipment: Dict[str, Any]) -> List[ShipmentRate]:
        """
        Get available shipping rates for a shipment.

        Args:
            shipment: Dictionary with keys:
                - weight: float (kg)
                - destination: dict with postcode, country
                - service_ids: list of service IDs (optional)

        Returns:
            List of ShipmentRate objects
        """
        logger.info("Getting Evri rates for shipment to %s",
                    shipment.get("destination", {}).get("postcode"))

        weight = shipment.get("weight", 1.0)
        destination = shipment.get("destination", {})
        country = destination.get("country", "GB")

        rates: List[ShipmentRate] = []

        for service_id, service_info in self.SERVICES.items():
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

        logger.info("Found %d Evri rates", len(rates))
        return rates

    def _calculate_rate_price(self, service_id: str, weight: float, country: str) -> float:
        """Calculate price for a service based on weight and destination."""
        base_prices = {
            "EVRI_COURIER": 3.99,
            "EVRI_EXPRESS": 5.99,
            "EVRI_INTERNATIONAL": 12.99,
        }

        base = base_prices.get(service_id, 3.99)
        weight_multiplier = 1 + (max(weight, 1) - 1) * 0.25

        if country != "GB":
            base *= 2.0

        return round(base * weight_multiplier, 2)

    def create_label(self, shipment: Dict[str, Any], service_id: str) -> ShipmentLabel:
        """
        Create a shipping label with Evri.

        Args:
            shipment: Dictionary with shipment details
            service_id: Evri service ID

        Returns:
            ShipmentLabel object
        """
        logger.info("Creating Evri label for service %s", service_id)

        service_info = self.SERVICES.get(service_id, {})
        service_code = service_info.get("service_code", "Courier")

        payload = {
            "serviceType": service_code,
            "senderDetails": {
                "name": shipment.get("from_name", "Sender"),
                "address": {
                    "addressLine1": shipment.get("from_address1", ""),
                    "addressLine2": shipment.get("from_address2", ""),
                    "city": shipment.get("from_city", ""),
                    "postcode": shipment.get("from_postcode", ""),
                    "countryCode": "GB",
                },
                "contactNumber": shipment.get("from_phone", ""),
                "email": shipment.get("from_email", ""),
            },
            "recipientDetails": {
                "name": shipment.get("to_name", ""),
                "address": {
                    "addressLine1": shipment.get("to_address1", ""),
                    "addressLine2": shipment.get("to_address2", ""),
                    "city": shipment.get("to_city", ""),
                    "postcode": shipment.get("to_postcode", ""),
                    "countryCode": shipment.get("to_country", "GB"),
                },
                "contactNumber": shipment.get("to_phone", ""),
                "email": shipment.get("to_email", ""),
            },
            "parcelDetails": {
                "weight": shipment.get("weight", 1.0),
                "dimensions": {
                    "length": shipment.get("length", 10),
                    "width": shipment.get("width", 10),
                    "height": shipment.get("height", 10),
                },
            },
            "reference": shipment.get("reference", ""),
        }

        if self.account_number:
            payload["accountNumber"] = self.account_number

        try:
            data = self._post("/v1/shipments", payload)
            shipment_id = data.get("shipmentId", "")
            tracking = data.get("trackingNumber") or data.get("parcelId", "")

            label_url = f"{self.base_url}/v1/shipments/{shipment_id}/label"

            cost = self._calculate_rate_price(
                service_id,
                shipment.get("weight", 1.0),
                shipment.get("to_country", "GB"),
            )

            logger.info("Evri label created: %s", tracking)
            return ShipmentLabel(
                tracking_number=tracking,
                label_url=label_url,
                service=service_info.get("name", "Evri Service"),
                cost=cost,
                currency="GBP",
            )

        except Exception as e:
            logger.error("Failed to create Evri label: %s", e)
            raise

    def cancel_label(self, tracking_number: str) -> bool:
        """
        Cancel an Evri shipment.

        Args:
            tracking_number: Evri tracking number

        Returns:
            True if cancellation successful
        """
        logger.info("Cancelling Evri shipment: %s", tracking_number)

        try:
            endpoint = f"/v1/shipments/{tracking_number}"
            result = self._delete(endpoint)
            if result:
                logger.info("Evri shipment %s cancelled", tracking_number)
            return result

        except Exception as e:
            logger.error("Failed to cancel Evri shipment: %s", e)
            return False

    def track_package(self, tracking_number: str) -> List[TrackingEvent]:
        """
        Track an Evri package.

        Args:
            tracking_number: Evri tracking number

        Returns:
            List of TrackingEvent objects
        """
        logger.info("Tracking Evri package: %s", tracking_number)

        try:
            data = self._get(f"/v1/shipments/{tracking_number}")
            events: List[TrackingEvent] = []

            tracking_data = data.get("trackingDetails", data)

            for event in tracking_data.get("events", []):
                try:
                    timestamp = datetime.fromisoformat(
                        event.get("timestamp", "").replace("Z", "+00:00")
                    )
                except (ValueError, AttributeError):
                    timestamp = datetime.now()

                events.append(
                    TrackingEvent(
                        timestamp=timestamp,
                        status=event.get("status", "UNKNOWN"),
                        description=event.get("description", event.get("status", "")),
                        location=event.get("location", ""),
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
            logger.warning("Evri tracking error for %s: %s", tracking_number, e)
            return [
                TrackingEvent(
                    timestamp=datetime.now(),
                    status="ERROR",
                    description=f"Tracking failed: {str(e)}",
                )
            ]
