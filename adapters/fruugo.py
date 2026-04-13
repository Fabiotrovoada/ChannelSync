"""Fruugo API adapter."""

import json
import logging
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

from .base import ChannelAdapter

logger = logging.getLogger(__name__)


class FruugoAdapter(ChannelAdapter):
    """Fruugo API adapter using Bearer token authentication."""

    def __init__(self):
        self.api_key: Optional[str] = None
        self.base_url: str = "https://api.fruugo.com"

    def configure(self, credentials: dict):
        """Store Fruugo API credentials."""
        super().configure(credentials)
        self.api_key = credentials.get("api_key")
        self.base_url = credentials.get("base_url", "https://api.fruugo.com")
        logger.info(f"Fruugo adapter configured, base_url={self.base_url}")

    def _api_request(
        self,
        method: str,
        path: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
    ) -> Optional[Dict]:
        """Make an authenticated request to the Fruugo API."""
        url = f"{self.base_url}{path}"
        if params:
            qs = "&".join(f"{k}={v}" for k, v in params.items())
            url = f"{url}?{qs}"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
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
            logger.error(f"Fruugo API error {method} {path}: {e.code} {body}")
            return None
        except Exception as e:
            logger.error(f"Fruugo API request error {method} {path}: {e}")
            return None

    def fetch_orders(self, since: str) -> List[Dict[str, Any]]:
        """Fetch Fruugo orders since the given ISO timestamp."""
        logger.info(f"Fetching Fruugo orders since {since}")
        all_orders: List[Dict[str, Any]] = []
        page = 1
        page_size = 50

        while True:
            result = self._api_request(
                "GET",
                "/orders",
                params={"page": page, "pageSize": page_size, "fromDate": since},
            )
            if result is None:
                break

            orders = result.get("orders", result.get("data", []))
            if not orders:
                break

            if not isinstance(orders, list):
                orders = [orders]

            for o in orders:
                order = self._normalize_order(o)
                all_orders.append(order)

            total_pages = result.get("pagination", {}).get("totalPages", 1)
            if page >= total_pages:
                break
            page += 1

        logger.info(f"Fetched {len(all_orders)} Fruugo orders")
        return all_orders

    def _normalize_order(self, order: Dict) -> Dict[str, Any]:
        """Convert a Fruugo order into a NormalizedOrder dict."""
        items = []
        for item in order.get("items", []):
            items.append({
                "sku": item.get("sku", ""),
                "title": item.get("name", ""),
                "quantity": item.get("quantity", 1),
                "price": float(item.get("unitPrice", 0)),
                "channel_listing_id": str(item.get("productId", "")),
            })

        customer = {
            "name": order.get("customerName", ""),
            "email": order.get("customerEmail", ""),
        }

        status_map = {
            "PENDING": "pending",
            "PROCESSING": "paid",
            "SHIPPED": "shipped",
            "DELIVERED": "delivered",
            "CANCELLED": "cancelled",
            "REFUNDED": "refunded",
        }
        raw_status = order.get("status", "PENDING")
        status = status_map.get(raw_status, raw_status.lower())

        return {
            "channel": "fruugo",
            "channel_order_id": str(order.get("orderId", "")),
            "order_number": str(order.get("orderReference", "")),
            "order_date": order.get("orderDate", ""),
            "status": status,
            "customer": customer,
            "items": items,
            "total": float(order.get("totalAmount", 0)),
            "currency": order.get("currency", "USD"),
        }

    def push_tracking(self, order_id: str, tracking: str, carrier: str) -> bool:
        """Push tracking number to Fruugo order."""
        logger.info(f"Pushing tracking {tracking} ({carrier}) to Fruugo order {order_id}")
        payload = {
            "orderId": order_id,
            "trackingNumber": tracking,
            "carrier": carrier,
        }
        result = self._api_request("PUT", "/orders/{}/tracking".format(order_id), data=payload)
        if result is not None:
            logger.info(f"Tracking pushed to Fruugo order {order_id}")
            return True
        logger.warning(f"Failed to push tracking to Fruugo order {order_id}")
        return False

    def fetch_listings(self) -> List[Dict[str, Any]]:
        """Fetch all Fruugo product listings."""
        logger.info("Fetching Fruugo listings")
        all_listings: List[Dict[str, Any]] = []
        page = 1
        page_size = 50

        while True:
            result = self._api_request(
                "GET",
                "/products",
                params={"page": page, "pageSize": page_size},
            )
            if result is None:
                break

            products = result.get("products", result.get("data", []))
            if not products:
                break

            if not isinstance(products, list):
                products = [products]

            for p in products:
                listing = self._normalize_listing(p)
                all_listings.append(listing)

            total_pages = result.get("pagination", {}).get("totalPages", 1)
            if page >= total_pages:
                break
            page += 1

        logger.info(f"Fetched {len(all_listings)} Fruugo listings")
        return all_listings

    def _normalize_listing(self, product: Dict) -> Dict[str, Any]:
        """Convert a Fruugo product into a NormalizedListing dict."""
        images = product.get("images", [])
        image_url = images[0].get("url", "") if images else ""

        return {
            "channel": "fruugo",
            "sku": product.get("sku", ""),
            "title": product.get("name", ""),
            "description": product.get("description", ""),
            "price": float(product.get("price", 0)),
            "quantity": product.get("stock", 0),
            "status": "active" if product.get("status", "").lower() == "active" else "inactive",
            "image_url": image_url,
            "channel_url": product.get("productUrl", ""),
        }

    def create_listing(self, listing: Dict) -> Dict[str, Any]:
        """Create a new Fruugo listing."""
        logger.info(f"Creating Fruugo listing: {listing.get('title', 'unknown')}")
        payload = {
            "sku": listing.get("sku", ""),
            "name": listing.get("title", ""),
            "description": listing.get("description", ""),
            "price": listing.get("price", 0),
            "stock": listing.get("quantity", 0),
        }
        result = self._api_request("POST", "/products", data=payload)
        if result:
            pid = result.get("productId", 0)
            logger.info(f"Fruugo listing created: id={pid}")
            return {"productId": pid, "sku": listing.get("sku", "")}
        logger.error("Failed to create Fruugo listing")
        return {}

    def update_listing(self, sku: str, changes: Dict) -> Dict[str, Any]:
        """Update an existing Fruugo listing by SKU."""
        logger.info(f"Updating Fruugo listing SKU {sku}: {changes}")
        product_id = self._find_product_id_by_sku(sku)
        if not product_id:
            logger.warning(f"No Fruugo product found for SKU {sku}")
            return {}

        result = self._api_request("PUT", f"/products/{product_id}", data=changes)
        if result:
            logger.info(f"Fruugo listing {product_id} updated")
            return {"productId": product_id, "updated": True}
        logger.error(f"Failed to update Fruugo listing {product_id}")
        return {}

    def _find_product_id_by_sku(self, sku: str) -> Optional[str]:
        """Find Fruugo product ID by SKU."""
        page = 1
        page_size = 50
        while True:
            result = self._api_request(
                "GET",
                "/products",
                params={"page": page, "pageSize": page_size, "sku": sku},
            )
            if not result:
                break
            products = result.get("products", result.get("data", []))
            if products and isinstance(products, list):
                for p in products:
                    if p.get("sku") == sku:
                        return str(p.get("productId", ""))
            pagination = result.get("pagination", {})
            if page >= pagination.get("totalPages", 1):
                break
            page += 1
        return None

    def fetch_messages(self, since: str) -> List[Dict[str, Any]]:
        """Fetch Fruugo messages since the given timestamp."""
        logger.info(f"Fetching Fruugo messages since {since}")
        result = self._api_request(
            "GET",
            "/messages",
            params={"fromDate": since},
        )
        messages: List[Dict[str, Any]] = []
        if result:
            logger.info(f"Fruugo messages fetched (placeholder)")
        return messages
