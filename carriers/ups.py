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


class UPSAdapter(BaseCarrierAdapter):
    carrier_name = "UPS"

    AUTH_URL = "https://onlinetools.ups.com/security/v1/oauth/token"
    RATES_URL = "https://onlinetools.ups.com/api/rating/v2205"
    SHIP_URL = "https://onlinetools.ups.com/api/shipments/v2205"
    TRACK_URL = "https://onlinetools.ups.com/api/tracking/v1/details"

    SERVICE_MAP: dict[str, dict[str, str]] = {
        "01": {"name": "UPS Next Day Air", "id": "01"},
        "02": {"name": "UPS 2nd Day Air", "id": "02"},
        "03": {"name": "UPS Ground", "id": "03"},
        "13": {"name": "UPS Express", "id": "13"},
        "65": {"name": "UPS Saver", "id": "65"},
        "11": {"name": "UPS Worldwide Express", "id": "11"},
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
            raise CarrierAPIError("UPS adapter requires client_id and client_secret")

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
            raise CarrierAPIError(f"UPS authentication failed: {exc}") from exc

    def _headers(self) -> dict[str, str]:
        token = self._authenticate()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "transId": f"vendstack-{int(time.time())}",
            "transactionSrc": "vendstack",
        }

    def get_rates(self, request: RateRequest) -> list[ShipmentRate]:
        payload = self._build_rate_request(request)
        try:
            data = self._request_with_retry(
                "POST",
                self.RATES_URL,
                headers=self._headers(),
                json=payload,
            )
            return self._parse_rates_response(data)
        except Exception as exc:
            raise CarrierAPIError(f"UPS get_rates failed: {exc}") from exc

    def _build_rate_request(self, request: RateRequest) -> dict[str, Any]:
        account_number = self.config.get("account_number", "")
        return {
            "RateRequest": {
                "Request": {
                    "TransactionReference": {
                        "CustomerContext": "vendstack-rate-request",
                        "XpciVersion": "1.0",
                    }
                },
                "Shipment": {
                    "Shipper": {
                        "Name": "Shipper",
                        "ShipperNumber": account_number,
                        "Address": {
                            "PostalCode": request.sender_postal_code,
                            "CountryCode": "GB",
                        },
                    },
                    "ShipTo": {
                        "Name": "Recipient",
                        "Address": {
                            "PostalCode": request.recipient_postal_code,
                            "CountryCode": "GB",
                        },
                    },
                    "Package": [
                        {
                            "PackagingType": {"Code": "02", "Description": "Customer Supplied"},
                            "PackageWeight": {
                                "UnitOfMeasurement": "KGS",
                                "Weight": str(request.package_weight_kg),
                            },
                        }
                    ],
                },
            }
        }

    def _parse_rates_response(self, data: dict[str, Any]) -> list[ShipmentRate]:
        rates: list[ShipmentRate] = []
        try:
            rated_shipments = (
                data.get("RateResponse", {})
                .get("RatedShipment", [])
            )
            for shipment in rated_shipments:
                service_code = shipment.get("Service", {}).get("Code", "")
                service_info = self.SERVICE_MAP.get(
                    service_code,
                    {"name": f"UPS Service {service_code}", "id": service_code},
                )
                charge = shipment.get("TotalCharges", {})
                price = float(charge.get("MonetaryValue", 0))
                currency = charge.get("CurrencyCode", "GBP")

                guaranteed = shipment.get("Guaranteed", {})
                delivery_time = None
                if isinstance(guaranteed, dict):
                    delivery_date = guaranteed.get("DeliveryByEndOfDay", "")
                    if delivery_date:
                        delivery_time = 1

                rates.append(
                    ShipmentRate(
                        carrier="UPS",
                        service_name=service_info["name"],
                        service_id=service_info["id"],
                        price=price,
                        currency=currency,
                        estimated_days=delivery_time,
                    )
                )
        except Exception:
            pass
        return rates

    def create_shipment(self, request: ShipmentRequest) -> ShipmentLabel:
        payload = self._build_shipment_request(request)
        try:
            data = self._request_with_retry(
                "POST",
                self.SHIP_URL,
                headers=self._headers(),
                json=payload,
            )
            return self._parse_shipment_response(data, request.service_id)
        except Exception as exc:
            raise CarrierAPIError(f"UPS create_shipment failed: {exc}") from exc

    def _build_shipment_request(self, request: ShipmentRequest) -> dict[str, Any]:
        account_number = self.config.get("account_number", "")
        package = {
            "PackagingType": {"Code": "02", "Description": "Customer Supplied"},
            "PackageWeight": {
                "UnitOfMeasurement": "KGS",
                "Weight": str(request.package_weight_kg),
            },
        }
        if request.package_dimensions:
            package["Dimensions"] = {
                "UnitOfMeasurement": "CMT",
                "Length": str(request.package_dimensions.get("length", 10)),
                "Width": str(request.package_dimensions.get("width", 10)),
                "Height": str(request.package_dimensions.get("height", 10)),
            }

        return {
            "ShipmentRequest": {
                "Request": {
                    "TransactionReference": {
                        "CustomerContext": "vendstack-shipment",
                        "XpciVersion": "1.0",
                    }
                },
                "Shipment": {
                    "Shipper": {
                        "Name": request.sender_name,
                        "ShipperNumber": account_number,
                        "Address": {
                            "AddressLine1": request.sender_address_line1,
                            "City": request.sender_city,
                            "PostalCode": request.sender_postal_code,
                            "CountryCode": request.sender_country,
                        },
                    },
                    "ShipTo": {
                        "Name": request.recipient_name,
                        "Address": {
                            "AddressLine1": request.recipient_address_line1,
                            "City": request.recipient_city,
                            "PostalCode": request.recipient_postal_code,
                            "CountryCode": request.recipient_country,
                        },
                    },
                    "Service": {"Code": request.service_id},
                    "Package": [package],
                },
                "LabelSpecification": {
                    "LabelImageFormat": {"Code": "GIF"},
                    "HTTPUserAgent": "VendStack/1.0",
                },
            }
        }

    def _parse_shipment_response(
        self, data: dict[str, Any], service_id: str
    ) -> ShipmentLabel:
        try:
            shipment = data.get("ShipmentResponse", {}).get("ShipmentResults", {})
            tracking_number = shipment.get("PackageResults", [{}])[0].get(
                "TrackingNumber", ""
            )
            label_url = ""
            label_image = (
                shipment.get("PackageResults", [{}])[0].get("ShippingLabel", {})
            )
            graphic_image = label_image.get("GraphicImage", "")
            if graphic_image:
                label_url = f"data:image/gif;base64,{graphic_image}"

            charge = shipment.get("ShipmentCharge", [])
            cost = 0.0
            currency = "GBP"
            if isinstance(charge, list) and len(charge) > 0:
                cost = float(charge[0].get("TotalCharge", {}).get("MonetaryValue", 0))
                currency = charge[0].get("TotalCharge", {}).get("CurrencyCode", "GBP")

            service_name = next(
                (
                    v["name"]
                    for v in self.SERVICE_MAP.values()
                    if v["id"] == service_id
                ),
                f"UPS Service {service_id}",
            )

            return ShipmentLabel(
                tracking_number=tracking_number,
                label_url=label_url,
                carrier="UPS",
                service=service_name,
                cost=cost,
                currency=currency,
            )
        except Exception as exc:
            raise CarrierAPIError(f"UPS parse shipment response failed: {exc}") from exc

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
            raise CarrierAPIError(f"UPS get_tracking failed: {exc}") from exc

    def _parse_tracking_response(self, data: dict[str, Any]) -> list[TrackingEvent]:
        events: list[TrackingEvent] = []
        try:
            track_response = data.get("trackResponse", {}).get("shipment", [{}])
            if not track_response:
                return events
            package = track_response[0].get("package", [{}])[0]
            activity = package.get("activity", [])
            for act in activity:
                location = act.get("location", {})
                city = location.get("address", {}).get("city", "")
                country = location.get("address", {}).get("countryCode", "")
                loc_str = ", ".join(filter(None, [city, country]))

                status = act.get("status", {})
                description = status.get("description", "Unknown")

                date_str = act.get("date", "")
                time_str = act.get("time", "")
                timestamp = f"{date_str}T{time_str}" if date_str else ""

                events.append(
                    TrackingEvent(
                        timestamp=timestamp,
                        status=status.get("type", "UNKNOWN"),
                        description=description,
                        location=loc_str,
                    )
                )
        except Exception:
            pass
        return events
