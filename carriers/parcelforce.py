from __future__ import annotations

import base64
import time
from typing import Any

import requests

from .base import (
    BaseCarrierAdapter,
    CarrierAPIError,
    RateRequest,
    ShipmentLabel,
    ShipmentRate,
    ShipmentRequest,
    TrackingEvent,
    TrackingRequest,
)


class ParcelforceAdapter(BaseCarrierAdapter):
    carrier_name = "Parcelforce"

    BASE_URL = "https://api.parcelforce.com"

    AUTH_URL = f"{BASE_URL}/oauth/token"
    RATES_URL = f"{BASE_URL}/v1/rates"
    SHIP_URL = f"{BASE_URL}/v1/shipments"
    TRACK_URL = f"{BASE_URL}/v1/tracking"

    SERVICE_MAP: dict[str, dict[str, str]] = {
        "EXPRESS_24": {"name": "Parcelforce Express 24", "id": "EXPRESS_24"},
        "EXPRESS_48": {"name": "Parcelforce Express 48", "id": "EXPRESS_48"},
        "EXPRESS_AM": {"name": "Parcelforce Express AM", "id": "EXPRESS_AM"},
        "INTERNATIONAL": {"name": "Parcelforce International", "id": "INTERNATIONAL"},
    }

    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__(config)
        self._access_token: str | None = None
        self._token_expires_at: float = 0.0

    def _authenticate(self) -> str:
        if self._access_token and time.time() < self._token_expires_at - 60:
            return self._access_token

        client_id = self.config.get("client_id")
        client_secret = self.config.get("client_secret")
        if not client_id or not client_secret:
            raise CarrierAPIError(
                "Parcelforce adapter requires client_id and client_secret"
            )

        credentials = f"{client_id}:{client_secret}"
        encoded = base64.b64encode(credentials.encode()).decode()

        headers = {
            "Authorization": f"Basic {encoded}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        payload = "grant_type=client_credentials"

        try:
            response = requests.post(
                self.AUTH_URL,
                headers=headers,
                data=payload,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            self._access_token = data["access_token"]
            self._token_expires_at = time.time() + data.get("expires_in", 3600)
            return self._access_token
        except requests.RequestException as exc:
            raise CarrierAPIError(f"Parcelforce authentication failed: {exc}") from exc

    def _headers(self) -> dict[str, str]:
        token = self._authenticate()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-Correlation-Id": f"vendstack-{int(time.time())}",
        }

    def get_rates(self, request: RateRequest) -> list[ShipmentRate]:
        payload = self._build_rate_payload(request)
        try:
            data = self._request_with_retry(
                "POST",
                self.RATES_URL,
                headers=self._headers(),
                json=payload,
            )
            return self._parse_rates_response(data)
        except Exception as exc:
            raise CarrierAPIError(f"Parcelforce get_rates failed: {exc}") from exc

    def _build_rate_payload(self, request: RateRequest) -> dict[str, Any]:
        account_number = self.config.get("account_number", "")
        payload: dict[str, Any] = {
            "accountNumber": account_number,
            "origin": {
                "postcode": request.sender_postal_code,
                "country": request.config.get("sender_country", "GB"),
            },
            "destination": {
                "postcode": request.recipient_postal_code,
                "country": request.config.get("recipient_country", "GB"),
            },
            "parcels": [
                {
                    "weight": request.package_weight_kg,
                    "dimensions": request.package_dimensions or {},
                }
            ],
        }
        if request.service_ids:
            payload["services"] = request.service_ids
        if request.saturday_delivery:
            payload["saturdayDelivery"] = True
        return payload

    def _parse_rates_response(self, data: dict[str, Any]) -> list[ShipmentRate]:
        rates: list[ShipmentRate] = []
        try:
            services = data.get("services", data.get("rates", []))
            for svc in services:
                service_id = svc.get("serviceId", svc.get("service_id", ""))
                service_info = self.SERVICE_MAP.get(
                    service_id,
                    {"name": f"Parcelforce {service_id}", "id": service_id},
                )

                price_info = svc.get("price", svc.get("cost", {}))
                if isinstance(price_info, dict):
                    price = float(price_info.get("amount", 0))
                    currency = price_info.get("currency", "GBP")
                else:
                    price = float(price_info) if price_info else 0.0
                    currency = "GBP"

                transit_days = svc.get("transitDays", svc.get("estimated_days", None))
                estimated_days = int(transit_days) if transit_days else None

                rates.append(
                    ShipmentRate(
                        carrier="Parcelforce",
                        service_name=service_info["name"],
                        service_id=service_info["id"],
                        price=price,
                        currency=currency,
                        estimated_days=estimated_days,
                    )
                )
        except Exception:
            pass
        return rates

    def create_shipment(self, request: ShipmentRequest) -> ShipmentLabel:
        payload = self._build_shipment_payload(request)
        try:
            data = self._request_with_retry(
                "POST",
                self.SHIP_URL,
                headers=self._headers(),
                json=payload,
            )
            return self._parse_shipment_response(data, request.service_id)
        except Exception as exc:
            raise CarrierAPIError(f"Parcelforce create_shipment failed: {exc}") from exc

    def _build_shipment_payload(self, request: ShipmentRequest) -> dict[str, Any]:
        account_number = self.config.get("account_number", "")
        payload: dict[str, Any] = {
            "accountNumber": account_number,
            "service": request.service_id,
            "sender": {
                "name": request.sender_name,
                "address": {
                    "line1": request.sender_address_line1,
                    "city": request.sender_city,
                    "postcode": request.sender_postal_code,
                    "country": request.sender_country,
                },
            },
            "recipient": {
                "name": request.recipient_name,
                "address": {
                    "line1": request.recipient_address_line1,
                    "city": request.recipient_city,
                    "postcode": request.recipient_postal_code,
                    "country": request.recipient_country,
                },
            },
            "parcels": [
                {
                    "weight": request.package_weight_kg,
                }
            ],
        }

        if request.package_dimensions:
            parcel = payload["parcels"][0]
            parcel["dimensions"] = {
                "length": request.package_dimensions.get("length", 10),
                "width": request.package_dimensions.get("width", 10),
                "height": request.package_dimensions.get("height", 10),
            }

        return payload

    def _parse_shipment_response(
        self, data: dict[str, Any], service_id: str
    ) -> ShipmentLabel:
        try:
            shipment = data.get("shipment", data.get("data", {}))
            shipment_id = shipment.get("id", shipment.get("shipmentId", ""))
            tracking_number = shipment.get("trackingNumber", shipment_id)

            label_url = f"{self.BASE_URL}/v1/shipments/{shipment_id}/label"

            price_info = shipment.get("price", shipment.get("cost", {}))
            if isinstance(price_info, dict):
                cost = float(price_info.get("amount", 0))
                currency = price_info.get("currency", "GBP")
            else:
                cost = float(price_info) if price_info else 0.0
                currency = "GBP"

            service_name = next(
                (
                    v["name"]
                    for v in self.SERVICE_MAP.values()
                    if v["id"] == service_id
                ),
                f"Parcelforce {service_id}",
            )

            return ShipmentLabel(
                tracking_number=tracking_number,
                label_url=label_url,
                carrier="Parcelforce",
                service=service_name,
                cost=cost,
                currency=currency,
            )
        except Exception as exc:
            raise CarrierAPIError(
                f"Parcelforce parse shipment response failed: {exc}"
            ) from exc

    def get_tracking(self, request: TrackingRequest) -> list[TrackingEvent]:
        params = {"trackingNumber": request.tracking_number}
        try:
            data = self._request_with_retry(
                "GET",
                self.TRACK_URL,
                headers=self._headers(),
                json=None,
                data=None,
            )
            return self._parse_tracking_response(data)
        except Exception as exc:
            raise CarrierAPIError(f"Parcelforce get_tracking failed: {exc}") from exc

    def _parse_tracking_response(self, data: dict[str, Any]) -> list[TrackingEvent]:
        events: list[TrackingEvent] = []
        try:
            tracking = data.get("tracking", data.get("data", {}))
            scan_events = tracking.get("events", tracking.get("scanEvents", []))

            for event in scan_events:
                timestamp = event.get("timestamp", event.get("dateTime", ""))
                status = event.get("status", "UNKNOWN")
                description = event.get("description", event.get("message", "Unknown"))
                location_parts = []
                for key in ("location", "depot", "city"):
                    if event.get(key):
                        location_parts.append(event[key])
                location = ", ".join(location_parts)

                events.append(
                    TrackingEvent(
                        timestamp=timestamp,
                        status=status,
                        description=description,
                        location=location,
                    )
                )
        except Exception:
            pass
        return events
