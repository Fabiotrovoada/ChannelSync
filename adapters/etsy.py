"""Etsy API adapter."""

import json
import logging
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .base import ChannelAdapter

logger = logging.getLogger(__name__)


class EtsyAdapter(ChannelAdapter):
    """Etsy Marketplace API adapter using OAuth 2.0."""

    BASE_URL = "https://api.etsy.com/v3"
    TOKEN_URL = "https://api.etsy.com/v3/public/oauth/token"

    def __init__(self):
        self.client_id: Optional[str] = None
        self.client_secret: Optional[str] = None
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.shop_id: Optional[str] = None
        self._token_expiry: float = 0

    def configure(self, credentials: dict):
        """Store Etsy API credentials."""
        super().configure(credentials)
        self.client_id = credentials.get("client_id")
        self.client_secret = credentials.get("client_secret")
        self.access_token = credentials.get("access_token")
        self.refresh_token = credentials.get("refresh_token")
        self.shop_id = credentials.get("shop_id")
        logger.info(f"Etsy adapter configured for shop_id={self.shop_id}")

    def _is_token_expired(self) -> bool:
        """Check if the current access token is expired or about to expire."""
        return time.time() >= self._token_expiry - 60

    def _refresh_access_token(self) -> bool:
        """Refresh the OAuth access token using refresh_token."""
        if not self.refresh_token or not self.client_id or not self.client_secret:
            logger.error("Cannot refresh token: missing refresh_token or client credentials")
            return False

        logger.info("Refreshing Etsy OAuth token")
        data = urllib.parse.urlencode({
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "refresh_token": self.refresh_token,
        }).encode()

        req = urllib.request.Request(
            self.TOKEN_URL,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read())
                self.access_token = result.get("access_token")
                if "refresh_token" in result:
                    self.refresh_token = result.get("refresh_token")
                expires_in = result.get("expires_in", 3600)
                self._token_expiry = time.time() + expires_in
                logger.info("Etsy OAuth token refreshed successfully")
                return True
        except urllib.error.HTTPError as e:
            body = e.read().decode() if e.fp else ""
            logger.error(f"Etsy token refresh failed: {e.code} {body}")
            return False
        except Exception as e:
            logger.error(f"Etsy token refresh error: {e}")
            return False

    def _get_access_token(self) -> Optional[str]:
        """Get a valid access token, refreshing if necessary."""
        if self._is_token_expired():
            if not self._refresh_access_token():
                return None
        return self.access_token

    def _api_request(
        self, method: str, path: str, data: Optional[Dict] = None, params: Optional[Dict] = None
    ) -> Optional[Dict]:
        """Make an authenticated request to the Etsy API."""
        token = self._get_access_token()
        if not token:
            logger.error("No valid Etsy access token available")
            return None

        url = f"{self.BASE_URL}{path}"
        if params:
            qs = "&".join(f"{k}={v}" for k, v in params.items())
            url = f"{url}?{qs}"

        headers = {
            "Authorization": f"Bearer {token}",
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
            logger.error(f"Etsy API error {method} {path}: {e.code} {body}")
            return None
        except Exception as e:
            logger.error(f"Etsy API request error {method} {path}: {e}")
            return None

    def fetch_orders(self, since: str) -> List[Dict[str, Any]]:
        """Fetch orders since the given ISO timestamp."""
        logger.info(f"Fetching Etsy orders since {since}")
        if not self.shop_id:
            logger.error("shop_id not configured")
            return []

        all_orders: List[Dict[str, Any]] = []
        offset = 0
        limit = 50

        while True:
            result = self._api_request(
                "GET",
                f"/application/shops/{self.shop_id}/receipts",
                params={"offset": offset, "limit": limit, "created_after": since},
            )
            if result is None:
                break

            receipts = result.get("receipts", [])
            if not receipts:
                break

            for r in receipts:
                order = self._normalize_order(r)
                all_orders.append(order)

            if len(receipts) < limit:
                break
            offset += limit

        logger.info(f"Fetched {len(all_orders)} Etsy orders")
        return all_orders

    def _normalize_order(self, receipt: Dict) -> Dict[str, Any]:
        """Convert an Etsy receipt into a NormalizedOrder dict."""
        items = []
        for li in receipt.get("receipt_items", []):
            items.append({
                "sku": li.get("sku", ""),
                "title": li.get("title", ""),
                "quantity": li.get("quantity", 1),
                "price": float(li.get("price", 0)),
                "channel_listing_id": str(li.get("listing_id", "")),
            })

        customer = {
            "name": receipt.get("name", ""),
            "email": receipt.get("buyer_email", ""),
        }

        status_map = {
            "open": "pending",
            "paid": "paid",
            "shipped": "shipped",
            "completed": "delivered",
            "cancelled": "cancelled",
            "refunded": "refunded",
        }
        raw_status = receipt.get("status", "open")
        status = status_map.get(raw_status, raw_status)

        return {
            "channel": "etsy",
            "channel_order_id": str(receipt.get("receipt_id", "")),
            "order_number": str(receipt.get("receipt_id", "")),
            "order_date": receipt.get("creation_tsz", ""),
            "status": status,
            "customer": customer,
            "items": items,
            "total": float(receipt.get("total_taxable_price", 0)),
            "currency": receipt.get("currency", "USD"),
        }

    def push_tracking(self, order_id: str, tracking: str, carrier: str) -> bool:
        """Push tracking number to Etsy order."""
        logger.info(f"Pushing tracking {tracking} ({carrier}) to Etsy order {order_id}")
        if not self.shop_id:
            logger.error("shop_id not configured")
            return False

        payload = {
            "tracking_code": tracking,
            "carrier_name": carrier,
        }
        result = self._api_request(
            "POST",
            f"/application/shops/{self.shop_id}/receipts/{order_id}/tracking",
            data=payload,
        )
        if result is not None:
            logger.info(f"Tracking pushed to Etsy order {order_id}")
            return True
        logger.warning(f"Failed to push tracking to Etsy order {order_id}")
        return False

    def fetch_listings(self) -> List[Dict[str, Any]]:
        """Fetch all active Etsy listings."""
        logger.info("Fetching Etsy active listings")
        all_listings: List[Dict[str, Any]] = []
        offset = 0
        limit = 50

        while True:
            result = self._api_request(
                "GET",
                "/application/listings/active",
                params={"offset": offset, "limit": limit},
            )
            if result is None:
                break

            listings = result.get("results", [])
            if not listings:
                break

            for lst in listings:
                item = self._normalize_listing(lst)
                all_listings.append(item)

            if len(listings) < limit:
                break
            offset += limit

        logger.info(f"Fetched {len(all_listings)} Etsy listings")
        return all_listings

    def _normalize_listing(self, listing: Dict) -> Dict[str, Any]:
        """Convert an Etsy listing into a NormalizedListing dict."""
        images = listing.get("images", [])
        image_url = images[0].get("url_fullxfull", "") if images else ""

        return {
            "channel": "etsy",
            "sku": listing.get("sku", ""),
            "title": listing.get("title", ""),
            "description": listing.get("description", ""),
            "price": float(listing.get("price", {}).get("amount", 0)) / 100
                if isinstance(listing.get("price"), dict)
                else float(listing.get("price", 0)),
            "quantity": listing.get("quantity", 0),
            "status": "active" if listing.get("state") == "active" else "inactive",
            "image_url": image_url,
            "channel_url": listing.get("url", ""),
        }

    def create_listing(self, listing: Dict) -> Dict[str, Any]:
        """Create a new Etsy listing."""
        logger.info(f"Creating Etsy listing: {listing.get('title', 'unknown')}")
        payload = {
            "title": listing.get("title", ""),
            "description": listing.get("description", ""),
            "price": listing.get("price", 0),
            "quantity": listing.get("quantity", 1),
            "taxonomy_id": listing.get("taxonomy_id", 0),
            "shipping_profile_id": listing.get("shipping_profile_id"),
            "sku": listing.get("sku", ""),
        }
        result = self._api_request("POST", "/application/listings", data=payload)
        if result:
            logger.info(f"Etsy listing created: {result.get('listing_id')}")
            return self._normalize_listing(result)
        logger.error("Failed to create Etsy listing")
        return {}

    def update_listing(self, sku: str, changes: Dict) -> Dict[str, Any]:
        """Update an existing Etsy listing by SKU."""
        logger.info(f"Updating Etsy listing with SKU {sku}: {changes}")
        listing_id = self._find_listing_id_by_sku(sku)
        if not listing_id:
            logger.warning(f"No Etsy listing found for SKU {sku}")
            return {}

        path = f"/application/listings/{listing_id}"
        result = self._api_request("PUT", path, data=changes)
        if result:
            logger.info(f"Etsy listing {listing_id} updated")
            return self._normalize_listing(result)
        logger.error(f"Failed to update Etsy listing {listing_id}")
        return {}

    def _find_listing_id_by_sku(self, sku: str) -> Optional[str]:
        """Find Etsy listing ID by SKU."""
        offset = 0
        limit = 50
        while True:
            result = self._api_request(
                "GET",
                "/application/listings/active",
                params={"offset": offset, "limit": limit},
            )
            if not result:
                break
            for lst in result.get("results", []):
                if lst.get("sku") == sku:
                    return str(lst.get("listing_id"))
            if len(result.get("results", [])) < limit:
                break
            offset += limit
        return None

    def fetch_messages(self, since: str) -> List[Dict[str, Any]]:
        """Fetch Etsy buyer messages since the given timestamp."""
        logger.info(f"Fetching Etsy messages since {since}")
        if not self.shop_id:
            return []

        all_messages: List[Dict[str, Any]] = []
        offset = 0
        limit = 50

        while True:
            result = self._api_request(
                "GET",
                f"/application/shops/{self.shop_id}/messages",
                params={"offset": offset, "limit": limit, "created_after": since},
            )
            if result is None:
                break

            messages = result.get("results", [])
            if not messages:
                break

            for msg in messages:
                all_messages.append({
                    "channel": "etsy",
                    "message_id": str(msg.get("message_id", "")),
                    "order_id": str(msg.get("receipt_id", "")),
                    "subject": msg.get("subject", ""),
                    "body": msg.get("body", ""),
                    "from_id": str(msg.get("from_user_id", "")),
                    "to_id": str(msg.get("to_user_id", "")),
                    "created_at": msg.get("creation_tsz", ""),
                    "is_read": msg.get("is_read", False),
                })

            if len(messages) < limit:
                break
            offset += limit

        logger.info(f"Fetched {len(all_messages)} Etsy messages")
        return all_messages
