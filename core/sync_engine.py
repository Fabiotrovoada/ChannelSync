"""
VendStack Multi-Channel Sync Orchestrator
- Orchestrates order, listing, and inventory sync across all channels
- Handles scheduling and error tracking
"""

import json
import traceback
from datetime import datetime, timedelta


class SyncEngine:
    def __init__(self, db):
        self.db = db

    def get_adapter(self, channel_type):
        """Get the appropriate channel adapter."""
        from adapters import get_adapter
        return get_adapter(channel_type)

    def sync_channel(self, channel):
        """Sync a single channel: orders, listings, messages."""
        channel_id = channel['id']
        merchant_id = channel['merchant_id']
        channel_type = channel['channel_type']
        results = {'orders': 0, 'listings': 0, 'errors': []}

        try:
            adapter = self.get_adapter(channel_type)
            if not adapter:
                results['errors'].append(f'No adapter for {channel_type}')
                return results

            creds = json.loads(channel.get('credentials_json') or '{}')
            adapter.configure(creds)

            # Sync orders
            try:
                since = channel.get('last_sync_at') or (datetime.utcnow() - timedelta(days=30)).isoformat()
                orders = adapter.fetch_orders(since)
                for order in orders:
                    order['merchant_id'] = merchant_id
                    order['channel'] = channel_type
                    self._upsert_order(order)
                results['orders'] = len(orders)
            except Exception as e:
                results['errors'].append(f'Order sync error: {str(e)}')

            # Sync listings
            try:
                listings = adapter.fetch_listings()
                for listing in listings:
                    listing['merchant_id'] = merchant_id
                    listing['channel'] = channel_type
                    self._upsert_listing(listing)
                results['listings'] = len(listings)
            except Exception as e:
                results['errors'].append(f'Listing sync error: {str(e)}')

            # Update last sync time
            self.db.execute(
                'UPDATE channels SET last_sync_at = ?, error_log = ? WHERE id = ?',
                (datetime.utcnow().isoformat(), json.dumps(results['errors']) if results['errors'] else None, channel_id)
            )
            self.db.commit()

        except Exception as e:
            results['errors'].append(f'Sync failed: {str(e)}')
            self.db.execute(
                'UPDATE channels SET error_log = ? WHERE id = ?',
                (traceback.format_exc(), channel_id)
            )
            self.db.commit()

        return results

    def sync_all_channels(self, merchant_id):
        """Sync all active channels for a merchant."""
        channels = self.db.execute(
            'SELECT * FROM channels WHERE merchant_id = ? AND active = 1',
            (merchant_id,)
        ).fetchall()

        all_results = {}
        for ch in channels:
            channel = dict(ch)
            all_results[channel['display_name']] = self.sync_channel(channel)

        return all_results

    def push_tracking(self, order, tracking_number, carrier):
        """Push tracking info to the channel the order came from."""
        try:
            adapter = self.get_adapter(order['channel'])
            if adapter:
                adapter.push_tracking(
                    order.get('channel_order_id', ''),
                    tracking_number,
                    carrier
                )
                return True
        except Exception:
            pass
        return False

    def _upsert_order(self, order):
        """Insert or update an order by channel_order_id."""
        existing = self.db.execute(
            'SELECT id FROM orders WHERE channel_order_id = ? AND merchant_id = ?',
            (order.get('channel_order_id'), order['merchant_id'])
        ).fetchone()

        if existing:
            self.db.execute(
                'UPDATE orders SET status = ?, tracking_number = ?, shipped_at = ? WHERE id = ?',
                (order.get('status', 'pending'), order.get('tracking_number'), order.get('shipped_at'), existing['id'])
            )
        else:
            self.db.execute(
                '''INSERT INTO orders (merchant_id, channel, channel_order_id, order_number,
                   customer_name, customer_email, address, items_json, total, currency,
                   status, tracking_number, carrier, order_date)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (
                    order['merchant_id'], order['channel'], order.get('channel_order_id'),
                    order.get('order_number', ''), order.get('customer_name', ''),
                    order.get('customer_email'), order.get('address'),
                    json.dumps(order.get('items', [])), order.get('total', 0),
                    order.get('currency', 'GBP'), order.get('status', 'pending'),
                    order.get('tracking_number'), order.get('carrier'),
                    order.get('order_date'),
                )
            )
        self.db.commit()

    def _upsert_listing(self, listing):
        """Insert or update a listing by SKU + channel."""
        existing = self.db.execute(
            'SELECT id FROM listings WHERE sku = ? AND channel = ? AND merchant_id = ?',
            (listing.get('sku'), listing['channel'], listing['merchant_id'])
        ).fetchone()

        if existing:
            self.db.execute(
                'UPDATE listings SET title = ?, price = ?, quantity = ?, status = ? WHERE id = ?',
                (listing.get('title'), listing.get('price'), listing.get('quantity'), listing.get('status', 'active'), existing['id'])
            )
        else:
            self.db.execute(
                '''INSERT INTO listings (merchant_id, channel, sku, title, description, price, quantity, status, image_url)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (
                    listing['merchant_id'], listing['channel'], listing.get('sku', ''),
                    listing.get('title', ''), listing.get('description', ''),
                    listing.get('price', 0), listing.get('quantity', 0),
                    listing.get('status', 'active'), listing.get('image_url'),
                )
            )
        self.db.commit()
