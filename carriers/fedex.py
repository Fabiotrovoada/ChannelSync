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


class FedExAdapter(BaseCarrierAdapter):
    carrier_name = "FedEx"

    AUTH_URL = "https://apis.fedex.com/oauth/token"
    RATES_URL = "https://apis.fedex.com/rate/v1/rates/quotes"
    SHIP_URL = "https://apis.fedex.com/ship/v1/shipments"
    TRACK_URL = "https://apis.fedex.com/track/v1/trackingnumbers"

    SERVICE_MAP: dict[str, dict[str, str]] = {
        "PRIORITY_OVERNIGHT": {
            "name": "FedEx Priority Overnight",
            "id": "PRIORITY_OVERNIGHT",
        },
        "FEDEX_2_DAY": {"name": "FedEx 2Day", "id": "FEDEX_2_DAY"},
        "FEDEX_GROUND": {"name": "FedEx Ground", "id": "FEDEX_GROUND"},
        "INTERNATIONAL_PRIORITY": {
            "name": "FedEx International Priority",
            "id": "INTERNATIONAL_PRIORITY",
        },
        "INTERNATIONAL_ECONOMY": {
            "name": "FedEx International Economy",
            "id": "INTERNATIONAL_ECONOMY",
        },
    }

    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__(config)
        self._access_token: str | None = None
        self._token_expires_at: float = 0.0

    def _authenticate(self) -> str:
        if self._access_token and time.time() < self._token_expires_at - 60:
            return self._access_token

        api_key = self.config.get("api_key")
        api_secret = self.config.get("api_secret")
        if not api_key or not api_secret:
            raise CarrierAPIError("FedEx adapter requires api_key and api_secret")

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
        }
        payload = {
            "grant_type": "client_credentials",
            "client_id": api_key,
            "client_secret": api_secret,
        }

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
            raise CarrierAPIError(f"FedEx authentication failed: {exc}") from exc

    def _headers(self) -> dict[str, str]:
        token = self._authenticate()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-locale": "en_GB",
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
            raise CarrierAPIError(f"FedEx get_rates failed: {exc}") from exc

    def _build_rate_request(self, request: RateRequest) -> dict[str, Any]:
        account_number = self.config.get("account_number", "")
        requested_services = request.service_ids or list(self.SERVICE_MAP.keys())

        package_line_items = [
            {
                "groupPackageCount": "1",
                "weight": {
                    "units": "KG",
                    "value": request.package_weight_kg,
                },
            }
        ]

        if request.package_dimensions:
            package_line_items[0]["dimensions"] = {
                "length": request.package_dimensions.get("length", 10),
                "width": request.package_dimensions.get("width", 10),
                "height": request.package_dimensions.get("height", 10),
                "units": "CM",
            }

        return {
            "accountNumber": {
                "value": account_number,
            },
            "requestedShipment": {
                "shipper": {
                    "address": {
                        "postalCode": request.sender_postal_code,
                        "countryCode": "GB",
                    }
                },
                "recipients": [
                    {
                        "address": {
                            "postalCode": request.recipient_postal_code,
                            "countryCode": "GB",
                        }
                    }
                ],
                "requestedPackageLineItems": package_line_items,
                "serviceType": requested_services[0] if requested_services else None,
                "packagingType": "YOUR_PACKAGING",
            },
            "requestedServices": requested_services,
            "returnTransitTimes": True,
        }

    def _parse_rates_response(self, data: dict[str, Any]) -> list[ShipmentRate]:
        rates: list[ShipmentRate] = []
        try:
            rate_results = data.get("output", {}).get("rateReplyDetails", [])
            for detail in rate_results:
                service_type = detail.get("serviceType", "")
                service_info = self.SERVICE_MAP.get(
                    service_type,
                    {"name": f"FedEx {service_type}", "id": service_type},
                )

                rated_shipment_details = detail.get("ratedShipmentDetails", [])
                total_price = 0.0
                currency = "GBP"
                if rated_shipment_details:
                    amount_str = (
                        rated_shipment_details[0]
                        .get("totalNetCharge", {})
                        .get("amount", "0")
                    )
                    total_price = float(amount_str)
                    currency = (
                        rated_shipment_details[0]
                        .get("totalNetCharge", {})
                        .get("currency", "GBP")
                    )

                transit_time = detail.get("commitTimestamp", "")
                estimated_days = None
                if transit_time:
                    estimated_days = 1

                if service_type:
                    rates.append(
                        ShipmentRate(
                            carrier="FedEx",
                            service_name=service_info["name"],
                            service_id=service_info["id"],
                            price=total_price,
                            currency=currency,
                            estimated_days=estimated_days,
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
            raise CarrierAPIError(f"FedEx create_shipment failed: {exc}") from exc

    def _build_shipment_request(self, request: ShipmentRequest) -> dict[str, Any]:
        account_number = self.config.get("account_number", "")
        meter_number = self.config.get("meter_number", "")

        package_line_items = [
            {
                "weight": {
                    "units": "KG",
                    "value": request.package_weight_kg,
                },
            }
        ]

        if request.package_dimensions:
            package_line_items[0]["dimensions"] = {
                "length": request.package_dimensions.get("length", 10),
                "width": request.package_dimensions.get("width", 10),
                "height": request.package_dimensions.get("height", 10),
                "units": "CM",
            }

        return {
            "labelResponseOptions": "URL_ONLY",
            "requestedShipment": {
                "shipDatestamp": time.strftime("%Y-%m-%d"),
                "totalPackageCount": "1",
                "shipper": {
                    "contact": {"personName": request.sender_name},
                    "address": {
                        "streetLines": [request.sender_address_line1],
                        "city": request.sender_city,
                        "postalCode": request.sender_postal_code,
                        "countryCode": request.sender_country,
                    },
                },
                "recipients": [
                    {
                        "contact": {"personName": request.recipient_name},
                        "address": {
                            "streetLines": [request.recipient_address_line1],
                            "city": request.recipient_city,
                            "postalCode": request.recipient_postal_code,
                            "countryCode": request.recipient_country,
                        },
                    }
                ],
                "shippingChargesPayment": {
                    "paymentType": "SENDER",
                    "payor": {
                        "responsibleParty": {
                            "accountNumber": {"value": account_number}
                        }
                    },
                },
                "serviceType": request.service_id,
                "packagingType": "YOUR_PACKAGING",
                "requestedPackageLineItems": package_line_items,
            },
            "accountNumber": {"value": account_number},
            "meterNumber": meter_number,
        }

    def _parse_shipment_response(
        self, data: dict[str, Any], service_id: str
    ) -> ShipmentLabel:
        try:
            output = data.get("output", {})
            transaction_id = output.get("transactionId", "")
            job_id = output.get("jobId", "")

            piece_response = output.get("pieceResponseList", [])
            tracking_number = ""
            if piece_response:
                tracking_number = piece_response[0].get("trackingNumber", "")

            document_url = output.get("documents", [{}])[0].get("url", "")
            if not document_url and job_id:
                document_url = f"https://apis.fedex.com/ship/v1/shipments/{job_id}/documents"

            charges = output.get("totalDeclaredValue", {})
            cost = float(charges.get("amount", 0)) if charges else 0.0
            currency = charges.get("currency", "GBP") if charges else "GBP"

            service_name = next(
                (
                    v["name"]
                    for v in self.SERVICE_MAP.values()
                    if v["id"] == service_id
                ),
                f"FedEx {service_id}",
            )

            return ShipmentLabel(
                tracking_number=tracking_number,
                label_url=document_url,
                carrier="FedEx",
                service=service_name,
                cost=cost,
                currency=currency,
            )
        except Exception as exc:
            raise CarrierAPIError(f"FedEx parse shipment response failed: {exc}") from exc

    def get_tracking(self, request: TrackingRequest) -> list[TrackingEvent]:
        payload = {"trackingInfoList": [{"trackingNumberInfo": {"trackingNumber": request.tracking_number}}]}
        try:
            data = self._request_with_retry(
                "GET",
                self.TRACK_URL,
                headers=self._headers(),
                json=payload,
            )
            return self._parse_tracking_response(data)
        except Exception as exc:
            raise CarrierAPIError(f"FedEx get_tracking failed: {exc}") from exc

    def _parse_tracking_response(self, data: dict[str, Any]) -> list[TrackingEvent]:
        events: list[TrackingEvent] = []
        try:
            track_results = (
                data.get("output", {})
                .get("trackResults", [{}])
            )
            for result in track_results:
                scan_events = result.get("scanEvents", [])
                for event in scan_events:
                    timestamp = event.get("date", "") + "T" + event.get("time", "")
                    events.append(
                        TrackingEvent(
                            timestamp=timestamp,
                            status=event.get("eventType", "UNKNOWN"),
                            description=event.get("eventDescription", "Unknown"),
                            location=event.get("scanLocation", {}).get("city", ""),
                        )
                    )
        except Exception:
            pass
        return events
