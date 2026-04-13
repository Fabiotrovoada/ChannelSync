"""Walmart Marketplace API adapter."""

import base64
import hashlib
import json
import logging
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

from .base import ChannelAdapter

logger = logging.getLogger(__name__)


class WalmartAdapter(ChannelAdapter):
    """Walmart Marketplace API adapter using OAuth 2.0 client credentials."""

    BASE_URL = "https://marketplace.walmartapis.com/v3"
    TOKEN_URL = "https://marketplace.walmartapis.com/v3/token"

    def __init__(self):
        self.client_id: Optional[str] = None
        self.client_secret: Optional[str] = None
        self.consumer_id: Optional[str] = None
        self.access_token: Optional[str] = None
        self._token_expiry: float = 0

    def configure(self, credentials: dict):
        """Store Walmart API credentials."""
        super().configure(credentials)
        self.client_id = credentials.get("client_id")
        self.client_secret = credentials.get("client_secret")
        self.consumer_id = credentials.get("consumer_id")
        logger.info("Walmart adapter configured")

    def _is_token_expired(self) -> bool:
        """Check if the current access token is expired or about to expire."""
        return time.time() >= self._token_expiry - 60

    def _fetch_access_token(self) -> bool:
        """Fetch a new access token using client credentials flow."""
        if not self.client_id or not self.client_secret or not self.consumer_id:
            logger.error("Missing Walmart credentials for token fetch")
            return False

        logger.info("Fetching Walmart OAuth token")
        auth = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()

        data = urllib.parse.urlencode({"grant_type": "client_credentials"}).encode()
        headers = {
            "Authorization": f"Basic {auth}",
            "WM_QOS.CORRELATION_ID": self.consumer_id,
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        }

        req = urllib.request.Request(
            self.TOKEN_URL, data=data, headers=headers, method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read())
                self.access_token = result.get("access_token")
                expires_in = result.get("expires_in", 3600)
                self._token_expiry = time.time() + expires_in
                logger.info("Walmart OAuth token obtained successfully")
                return True
        except urllib.error.HTTPError as e:
            body = e.read().decode() if e.fp else ""
            logger.error(f"Walmart token fetch failed: {e.code} {body}")
            return False
        except Exception as e:
            logger.error(f"Walmart token fetch error: {e}")
            return False

    def _get_access_token(self) -> Optional[str]:
        """Get a valid access token, fetching a new one if expired."""
        if self._is_token_expired():
            if not self._fetch_access_token():
                return None
        return self.access_token

    def _generate_qos_header(self) -> str:
        """Generate a unique QoS correlation ID."""
        return hashlib.sha256(
            f"{self.consumer_id}{time.time()}".encode()
        ).hexdigest()[:32]

    def _api_request(
        self,
        method: str,
        path: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
    ) -> Optional[Dict]:
        """Make an authenticated request to the Walmart API."""
        token = self._get_access_token()
        if not token:
            logger.error("No valid Walmart access token")
            return None

        url = f"{self.BASE_URL}{path}"
        if params:
            qs = "&".join(f"{k}={v}" for k, v in params.items())
            url = f"{url}?{qs}"

        headers = {
            "WM_SEC.ACCESS_TOKEN": token,
            "WM_QOS.CORRELATION_ID": self._generate_qos_header(),
            "WM_CONSUMER.ID": self.consumer_id or "",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        req = urllib.request.Request(url, headers=headers, method=method)
        if data:
            req.data = json.dumps(data).encode()

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            body = e.read().decode() if e.fp else ""
            logger.error(f"Walmart API error {method} {path}: {e.code} {body}")
            return None
        except Exception as e:
            logger.error(f"Walmart API request error {method} {path}: {e}")
            return None

    def fetch_orders(self, since: str) -> List[Dict[str, Any]]:
        """Fetch Walmart orders since the given ISO timestamp."""
        logger.info(f"Fetching Walmart orders since {since}")
        all_orders: List[Dict[str, Any]] = []
        next_cursor: Optional[str] = None

        while True:
            params: Dict[str, Any] = {"createdStartDate": since}
            if next_cursor:
                params["nextCursor"] = next_cursor

            result = self._api_request("GET", "/orders", params=params)
            if result is None:
                break

            orders = result.get("list", {})
            if isinstance(orders, dict):
                orders = orders.get("order", [])
            if not orders:
                break

            if not isinstance(orders, list):
                orders = [orders]

            for o in orders:
                order = self._normalize_order(o)
                all_orders.append(order)

            meta = result.get("meta", {})
            next_cursor = meta.get("nextCursor")
            if not next_cursor:
                break

        logger.info(f"Fetched {len(all_orders)} Walmart orders")
        return all_orders

    def _normalize_order(self, order: Dict) -> Dict[str, Any]:
        """Convert a Walmart order into a NormalizedOrder dict."""
        order_lines = order.get("orderLines", {}).get("orderLine", [])
        if not isinstance(order_lines, list):
            order_lines = [order_lines]

        items = []
        for line in order_lines:
            item = line.get("item", {})
            items.append({
                "sku": item.get("sku", ""),
                "title": item.get("productName", ""),
                "quantity": int(line.get("quantity", {}).get("amount", 1)),
                "price": float(line.get("price", {}).get("unitPrice", {}).get("amount", 0)),
                "channel_listing_id": item.get("productId", ""),
            })

        customer = {
            "name": order.get("shippingInfo", {}).get("phone", ""),
            "email": order.get("shippingInfo", {}).get("email", ""),
        }

        status_map = {
            "Created": "pending",
            "Acknowledged": "paid",
            "Shipped": "shipped",
            "Delivered": "delivered",
            "Cancelled": "cancelled",
        }
        raw_status = order.get("orderStatus", "Created")
        status = status_map.get(raw_status, raw_status.lower())

        total = float(order.get("orderTotal", {}).get("amount", 0))

        return {
            "channel": "walmart",
            "channel_order_id": str(order.get("purchaseOrderId", "")),
            "order_number": str(order.get("customerOrderId", "")),
            "order_date": order.get("orderDate", ""),
            "status": status,
            "customer": customer,
            "items": items,
            "total": total,
            "currency": order.get("currency", "USD"),
        }

    def push_tracking(self, order_id: str, tracking: str, carrier: str) -> bool:
        """Push tracking number to Walmart order."""
        logger.info(f"Pushing tracking {tracking} ({carrier}) to Walmart order {order_id}")
        payload = {
            "orderSource": "Walmart",
            "shipmentTrackingNumber": tracking,
            "shipMethod": carrier,
        }
        result = self._api_request(
            "PUT", f"/orders/{order_id}/shipping", data=payload
        )
        if result is not None:
            logger.info(f"Tracking pushed to Walmart order {order_id}")
            return True
        logger.warning(f"Failed to push tracking to Walmart order {order_id}")
        return False

    def fetch_listings(self) -> List[Dict[str, Any]]:
        """Fetch all Walmart items."""
        logger.info("Fetching Walmart items")
        all_items: List[Dict[str, Any]] = []
        next_cursor: Optional[str] = None

        while True:
            params: Dict[str, Any] = {}
            if next_cursor:
                params["nextCursor"] = next_cursor

            result = self._api_request("GET", "/items", params=params)
            if result is None:
                break

            items = result.get("ItemResponse", [])
            if not items:
                items = result.get("items", [])
            if not items:
                break

            for item in items:
                listing = self._normalize_listing(item)
                all_items.append(listing)

            meta = result.get("meta", {})
            next_cursor = meta.get("nextCursor")
            if not next_cursor:
                break

        logger.info(f"Fetched {len(all_items)} Walmart items")
        return all_items

    def _normalize_listing(self, item: Dict) -> Dict[str, Any]:
        """Convert a Walmart item into a NormalizedListing dict."""
        return {
            "channel": "walmart",
            "sku": item.get("sku", ""),
            "title": item.get("productName", ""),
            "description": item.get("longDescription", ""),
            "price": float(item.get("price", 0)),
            "quantity": int(item.get("quantity", 0)),
            "status": "active" if item.get("status", "").lower() == "published" else "inactive",
            "image_url": item.get("imageUrl", ""),
            "channel_url": "",
        }

    def create_listing(self, listing: Dict) -> Dict[str, Any]:
        """Create a new Walmart item."""
        logger.info(f"Creating Walmart listing: {listing.get('title', 'unknown')}")
        payload = {
            "sku": listing.get("sku", ""),
            "productName": listing.get("title", ""),
            "description": listing.get("description", ""),
            "price": listing.get("price", 0),
            "quantity": listing.get("quantity", 0),
        }
        result = self._api_request("POST", "/items", data=payload)
        if result:
            logger.info(f"Walmart listing created: {listing.get('sku')}")
            return self._normalize_listing(result)
        logger.error("Failed to create Walmart listing")
        return {}

    def update_listing(self, sku: str, changes: Dict) -> Dict[str, Any]:
        """Update an existing Walmart item by SKU."""
        logger.info(f"Updating Walmart listing SKU {sku}: {changes}")
        result = self._api_request("PUT", f"/items/{sku}", data=changes)
        if result:
            logger.info(f"Walmart listing {sku} updated")
            return self._normalize_listing(result)
        logger.error(f"Failed to update Walmart listing {sku}")
        return {}

    def fetch_messages(self, since: str) -> List[Dict[str, Any]]:
        """Fetch Walmart supplier messages since the given timestamp."""
        logger.info(f"Fetching Walmart messages since {since}")
        result = self._api_request(
            "GET",
            "/items",
            params={"publishedDate.startDate": since},
        )
        messages: List[Dict[str, Any]] = []
        if result:
            logger.info(f"Fetched messages (placeholder — Walmart uses separate feeds)")
        return messages
