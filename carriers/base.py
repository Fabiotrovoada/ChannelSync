from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ShipmentRate:
    carrier: str
    service_name: str
    service_id: str
    price: float
    currency: str = "GBP"
    estimated_days: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "carrier": self.carrier,
            "service_name": self.service_name,
            "service_id": self.service_id,
            "price": self.price,
            "currency": self.currency,
            "estimated_days": self.estimated_days,
        }


@dataclass
class ShipmentLabel:
    tracking_number: str
    label_url: str
    carrier: str
    service: str
    cost: float
    currency: str = "GBP"

    def to_dict(self) -> dict[str, Any]:
        return {
            "tracking_number": self.tracking_number,
            "label_url": self.label_url,
            "carrier": self.carrier,
            "service": self.service,
            "cost": self.cost,
            "currency": self.currency,
        }


@dataclass
class TrackingEvent:
    timestamp: str
    status: str
    description: str
    location: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "status": self.status,
            "description": self.description,
            "location": self.location,
        }


class RateRequest:
    def __init__(
        self,
        sender_postal_code: str,
        recipient_postal_code: str,
        package_weight_kg: float,
        package_dimensions: dict[str, float] | None = None,
        service_ids: list[str] | None = None,
        saturday_delivery: bool = False,
    ) -> None:
        self.sender_postal_code = sender_postal_code
        self.recipient_postal_code = recipient_postal_code
        self.package_weight_kg = package_weight_kg
        self.package_dimensions = package_dimensions or {}
        self.service_ids = service_ids
        self.saturday_delivery = saturday_delivery


class ShipmentRequest:
    def __init__(
        self,
        sender_postal_code: str,
        recipient_postal_code: str,
        package_weight_kg: float,
        service_id: str,
        sender_name: str,
        recipient_name: str,
        sender_address_line1: str,
        recipient_address_line1: str,
        sender_city: str,
        recipient_city: str,
        sender_country: str = "GB",
        recipient_country: str = "GB",
        package_dimensions: dict[str, float] | None = None,
    ) -> None:
        self.sender_postal_code = sender_postal_code
        self.recipient_postal_code = recipient_postal_code
        self.package_weight_kg = package_weight_kg
        self.service_id = service_id
        self.sender_name = sender_name
        self.recipient_name = recipient_name
        self.sender_address_line1 = sender_address_line1
        self.recipient_address_line1 = recipient_address_line1
        self.sender_city = sender_city
        self.recipient_city = recipient_city
        self.sender_country = sender_country
        self.recipient_country = recipient_country
        self.package_dimensions = package_dimensions or {}


class TrackingRequest:
    def __init__(self, tracking_number: str) -> None:
        self.tracking_number = tracking_number


class BaseCarrierAdapter(ABC):
    carrier_name: str = "BASE"

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config

    @abstractmethod
    def get_rates(self, request: RateRequest) -> list[ShipmentRate]:
        raise NotImplementedError

    @abstractmethod
    def create_shipment(self, request: ShipmentRequest) -> ShipmentLabel:
        raise NotImplementedError

    @abstractmethod
    def get_tracking(self, request: TrackingRequest) -> list[TrackingEvent]:
        raise NotImplementedError

    def _request_with_retry(
        self,
        method: str,
        url: str,
        headers: dict[str, str] | None = None,
        json: dict[str, Any] | None = None,
        data: bytes | None = None,
        retries: int = 3,
        backoff: float = 1.0,
    ) -> dict[str, Any]:
        import requests

        attempt = 0
        while attempt <= retries:
            try:
                response = requests.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=json,
                    data=data,
                    timeout=30,
                )
                if response.status_code in (429, 500, 502, 503, 504):
                    attempt += 1
                    if attempt > retries:
                        response.raise_for_status()
                    time.sleep(backoff * attempt)
                    continue
                response.raise_for_status()
                return response.json() if response.text else {}
            except requests.RequestException as exc:
                raise CarrierAPIError(str(exc)) from exc


class CarrierAPIError(Exception):
    pass


class AuthenticationError(CarrierAPIError):
    pass


class RateLimitError(CarrierAPIError):
    pass
