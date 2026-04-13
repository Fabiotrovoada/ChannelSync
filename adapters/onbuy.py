"""OnBuy UK API adapter."""

import hashlib
import json
import logging
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

from .base import ChannelAdapter

logger = logging.getLogger(__name__)


class OnBuyAdapter(ChannelAdapter):
    """OnBuy UK API adapter using Bearer token authentication."""

    BASE_URL = "https://api.onbuy.com/v2"

    def __init__(self):
        self.secret_key: Optional[str] = None
        self.consumer_id: Optional[str] = None
        self.site_id: int = 1
        self.access_token: Optional[str] = None
        self._token_expiry: float = 0

    def configure(self, credentials: dict):
        """Store OnBuy API credentials."""
        super().configure(credentials)
        self.secret_key = credentials.get("secret_key")
        self.consumer_id = credentials.get("consumer_id")
        self.site_id = credentials.get("site_id", 1)
        logger.info(f"OnBuy adapter configured for site_id={self.site_id}")

    def _get_auth_token(self) -> str:
        """Generate the OnBuy authorization token (signature-based)."""
        timestamp = int(time.time())
        msg = f"{self.consumer_id}{self.secret_key}{timestamp}"
        signature = hashlib.sha256(msg.encode()).hexdigest()
        return f"{self.consumer_id};{timestamp};{signature}"

    def _api_request(
        self,
        method: str,
        path: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
    ) -> Optional[Dict]:
        """Make an authenticated request to the OnBuy API."""
        url = f"{self.BASE_URL}{path}"
        if params:
            qs = "&".join(f"{k}={v}" for k, v in params.items())
            url = f"{url}?{qs}"

        auth_token = self._get_auth_token()
        headers = {
            "Authorization": f"Bearer {auth_token}",
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
            logger.error(f"OnBuy API error {method} {path}: {e.code} {body}")
            return None
        except Exception as e:
            logger.error(f"OnBuy API request error {method} {path}: {e}")
            return None

    def fetch_orders(self, since: str) -> List[Dict[str, Any]]:
        """Fetch OnBuy orders since the given ISO timestamp."""
        logger.info(f"Fetching OnBuy orders since {since}")
        all_orders: List[Dict[str, Any]] = []
        offset = 0
        limit = 50

        while True:
            result = self._api_request(
                "POST",
                "/orders",
                data={
                    "site_id": self.site_id,
                    "offset": offset,
                    "limit": limit,
                    "date_from": since,
                    "all_statuses": True,
                },
            )
            if result is None:
                break

            orders = result.get("results", [])
            if not orders:
                break

            for o in orders:
                order = self._normalize_order(o)
                all_orders.append(order)

            if len(orders) < limit:
                break
            offset += limit

        logger.info(f"Fetched {len(all_orders)} OnBuy orders")
        return all_orders

    def _normalize_order(self, order: Dict) -> Dict[str, Any]:
        """Convert an OnBuy order into a NormalizedOrder dict."""
        items = []
        for p in order.get("products", []):
            items.append({
                "sku": p.get("sku", ""),
                "title": p.get("name", ""),
                "quantity": p.get("qty", 1),
                "price": float(p.get("price", 0)),
                "channel_listing_id": str(p.get("product_id", "")),
            })

        customer = {
            "name": order.get("customer", {}).get("name", ""),
            "email": order.get("customer", {}).get("email", ""),
        }

        status_map = {
            "pending": "pending",
            "processing": "paid",
            "dispatched": "shipped",
            "delivered": "delivered",
            "cancelled": "cancelled",
            "refunded": "refunded",
        }
        raw_status = order.get("status", "pending")
        status = status_map.get(raw_status, raw_status)

        return {
            "channel": "onbuy",
            "channel_order_id": str(order.get("id", "")),
            "order_number": str(order.get("order_id", "")),
            "order_date": order.get("date_created", ""),
            "status": status,
            "customer": customer,
            "items": items,
            "total": float(order.get("total", 0)),
            "currency": "GBP",
        }

    def push_tracking(self, order_id: str, tracking: str, carrier: str) -> bool:
        """Push tracking number to OnBuy order."""
        logger.info(f"Pushing tracking {tracking} ({carrier}) to OnBuy order {order_id}")
        payload = {
            "site_id": self.site_id,
            "order_id": int(order_id),
            "tracking_no": tracking,
            "courier": carrier,
        }
        result = self._api_request("PUT", "/orders/dispatch", data=payload)
        if result is not None:
            logger.info(f"Tracking pushed to OnBuy order {order_id}")
            return True
        logger.warning(f"Failed to push tracking to OnBuy order {order_id}")
        return False

    def fetch_listings(self) -> List[Dict[str, Any]]:
        """Fetch all OnBuy product listings."""
        logger.info("Fetching OnBuy listings")
        all_listings: List[Dict[str, Any]] = []
        offset = 0
        limit = 100

        while True:
            result = self._api_request(
                "POST",
                "/products/list",
                data={
                    "site_id": self.site_id,
                    "offset": offset,
                    "limit": limit,
                },
            )
            if result is None:
                break

            products = result.get("results", [])
            if not products:
                break

            for p in products:
                listing = self._normalize_listing(p)
                all_listings.append(listing)

            if len(products) < limit:
                break
            offset += limit

        logger.info(f"Fetched {len(all_listings)} OnBuy listings")
        return all_listings

    def _normalize_listing(self, product: Dict) -> Dict[str, Any]:
        """Convert an OnBuy product into a NormalizedListing dict."""
        images = product.get("images", [])
        image_url = images[0] if images else ""

        return {
            "channel": "onbuy",
            "sku": product.get("sku", ""),
            "title": product.get("name", ""),
            "description": product.get("description", ""),
            "price": float(product.get("price", 0)),
            "quantity": product.get("stock_level", 0),
            "status": "active" if product.get("status") == "active" else "inactive",
            "image_url": image_url,
            "channel_url": product.get("product_url", ""),
        }

    def create_listing(self, listing: Dict) -> Dict[str, Any]:
        """Create a new OnBuy listing."""
        logger.info(f"Creating OnBuy listing: {listing.get('title', 'unknown')}")
        payload = {
            "site_id": self.site_id,
            "sku": listing.get("sku", ""),
            "name": listing.get("title", ""),
            "description": listing.get("description", ""),
            "price": listing.get("price", 0),
            "stock_quantity": listing.get("quantity", 0),
            "category_id": listing.get("category_id", 0),
        }
        result = self._api_request("POST", "/products", data=payload)
        if result:
            logger.info(f"OnBuy listing created: {listing.get('sku')}")
            pid = result.get("product_id", 0)
            return {"onbuy_product_id": pid, "sku": listing.get("sku", "")}
        logger.error("Failed to create OnBuy listing")
        return {}

    def update_listing(self, sku: str, changes: Dict) -> Dict[str, Any]:
        """Update an existing OnBuy listing by SKU."""
        logger.info(f"Updating OnBuy listing SKU {sku}: {changes}")
        payload = {"site_id": self.site_id, "sku": sku}
        payload.update(changes)
        result = self._api_request("PUT", "/products", data=payload)
        if result:
            logger.info(f"OnBuy listing {sku} updated")
            return {"sku": sku, "updated": True}
        logger.error(f"Failed to update OnBuy listing {sku}")
        return {}

    def fetch_messages(self, since: str) -> List[Dict[str, Any]]:
        """Fetch OnBuy order messages since the given timestamp."""
        logger.info(f"Fetching OnBuy messages since {since}")
        result = self._api_request(
            "POST",
            "/orders",
            data={"site_id": self.site_id, "date_from": since},
        )
        messages: List[Dict[str, Any]] = []
        if result:
            logger.info(f"OnBuy messages fetched (placeholder structure)")
        return messages
