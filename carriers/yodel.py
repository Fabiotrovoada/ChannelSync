from __future__ import annotations

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


class YodelAdapter(BaseCarrierAdapter):
    carrier_name = "Yodel"

    BASE_URL = "https://api.yodel.co.uk"

    SERVICE_MAP: dict[str, dict[str, str]] = {
        "STANDARD": {"name": "Yodel Standard", "id": "STANDARD"},
        "EXPRESS": {"name": "Yodel Express", "id": "EXPRESS"},
        "MORNING": {"name": "Yodel Morning", "id": "MORNING"},
        "INTERNATIONAL": {"name": "Yodel International", "id": "INTERNATIONAL"},
    }

    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__(config)
        self._base_url = config.get("base_url", self.BASE_URL)

    def _api_headers(self) -> dict[str, str]:
        api_key = self.config.get("api_key")
        if not api_key:
            raise CarrierAPIError("Yodel adapter requires api_key")
        return {
            "X-API-Key": api_key,
            "Content-Type": "application/json",
            "X-API-Version": "1",
        }

    def get_rates(self, request: RateRequest) -> list[ShipmentRate]:
        params = self._build_rate_params(request)
        try:
            data = self._request_with_retry(
                "GET",
                f"{self._base_url}/v1/rates",
                headers=self._api_headers(),
                json=None,
                data=None,
            )
            return self._parse_rates_response(data)
        except Exception as exc:
            raise CarrierAPIError(f"Yodel get_rates failed: {exc}") from exc

    def _build_rate_params(self, request: RateRequest) -> dict[str, Any]:
        params: dict[str, Any] = {
            "origin_postcode": request.sender_postal_code,
            "destination_postcode": request.recipient_postal_code,
            "weight_kg": request.package_weight_kg,
        }
        if request.package_dimensions:
            params.update(
                {
                    "length_cm": request.package_dimensions.get("length", 10),
                    "width_cm": request.package_dimensions.get("width", 10),
                    "height_cm": request.package_dimensions.get("height", 10),
                }
            )
        if request.service_ids:
            params["service"] = request.service_ids[0]
        return params

    def _parse_rates_response(self, data: dict[str, Any]) -> list[ShipmentRate]:
        rates: list[ShipmentRate] = []
        try:
            services = data.get("services", data.get("rates", []))
            for svc in services:
                service_id = svc.get("service_id", svc.get("id", ""))
                service_info = self.SERVICE_MAP.get(
                    service_id,
                    {"name": f"Yodel {service_id}", "id": service_id},
                )
                price_info = svc.get("price", svc.get("cost", {}))
                if isinstance(price_info, dict):
                    price = float(price_info.get("amount", 0))
                    currency = price_info.get("currency", "GBP")
                else:
                    price = float(price_info)
                    currency = "GBP"

                estimated_days = svc.get("estimated_delivery_days", None)

                rates.append(
                    ShipmentRate(
                        carrier="Yodel",
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
                f"{self._base_url}/v1/shipments",
                headers=self._api_headers(),
                json=payload,
            )
            return self._parse_shipment_response(data, request.service_id)
        except Exception as exc:
            raise CarrierAPIError(f"Yodel create_shipment failed: {exc}") from exc

    def _build_shipment_payload(self, request: ShipmentRequest) -> dict[str, Any]:
        account_id = self.config.get("account_id", "")
        payload: dict[str, Any] = {
            "account_id": account_id,
            "service": request.service_id,
            "sender": {
                "name": request.sender_name,
                "address_line_1": request.sender_address_line1,
                "city": request.sender_city,
                "postcode": request.sender_postal_code,
                "country": request.sender_country,
            },
            "recipient": {
                "name": request.recipient_name,
                "address_line_1": request.recipient_address_line1,
                "city": request.recipient_city,
                "postcode": request.recipient_postal_code,
                "country": request.recipient_country,
            },
            "parcels": [
                {
                    "weight_kg": request.package_weight_kg,
                }
            ],
        }

        if request.package_dimensions:
            parcel = payload["parcels"][0]
            parcel.update(
                {
                    "length_cm": request.package_dimensions.get("length", 10),
                    "width_cm": request.package_dimensions.get("width", 10),
                    "height_cm": request.package_dimensions.get("height", 10),
                }
            )

        return payload

    def _parse_shipment_response(
        self, data: dict[str, Any], service_id: str
    ) -> ShipmentLabel:
        try:
            shipment = data.get("shipment", data.get("data", {}))
            shipment_id = shipment.get("id", shipment.get("shipment_id", ""))
            tracking_number = shipment.get("tracking_number", shipment_id)

            label_url = f"{self._base_url}/v1/shipments/{shipment_id}/label"

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
                f"Yodel {service_id}",
            )

            return ShipmentLabel(
                tracking_number=tracking_number,
                label_url=label_url,
                carrier="Yodel",
                service=service_name,
                cost=cost,
                currency=currency,
            )
        except Exception as exc:
            raise CarrierAPIError(f"Yodel parse shipment response failed: {exc}") from exc

    def get_tracking(self, request: TrackingRequest) -> list[TrackingEvent]:
        tracking_number = request.tracking_number
        try:
            data = self._request_with_retry(
                "GET",
                f"{self._base_url}/v1/shipments/{tracking_number}",
                headers=self._api_headers(),
                json=None,
                data=None,
            )
            return self._parse_tracking_response(data)
        except Exception as exc:
            raise CarrierAPIError(f"Yodel get_tracking failed: {exc}") from exc

    def _parse_tracking_response(self, data: dict[str, Any]) -> list[TrackingEvent]:
        events: list[TrackingEvent] = []
        try:
            shipment = data.get("shipment", data.get("data", {}))
            tracking_events = shipment.get("events", shipment.get("tracking_events", []))

            for event in tracking_events:
                timestamp = event.get("timestamp", event.get("datetime", ""))
                status = event.get("status", "UNKNOWN")
                description = event.get("description", event.get("message", "Unknown"))
                location = event.get("location", event.get("depots", ""))

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
