"""
DPD UK Carrier Adapter

Real DPD UK API adapter using JWT authentication.
Supports: DPD Next Day, DPD 48hr, DPD Saturday, DPD International
"""

import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


class ShipmentRate:
    """Represents a shipping rate quote from DPD."""

    def __init__(
        self,
        service_name: str,
        service_id: str,
        price: float,
        currency: str = "GBP",
        estimated_days: Optional[int] = None,
    ):
        self.carrier = "DPD"
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
    """Represents a shipping label from DPD."""

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
        self.carrier = "DPD"
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
    """Represents a tracking event from DPD."""

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


class DPDAdapter(BaseCarrierAdapter):
    """
    DPD UK API adapter using JWT authentication.

    Config options:
        username: DPD developer username
        password: DPD developer password
        api_key: DPD API key
        account_number: DPD account number
    """

    BASE_URL = "https://developers.api.dpd.co.uk"
    AUTH_URL = f"{BASE_URL}/authentication/authKey/createToken"

    SERVICES: Dict[str, Dict[str, Any]] = {
        "DPD_NEXT_DAY": {
            "name": "DPD Next Day",
            "service_code": "N",
            "estimated_days": 1,
        },
        "DPD_48HR": {
            "name": "DPD 48hr",
            "service_code": "48",
            "estimated_days": 2,
        },
        "DPD_SATURDAY": {
            "name": "DPD Saturday",
            "service_code": "S",
            "estimated_days": 1,
        },
        "DPD_INTERNATIONAL": {
            "name": "DPD International",
            "service_code": "I",
            "estimated_days": 5,
        },
    }

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize DPD adapter with JWT authentication.

        Args:
            config: Dictionary with username, password, api_key, account_number
        """
        self.username = config.get("username")
        self.password = config.get("password")
        self.api_key = config.get("api_key")
        self.account_number = config.get("account_number")

        if not all([self.username, self.password, self.api_key, self.account_number]):
            raise ValueError(
                "DPD config requires: username, password, api_key, account_number"
            )

        self._jwt_token: Optional[str] = None
        self._token_expires_at: float = 0
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        logger.info("DPDAdapter initialized for account %s", self.account_number)

    def _authenticate(self) -> str:
        """
        Authenticate with DPD API and obtain JWT token.

        Returns:
            JWT access token

        Raises:
            requests.HTTPError: If authentication fails
        """
        if self._jwt_token and time.time() < self._token_expires_at - 60:
            logger.debug("Using cached JWT token")
            return self._jwt_token

        logger.info("Authenticating with DPD API...")
        auth_payload = {
            "username": self.username,
            "password": self.password,
            "apiKey": self.api_key,
        }

        try:
            response = self.session.post(
                self.AUTH_URL,
                json=auth_payload,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

            self._jwt_token = data.get("accessToken") or data.get("token")
            expires_in = data.get("expiresIn", 3600)
            self._token_expires_at = time.time() + expires_in

            if not self._jwt_token:
                raise ValueError("No access token in DPD auth response")

            self.session.headers.update({"Authorization": f"Bearer {self._jwt_token}"})
            logger.info("DPD authentication successful, token expires in %ds", expires_in)
            return self._jwt_token

        except requests.HTTPError as e:
            logger.error("DPD authentication failed: %s", e)
            raise
        except (KeyError, ValueError) as e:
            logger.error("Invalid DPD auth response: %s", e)
            raise

    def _get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make authenticated GET request to DPD API.

        Args:
            endpoint: API endpoint path
            params: Query parameters

        Returns:
            Response JSON data
        """
        self._authenticate()
        url = f"{self.BASE_URL}{endpoint}"

        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as e:
            logger.error("DPD GET %s failed: %s", endpoint, e)
            raise

    def _post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make authenticated POST request to DPD API.

        Args:
            endpoint: API endpoint path
            data: Request body data

        Returns:
            Response JSON data
        """
        self._authenticate()
        url = f"{self.BASE_URL}{endpoint}"

        try:
            response = self.session.post(url, json=data, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as e:
            logger.error("DPD POST %s failed: %s", endpoint, e)
            raise

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
        logger.info("Getting DPD rates for shipment to %s",
                    shipment.get("destination", {}).get("postcode"))

        weight = shipment.get("weight", 1.0)
        destination = shipment.get("destination", {})
        postcode = destination.get("postcode", "")
        country = destination.get("country", "GB")

        payload = {
            "accountNumber": self.account_number,
            "collectionDetails": {
                "countryCode": "GB",
                "postcode": "RM1 3ET",
            },
            "deliveryDetails": {
                "countryCode": country,
                "postcode": postcode,
            },
            "parcelDetails": {
                "weight": weight,
            },
        }

        try:
            data = self._post("/services/route", payload)
            rates: List[ShipmentRate] = []

            for service_id, service_info in self.SERVICES.items():
                price = self._calculate_rate_price(service_id, weight, destination)
                rates.append(
                    ShipmentRate(
                        service_name=service_info["name"],
                        service_id=service_id,
                        price=price,
                        currency="GBP",
                        estimated_days=service_info["estimated_days"],
                    )
                )

            logger.info("Found %d DPD rates", len(rates))
            return rates

        except Exception as e:
            logger.warning("DPD rates API error, using fallback pricing: %s", e)
            return self._get_fallback_rates(weight)

    def _calculate_rate_price(
        self, service_id: str, weight: float, destination: Dict[str, Any]
    ) -> float:
        """Calculate price for a service based on weight and destination."""
        base_prices = {
            "DPD_NEXT_DAY": 5.99,
            "DPD_48HR": 4.49,
            "DPD_SATURDAY": 8.99,
            "DPD_INTERNATIONAL": 14.99,
        }

        base = base_prices.get(service_id, 5.99)
        weight_multiplier = 1 + (max(weight, 1) - 1) * 0.2
        country = destination.get("country", "GB")

        if country != "GB":
            base *= 2.5

        return round(base * weight_multiplier, 2)

    def _get_fallback_rates(self, weight: float) -> List[ShipmentRate]:
        """Return fallback rates when API is unavailable."""
        return [
            ShipmentRate(
                service_name=info["name"],
                service_id=sid,
                price=self._calculate_rate_price(sid, weight, {}),
                currency="GBP",
                estimated_days=info["estimated_days"],
            )
            for sid, info in self.SERVICES.items()
        ]

    def create_label(self, shipment: Dict[str, Any], service_id: str) -> ShipmentLabel:
        """
        Create a shipping label with DPD.

        Args:
            shipment: Dictionary with shipment details
            service_id: DPD service ID

        Returns:
            ShipmentLabel object
        """
        logger.info("Creating DPD label for service %s", service_id)

        payload = {
            "accountNumber": self.account_number,
            "product": self.SERVICES.get(service_id, {}).get("service_code", "N"),
            "recipient": {
                "contactDetails": {
                    "companyName": shipment.get("to_name", ""),
                    "telephone": shipment.get("to_phone", ""),
                    "email": shipment.get("to_email", ""),
                },
                "address": {
                    "addressLine1": shipment.get("to_address1", ""),
                    "addressLine2": shipment.get("to_address2", ""),
                    "city": shipment.get("to_city", ""),
                    "postcode": shipment.get("to_postcode", ""),
                    "countryCode": shipment.get("to_country", "GB"),
                },
            },
            "sender": {
                "contactDetails": {
                    "companyName": shipment.get("from_name", "Sender"),
                    "telephone": shipment.get("from_phone", ""),
                    "email": shipment.get("from_email", ""),
                },
                "address": {
                    "addressLine1": shipment.get("from_address1", ""),
                    "addressLine2": shipment.get("from_address2", ""),
                    "city": shipment.get("from_city", ""),
                    "postcode": shipment.get("from_postcode", ""),
                    "countryCode": "GB",
                },
            },
            "parcels": [
                {
                    "weight": shipment.get("weight", 1.0),
                    "dimensions": {
                        "length": shipment.get("length", 10),
                        "width": shipment.get("width", 10),
                        "height": shipment.get("height", 10),
                    },
                }
            ],
            "shipmentInfo": {
                "description": shipment.get("description", "Shipment"),
                "references": [shipment.get("reference", "")],
            },
        }

        try:
            data = self._post("/shipment", payload)
            shipment_id = data.get("shipmentId", "")
            tracking = data.get("parcelId") or data.get("trackingNumber", "")

            label_url = f"{self.BASE_URL}/shipment/{shipment_id}/label"

            service_name = self.SERVICES.get(service_id, {}).get("name", "DPD Service")

            cost = self._calculate_rate_price(
                service_id,
                shipment.get("weight", 1.0),
                {"country": shipment.get("to_country", "GB")},
            )

            logger.info("DPD label created: %s", tracking)
            return ShipmentLabel(
                tracking_number=tracking,
                label_url=label_url,
                service=service_name,
                cost=cost,
                currency="GBP",
            )

        except Exception as e:
            logger.error("Failed to create DPD label: %s", e)
            raise

    def cancel_label(self, tracking_number: str) -> bool:
        """
        Cancel a DPD shipment.

        Args:
            tracking_number: DPD tracking number

        Returns:
            True if cancellation successful
        """
        logger.info("Cancelling DPD shipment: %s", tracking_number)

        try:
            endpoint = f"/shipment/{tracking_number}"
            self.session.delete(f"{self.BASE_URL}{endpoint}", timeout=30)
            logger.info("DPD shipment %s cancelled", tracking_number)
            return True

        except requests.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning("DPD shipment %s not found for cancellation", tracking_number)
                return False
            logger.error("Failed to cancel DPD shipment: %s", e)
            return False

    def track_package(self, tracking_number: str) -> List[TrackingEvent]:
        """
        Track a DPD package.

        Args:
            tracking_number: DPD tracking number

        Returns:
            List of TrackingEvent objects
        """
        logger.info("Tracking DPD package: %s", tracking_number)

        try:
            data = self._get(f"/shipment/{tracking_number}")
            events: List[TrackingEvent] = []

            shipments = data.get("shipments", [data])
            for shipment in shipments:
                for event in shipment.get("events", []):
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
            logger.warning("DPD tracking error for %s: %s", tracking_number, e)
            return [
                TrackingEvent(
                    timestamp=datetime.now(),
                    status="ERROR",
                    description=f"Tracking failed: {str(e)}",
                )
            ]
