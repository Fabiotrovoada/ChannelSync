"""BigCommerce API adapter."""

import json
import logging
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

from .base import ChannelAdapter

logger = logging.getLogger(__name__)


class BigCommerceAdapter(ChannelAdapter):
    """BigCommerce API adapter using X-Auth-Token authentication."""

    def __init__(self):
        self.store_hash: Optional[str] = None
        self.access_token: Optional[str] = None
        self.base_url: str = "https://api.bigcommerce.com"

    def configure(self, credentials: dict):
        """Store BigCommerce API credentials."""
        super().configure(credentials)
        self.store_hash = credentials.get("store_hash")
        self.access_token = credentials.get("access_token")
        self.base_url = credentials.get("base_url", "https://api.bigcommerce.com")
        logger.info(f"BigCommerce adapter configured for store_hash={self.store_hash}")

    def _api_url(self, path: str) -> str:
        """Build a full BigCommerce API URL."""
        return f"{self.base_url}/stores/{self.store_hash}/v3{path}"

    def _api_request(
        self,
        method: str,
        path: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
    ) -> Optional[Dict]:
        """Make an authenticated request to the BigCommerce API."""
        url = self._api_url(path)
        if params:
            qs = "&".join(f"{k}={v}" for k, v in params.items())
            url = f"{url}?{qs}"

        headers = {
            "X-Auth-Token": self.access_token or "",
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
            logger.error(f"BigCommerce API error {method} {path}: {e.code} {body}")
            return None
        except Exception as e:
            logger.error(f"BigCommerce API request error {method} {path}: {e}")
            return None

    def fetch_orders(self, since: str) -> List[Dict[str, Any]]:
        """Fetch BigCommerce orders since the given ISO timestamp."""
        logger.info(f"Fetching BigCommerce orders since {since}")
        all_orders: List[Dict[str, Any]] = []
        page = 1
        per_page = 50

        while True:
            result = self._api_request(
                "GET",
                "/orders",
                params={
                    "page": page,
                    "limit": per_page,
                    "min_date_created": since,
                    "include": "items,customers",
                },
            )
            if result is None:
                break

            orders = result.get("data", [])
            if not orders:
                break

            for o in orders:
                order = self._normalize_order(o)
                all_orders.append(order)

            meta = result.get("meta", {})
            if page >= meta.get("pagination", {}).get("total_pages", 1):
                break
            page += 1

        logger.info(f"Fetched {len(all_orders)} BigCommerce orders")
        return all_orders

    def _normalize_order(self, order: Dict) -> Dict[str, Any]:
        """Convert a BigCommerce order into a NormalizedOrder dict."""
        items = []
        for li in order.get("items", []).get("data", []):
            items.append({
                "sku": li.get("sku", ""),
                "title": li.get("name", ""),
                "quantity": li.get("quantity", 1),
                "price": float(li.get("price_inc_tax", 0)),
                "channel_listing_id": str(li.get("product_id", "")),
            })

        customers = order.get("items", {}).get("customers", {}).get("data", [])
        customer_data = customers[0] if customers else {}
        customer = {
            "name": customer_data.get("first_name", "") + " " + customer_data.get("last_name", ""),
            "email": customer_data.get("email", ""),
        }

        status_map = {
            "pending": "pending",
            "incomplete": "pending",
            "paid": "paid",
            "partially_shipped": "shipped",
            "shipped": "shipped",
            "delivered": "delivered",
            "cancelled": "cancelled",
            "refunded": "refunded",
            "declined": "cancelled",
        }
        raw_status = order.get("status", "pending")
        status = status_map.get(raw_status, raw_status.lower())

        return {
            "channel": "bigcommerce",
            "channel_order_id": str(order.get("id", "")),
            "order_number": str(order.get("order_number", "")),
            "order_date": order.get("date_created", ""),
            "status": status,
            "customer": customer,
            "items": items,
            "total": float(order.get("total_inc_tax", 0)),
            "currency": order.get("currency_code", "USD"),
        }

    def push_tracking(self, order_id: str, tracking: str, carrier: str) -> bool:
        """Push tracking number to BigCommerce order."""
        logger.info(f"Pushing tracking {tracking} ({carrier}) to BigCommerce order {order_id}")
        payload = {
            "order_id": int(order_id),
            "tracking_number": tracking,
            "shipping_method": carrier,
        }
        result = self._api_request("POST", "/orders/{}".format(order_id), data=payload)
        if result is not None:
            logger.info(f"Tracking pushed to BigCommerce order {order_id}")
            return True
        logger.warning(f"Failed to push tracking to BigCommerce order {order_id}")
        return False

    def fetch_listings(self) -> List[Dict[str, Any]]:
        """Fetch all BigCommerce product listings."""
        logger.info("Fetching BigCommerce listings")
        all_listings: List[Dict[str, Any]] = []
        page = 1
        per_page = 50

        while True:
            result = self._api_request(
                "GET",
                "/catalog/products",
                params={"page": page, "limit": per_page},
            )
            if result is None:
                break

            products = result.get("data", [])
            if not products:
                break

            for p in products:
                listing = self._normalize_listing(p)
                all_listings.append(listing)

            meta = result.get("meta", {})
            if page >= meta.get("pagination", {}).get("total_pages", 1):
                break
            page += 1

        logger.info(f"Fetched {len(all_listings)} BigCommerce listings")
        return all_listings

    def _normalize_listing(self, product: Dict) -> Dict[str, Any]:
        """Convert a BigCommerce product into a NormalizedListing dict."""
        images = product.get("images", {}).get("data", [])
        image_url = images[0].get("url_thumbnail", "") if images else ""

        return {
            "channel": "bigcommerce",
            "sku": product.get("sku", ""),
            "title": product.get("name", ""),
            "description": product.get("description", ""),
            "price": float(product.get("price", 0)),
            "quantity": product.get("inventory_level", 0),
            "status": "active" if product.get("is_visible", True) else "inactive",
            "image_url": image_url,
            "channel_url": product.get("custom_url", {}).get("url", ""),
        }

    def create_listing(self, listing: Dict) -> Dict[str, Any]:
        """Create a new BigCommerce product listing."""
        logger.info(f"Creating BigCommerce listing: {listing.get('title', 'unknown')}")
        payload = {
            "name": listing.get("title", ""),
            "type": "physical",
            "sku": listing.get("sku", ""),
            "description": listing.get("description", ""),
            "price": listing.get("price", 0),
            "inventory_level": listing.get("quantity", 0),
            "categories": listing.get("category_ids", []),
        }
        result = self._api_request("POST", "/catalog/products", data=payload)
        if result:
            pid = result.get("id", 0)
            logger.info(f"BigCommerce listing created: id={pid}")
            return self._normalize_listing(result)
        logger.error("Failed to create BigCommerce listing")
        return {}

    def update_listing(self, sku: str, changes: Dict) -> Dict[str, Any]:
        """Update an existing BigCommerce product by SKU."""
        logger.info(f"Updating BigCommerce listing SKU {sku}: {changes}")
        product_id = self._find_product_id_by_sku(sku)
        if not product_id:
            logger.warning(f"No BigCommerce product found for SKU {sku}")
            return {}

        result = self._api_request("PUT", f"/catalog/products/{product_id}", data=changes)
        if result:
            logger.info(f"BigCommerce listing {product_id} updated")
            return self._normalize_listing(result)
        logger.error(f"Failed to update BigCommerce listing {product_id}")
        return {}

    def _find_product_id_by_sku(self, sku: str) -> Optional[int]:
        """Find BigCommerce product ID by SKU."""
        page = 1
        per_page = 50
        while True:
            result = self._api_request(
                "GET",
                "/catalog/products",
                params={"page": page, "limit": per_page, "sku": sku},
            )
            if not result:
                break
            products = result.get("data", [])
            if products:
                return products[0].get("id")
            meta = result.get("meta", {})
            if page >= meta.get("pagination", {}).get("total_pages", 1):
                break
            page += 1
        return None

    def fetch_messages(self, since: str) -> List[Dict[str, Any]]:
        """Fetch BigCommerce customer messages since the given timestamp."""
        logger.info(f"Fetching BigCommerce messages since {since}")
        all_messages: List[Dict[str, Any]] = []
        page = 1
        per_page = 50

        while True:
            result = self._api_request(
                "GET",
                "/order_messages",
                params={"page": page, "limit": per_page, "min_date_created": since},
            )
            if result is None:
                break

            messages = result.get("data", [])
            if not messages:
                break

            for msg in messages:
                all_messages.append({
                    "channel": "bigcommerce",
                    "message_id": str(msg.get("id", "")),
                    "order_id": str(msg.get("order_id", "")),
                    "subject": msg.get("subject", ""),
                    "body": msg.get("message", ""),
                    "from_email": msg.get("from_email", ""),
                    "created_at": msg.get("date_created", ""),
                    "is_read": msg.get("is_read", False),
                })

            meta = result.get("meta", {})
            if page >= meta.get("pagination", {}).get("total_pages", 1):
                break
            page += 1

        logger.info(f"Fetched {len(all_messages)} BigCommerce messages")
        return all_messages
