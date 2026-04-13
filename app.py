"""
VendStack — Full Flask Backend
All API routes, auth, DB init, demo seeding
"""

import os
import json
import hashlib
import sqlite3
from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, request, jsonify, session, g, send_file
from flask_cors import CORS

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'vendstack-dev-secret-key-change-in-prod')
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

CORS(app, supports_credentials=True, origins=[
    'http://localhost:5173',
    'http://127.0.0.1:5173',
])

DATABASE = os.environ.get('DATABASE_PATH', 'vendstack.db')


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA journal_mode=WAL')
        g.db.execute('PRAGMA foreign_keys=ON')
    return g.db


@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    with open('db/schema.sql', 'r') as f:
        db.executescript(f.read())
    db.commit()
    return db


def dict_row(row):
    if row is None:
        return None
    return dict(row)


def dict_rows(rows):
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'merchant_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated


def current_merchant_id():
    return session.get('merchant_id')


def audit(action, details=None):
    mid = current_merchant_id()
    if mid:
        db = get_db()
        db.execute(
            'INSERT INTO audit_log (merchant_id, action, details_json) VALUES (?, ?, ?)',
            (mid, action, json.dumps(details) if details else None)
        )
        db.commit()


# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------

@app.route('/api/auth/login', methods=['POST'])
def auth_login():
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400

    db = get_db()
    merchant = dict_row(db.execute(
        'SELECT * FROM merchants WHERE email = ?', (email,)
    ).fetchone())

    if not merchant or merchant['password_hash'] != hash_password(password):
        return jsonify({'error': 'Invalid credentials'}), 401

    session['merchant_id'] = merchant['id']
    audit('login')

    return jsonify({
        'id': merchant['id'],
        'email': merchant['email'],
        'business_name': merchant['business_name'],
        'plan': merchant['plan'],
    })


@app.route('/api/auth/register', methods=['POST'])
def auth_register():
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    business_name = data.get('business_name', '').strip()
    plan = data.get('plan', 'starter')

    if not email or not password or not business_name:
        return jsonify({'error': 'All fields required'}), 400

    db = get_db()
    existing = db.execute('SELECT id FROM merchants WHERE email = ?', (email,)).fetchone()
    if existing:
        return jsonify({'error': 'Email already registered'}), 409

    db.execute(
        'INSERT INTO merchants (business_name, email, password_hash, plan) VALUES (?, ?, ?, ?)',
        (business_name, email, hash_password(password), plan)
    )
    db.commit()

    merchant = dict_row(db.execute('SELECT * FROM merchants WHERE email = ?', (email,)).fetchone())
    session['merchant_id'] = merchant['id']

    return jsonify({
        'id': merchant['id'],
        'email': merchant['email'],
        'business_name': merchant['business_name'],
        'plan': merchant['plan'],
    }), 201


@app.route('/api/auth/logout', methods=['POST'])
def auth_logout():
    audit('logout')
    session.clear()
    return jsonify({'ok': True})


@app.route('/api/auth/me', methods=['GET'])
@login_required
def auth_me():
    db = get_db()
    merchant = dict_row(db.execute(
        'SELECT id, email, business_name, plan, reply_tone, auto_reply_enabled, low_stock_threshold FROM merchants WHERE id = ?',
        (current_merchant_id(),)
    ).fetchone())
    return jsonify(merchant)


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@app.route('/api/dashboard/stats', methods=['GET'])
@login_required
def dashboard_stats():
    db = get_db()
    mid = current_merchant_id()

    total_orders = db.execute('SELECT COUNT(*) as c FROM orders WHERE merchant_id = ?', (mid,)).fetchone()['c']
    revenue = db.execute("SELECT COALESCE(SUM(total), 0) as s FROM orders WHERE merchant_id = ? AND status = 'shipped'", (mid,)).fetchone()['s']
    awaiting = db.execute("SELECT COUNT(*) as c FROM orders WHERE merchant_id = ? AND status = 'pending'", (mid,)).fetchone()['c']
    shipped_week = db.execute(
        "SELECT COUNT(*) as c FROM orders WHERE merchant_id = ? AND status = 'shipped' AND shipped_at >= ?",
        (mid, (datetime.utcnow() - timedelta(days=7)).isoformat())
    ).fetchone()['c']
    open_messages = db.execute("SELECT COUNT(*) as c FROM messages WHERE merchant_id = ? AND status = 'open'", (mid,)).fetchone()['c']
    active_channels = db.execute("SELECT COUNT(*) as c FROM channels WHERE merchant_id = ? AND active = 1", (mid,)).fetchone()['c']

    recent_orders = dict_rows(db.execute(
        'SELECT * FROM orders WHERE merchant_id = ? ORDER BY created_at DESC LIMIT 10', (mid,)
    ).fetchall())

    recent_messages = dict_rows(db.execute(
        "SELECT * FROM messages WHERE merchant_id = ? AND status = 'open' ORDER BY created_at DESC LIMIT 5", (mid,)
    ).fetchall())

    channels = dict_rows(db.execute(
        'SELECT id, channel_type, display_name, active, last_sync_at, error_log FROM channels WHERE merchant_id = ?', (mid,)
    ).fetchall())

    return jsonify({
        'total_orders': total_orders,
        'revenue': round(revenue, 2),
        'awaiting_shipment': awaiting,
        'shipped_this_week': shipped_week,
        'open_messages': open_messages,
        'active_channels': active_channels,
        'recent_orders': recent_orders,
        'recent_messages': recent_messages,
        'channels': channels,
    })


# ---------------------------------------------------------------------------
# Orders
# ---------------------------------------------------------------------------

@app.route('/api/orders', methods=['GET'])
@login_required
def orders_list():
    db = get_db()
    mid = current_merchant_id()
    channel = request.args.get('channel')
    status = request.args.get('status')
    search = request.args.get('search', '')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 25))
    offset = (page - 1) * per_page

    query = 'SELECT * FROM orders WHERE merchant_id = ?'
    params = [mid]

    if channel:
        query += ' AND channel = ?'
        params.append(channel)
    if status:
        query += ' AND status = ?'
        params.append(status)
    if search:
        query += ' AND (order_number LIKE ? OR customer_name LIKE ? OR customer_email LIKE ?)'
        s = f'%{search}%'
        params.extend([s, s, s])

    count_query = query.replace('SELECT *', 'SELECT COUNT(*) as c')
    total = db.execute(count_query, params).fetchone()['c']

    query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
    params.extend([per_page, offset])

    orders = dict_rows(db.execute(query, params).fetchall())

    return jsonify({
        'orders': orders,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page,
    })


@app.route('/api/orders/<int:order_id>', methods=['GET'])
@login_required
def order_detail(order_id):
    db = get_db()
    order = dict_row(db.execute(
        'SELECT * FROM orders WHERE id = ? AND merchant_id = ?',
        (order_id, current_merchant_id())
    ).fetchone())
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    return jsonify(order)


@app.route('/api/orders/<int:order_id>', methods=['PATCH'])
@login_required
def order_update(order_id):
    db = get_db()
    mid = current_merchant_id()
    data = request.get_json() or {}

    order = db.execute('SELECT * FROM orders WHERE id = ? AND merchant_id = ?', (order_id, mid)).fetchone()
    if not order:
        return jsonify({'error': 'Order not found'}), 404

    updates = []
    params = []

    if 'status' in data:
        updates.append('status = ?')
        params.append(data['status'])
        if data['status'] == 'shipped':
            updates.append('shipped_at = ?')
            params.append(datetime.utcnow().isoformat())

    if 'tracking_number' in data:
        updates.append('tracking_number = ?')
        params.append(data['tracking_number'])

    if 'carrier' in data:
        updates.append('carrier = ?')
        params.append(data['carrier'])

    if updates:
        query = f"UPDATE orders SET {', '.join(updates)} WHERE id = ? AND merchant_id = ?"
        params.extend([order_id, mid])
        db.execute(query, params)
        db.commit()
        audit('order_update', {'order_id': order_id, 'changes': data})

    updated = dict_row(db.execute('SELECT * FROM orders WHERE id = ?', (order_id,)).fetchone())
    return jsonify(updated)


@app.route('/api/orders/sync', methods=['POST'])
@login_required
def orders_sync():
    from core.sync_engine import SyncEngine
    engine = SyncEngine(get_db())
    results = engine.sync_all_channels(current_merchant_id())
    audit('order_sync', results)
    return jsonify({'results': results})


@app.route('/api/orders/<int:order_id>/ship', methods=['POST'])
@login_required
def order_ship(order_id):
    db = get_db()
    mid = current_merchant_id()
    data = request.get_json() or {}

    order = dict_row(db.execute(
        'SELECT * FROM orders WHERE id = ? AND merchant_id = ?', (order_id, mid)
    ).fetchone())
    if not order:
        return jsonify({'error': 'Order not found'}), 404

    carrier = data.get('carrier', '')
    tracking = data.get('tracking_number', '')

    db.execute(
        'UPDATE orders SET status = ?, carrier = ?, tracking_number = ?, shipped_at = ? WHERE id = ?',
        ('shipped', carrier, tracking, datetime.utcnow().isoformat(), order_id)
    )
    db.commit()

    # Push tracking to channel
    from core.sync_engine import SyncEngine
    engine = SyncEngine(db)
    engine.push_tracking(order, tracking, carrier)

    audit('order_shipped', {'order_id': order_id, 'carrier': carrier, 'tracking': tracking})

    updated = dict_row(db.execute('SELECT * FROM orders WHERE id = ?', (order_id,)).fetchone())
    return jsonify(updated)


# ---------------------------------------------------------------------------
# Messages
# ---------------------------------------------------------------------------

@app.route('/api/messages', methods=['GET'])
@login_required
def messages_list():
    db = get_db()
    mid = current_merchant_id()
    status = request.args.get('status', 'open')

    query = 'SELECT * FROM messages WHERE merchant_id = ?'
    params = [mid]

    if status:
        query += ' AND status = ?'
        params.append(status)

    query += ' ORDER BY created_at DESC'
    messages = dict_rows(db.execute(query, params).fetchall())
    return jsonify({'messages': messages})


@app.route('/api/messages/<int:message_id>', methods=['GET'])
@login_required
def message_detail(message_id):
    db = get_db()
    msg = dict_row(db.execute(
        'SELECT * FROM messages WHERE id = ? AND merchant_id = ?',
        (message_id, current_merchant_id())
    ).fetchone())
    if not msg:
        return jsonify({'error': 'Message not found'}), 404
    return jsonify(msg)


@app.route('/api/messages/<int:message_id>/reply', methods=['POST'])
@login_required
def message_reply(message_id):
    db = get_db()
    mid = current_merchant_id()
    data = request.get_json() or {}
    reply = data.get('reply', '').strip()

    if not reply:
        return jsonify({'error': 'Reply text required'}), 400

    msg = db.execute('SELECT * FROM messages WHERE id = ? AND merchant_id = ?', (message_id, mid)).fetchone()
    if not msg:
        return jsonify({'error': 'Message not found'}), 404

    db.execute(
        'UPDATE messages SET ai_reply = ?, status = ?, replied_at = ? WHERE id = ?',
        (reply, 'resolved', datetime.utcnow().isoformat(), message_id)
    )
    db.commit()
    audit('message_reply', {'message_id': message_id})

    updated = dict_row(db.execute('SELECT * FROM messages WHERE id = ?', (message_id,)).fetchone())
    return jsonify(updated)


@app.route('/api/messages/<int:message_id>/ai-reply', methods=['POST'])
@login_required
def message_ai_reply(message_id):
    db = get_db()
    mid = current_merchant_id()

    msg = dict_row(db.execute(
        'SELECT * FROM messages WHERE id = ? AND merchant_id = ?', (message_id, mid)
    ).fetchone())
    if not msg:
        return jsonify({'error': 'Message not found'}), 404

    merchant = dict_row(db.execute('SELECT * FROM merchants WHERE id = ?', (mid,)).fetchone())

    # Build context from related order if available
    context = {
        'customer_name': msg.get('customer_name', 'Customer'),
    }

    if msg.get('order_id'):
        order = dict_row(db.execute('SELECT * FROM orders WHERE id = ?', (msg['order_id'],)).fetchone())
        if order:
            context.update({
                'order_number': order['order_number'],
                'status': order['status'],
                'tracking_number': order.get('tracking_number'),
                'total': f"£{order['total']:.2f}",
            })

    from core.ai_engine import generate_reply
    result = generate_reply(
        msg['body'],
        tone=merchant.get('reply_tone', 'professional'),
        context=context,
        api_key=merchant.get('openai_api_key'),
    )

    # Save the AI reply
    db.execute(
        'UPDATE messages SET ai_reply = ?, intent = ?, sentiment = ? WHERE id = ?',
        (result['reply'], result['intent'], result['sentiment'], message_id)
    )
    db.commit()
    audit('ai_reply_generated', {'message_id': message_id, 'source': result['source']})

    return jsonify(result)


@app.route('/api/messages/ai-compose', methods=['POST'])
@login_required
def messages_ai_compose():
    data = request.get_json() or {}
    context_text = data.get('context', '')
    tone = data.get('tone', 'professional')

    db = get_db()
    merchant = dict_row(db.execute('SELECT * FROM merchants WHERE id = ?', (current_merchant_id(),)).fetchone())

    from core.ai_engine import compose_message
    reply = compose_message(
        context_text,
        tone=tone,
        api_key=merchant.get('openai_api_key'),
    )

    return jsonify({'reply': reply, 'tone': tone})


# ---------------------------------------------------------------------------
# Channels
# ---------------------------------------------------------------------------

@app.route('/api/channels', methods=['GET'])
@login_required
def channels_list():
    db = get_db()
    channels = dict_rows(db.execute(
        'SELECT id, merchant_id, channel_type, display_name, active, last_sync_at, error_log, created_at FROM channels WHERE merchant_id = ?',
        (current_merchant_id(),)
    ).fetchall())
    return jsonify({'channels': channels})


@app.route('/api/channels', methods=['POST'])
@login_required
def channels_create():
    db = get_db()
    data = request.get_json() or {}

    db.execute(
        'INSERT INTO channels (merchant_id, channel_type, display_name, credentials_json) VALUES (?, ?, ?, ?)',
        (current_merchant_id(), data.get('channel_type', ''), data.get('display_name', ''), json.dumps(data.get('credentials', {})))
    )
    db.commit()
    audit('channel_created', {'type': data.get('channel_type')})

    channel = dict_row(db.execute('SELECT * FROM channels WHERE merchant_id = ? ORDER BY id DESC LIMIT 1', (current_merchant_id(),)).fetchone())
    return jsonify(channel), 201


@app.route('/api/channels/<int:channel_id>', methods=['PATCH'])
@login_required
def channels_update(channel_id):
    db = get_db()
    data = request.get_json() or {}

    ch = db.execute('SELECT * FROM channels WHERE id = ? AND merchant_id = ?', (channel_id, current_merchant_id())).fetchone()
    if not ch:
        return jsonify({'error': 'Channel not found'}), 404

    updates, params = [], []
    for field in ['display_name', 'active']:
        if field in data:
            updates.append(f'{field} = ?')
            params.append(data[field])

    if 'credentials' in data:
        updates.append('credentials_json = ?')
        params.append(json.dumps(data['credentials']))

    if updates:
        params.extend([channel_id, current_merchant_id()])
        db.execute(f"UPDATE channels SET {', '.join(updates)} WHERE id = ? AND merchant_id = ?", params)
        db.commit()

    updated = dict_row(db.execute('SELECT * FROM channels WHERE id = ?', (channel_id,)).fetchone())
    return jsonify(updated)


@app.route('/api/channels/<int:channel_id>', methods=['DELETE'])
@login_required
def channels_delete(channel_id):
    db = get_db()
    ch = db.execute('SELECT * FROM channels WHERE id = ? AND merchant_id = ?', (channel_id, current_merchant_id())).fetchone()
    if not ch:
        return jsonify({'error': 'Channel not found'}), 404

    db.execute('DELETE FROM channels WHERE id = ? AND merchant_id = ?', (channel_id, current_merchant_id()))
    db.commit()
    audit('channel_deleted', {'channel_id': channel_id})
    return jsonify({'ok': True})


@app.route('/api/channels/<int:channel_id>/sync', methods=['POST'])
@login_required
def channels_sync(channel_id):
    db = get_db()
    ch = dict_row(db.execute(
        'SELECT * FROM channels WHERE id = ? AND merchant_id = ?',
        (channel_id, current_merchant_id())
    ).fetchone())
    if not ch:
        return jsonify({'error': 'Channel not found'}), 404

    from core.sync_engine import SyncEngine
    engine = SyncEngine(db)
    result = engine.sync_channel(ch)
    audit('channel_sync', {'channel_id': channel_id, 'result': result})
    return jsonify(result)


@app.route('/api/channels/<int:channel_id>/toggle', methods=['POST'])
@login_required
def channels_toggle(channel_id):
    data = request.json or {}
    db = get_db()
    db.execute(
        'UPDATE channels SET active = ? WHERE id = ? AND merchant_id = ?',
        (1 if data.get('active', True) else 0, channel_id, current_merchant_id())
    )
    db.commit()
    return jsonify({'ok': True})


# ---------------------------------------------------------------------------
# Listings
# ---------------------------------------------------------------------------

@app.route('/api/listings', methods=['GET'])
@login_required
def listings_list():
    db = get_db()
    mid = current_merchant_id()
    channel = request.args.get('channel')
    search = request.args.get('search', '')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 25))
    offset = (page - 1) * per_page

    query = 'SELECT * FROM listings WHERE merchant_id = ?'
    params = [mid]

    if channel:
        query += ' AND channel = ?'
        params.append(channel)
    if search:
        query += ' AND (title LIKE ? OR sku LIKE ?)'
        s = f'%{search}%'
        params.extend([s, s])

    count_query = query.replace('SELECT *', 'SELECT COUNT(*) as c')
    total = db.execute(count_query, params).fetchone()['c']

    query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
    params.extend([per_page, offset])

    listings = dict_rows(db.execute(query, params).fetchall())

    return jsonify({
        'listings': listings,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page,
    })


@app.route('/api/listings/<int:listing_id>', methods=['PATCH'])
@login_required
def listings_update(listing_id):
    db = get_db()
    mid = current_merchant_id()
    data = request.get_json() or {}

    listing = db.execute('SELECT * FROM listings WHERE id = ? AND merchant_id = ?', (listing_id, mid)).fetchone()
    if not listing:
        return jsonify({'error': 'Listing not found'}), 404

    updates, params = [], []
    for field in ['title', 'description', 'price', 'quantity', 'status']:
        if field in data:
            updates.append(f'{field} = ?')
            params.append(data[field])

    if updates:
        params.extend([listing_id, mid])
        db.execute(f"UPDATE listings SET {', '.join(updates)} WHERE id = ? AND merchant_id = ?", params)
        db.commit()
        audit('listing_updated', {'listing_id': listing_id, 'changes': data})

    updated = dict_row(db.execute('SELECT * FROM listings WHERE id = ?', (listing_id,)).fetchone())
    return jsonify(updated)


@app.route('/api/listings/bulk-update', methods=['POST'])
@login_required
def listings_bulk_update():
    db = get_db()
    mid = current_merchant_id()
    data = request.get_json() or {}
    ids = data.get('ids', [])
    changes = data.get('changes', {})

    if not ids or not changes:
        return jsonify({'error': 'ids and changes required'}), 400

    updates, params_template = [], []
    for field in ['price', 'quantity']:
        if field in changes:
            updates.append(f'{field} = ?')
            params_template.append(changes[field])

    if updates:
        for lid in ids:
            params = params_template + [lid, mid]
            db.execute(f"UPDATE listings SET {', '.join(updates)} WHERE id = ? AND merchant_id = ?", params)
        db.commit()
        audit('listings_bulk_update', {'ids': ids, 'changes': changes})

    return jsonify({'updated': len(ids)})


# ---------------------------------------------------------------------------
# Inventory
# ---------------------------------------------------------------------------

@app.route('/api/inventory', methods=['GET'])
@login_required
def inventory_list():
    db = get_db()
    mid = current_merchant_id()
    inventory = dict_rows(db.execute(
        'SELECT * FROM inventory WHERE merchant_id = ? ORDER BY sku', (mid,)
    ).fetchall())

    # Get low stock threshold
    merchant = dict_row(db.execute('SELECT low_stock_threshold FROM merchants WHERE id = ?', (mid,)).fetchone())
    threshold = merchant.get('low_stock_threshold', 10) if merchant else 10

    for item in inventory:
        item['low_stock'] = item['available_qty'] < threshold

    return jsonify({'inventory': inventory, 'low_stock_threshold': threshold})


@app.route('/api/inventory/<string:sku>', methods=['PATCH'])
@login_required
def inventory_update(sku):
    db = get_db()
    mid = current_merchant_id()
    data = request.get_json() or {}
    delta = data.get('quantity_delta', 0)
    reason = data.get('reason', '')

    inv = db.execute('SELECT * FROM inventory WHERE sku = ? AND merchant_id = ?', (sku, mid)).fetchone()
    if not inv:
        return jsonify({'error': 'SKU not found'}), 404

    new_warehouse = inv['warehouse_qty'] + delta
    new_available = new_warehouse - inv['reserved_qty']

    db.execute(
        'UPDATE inventory SET warehouse_qty = ?, available_qty = ?, last_updated = ? WHERE sku = ? AND merchant_id = ?',
        (new_warehouse, max(new_available, 0), datetime.utcnow().isoformat(), sku, mid)
    )
    db.commit()
    audit('inventory_adjusted', {'sku': sku, 'delta': delta, 'reason': reason})

    updated = dict_row(db.execute('SELECT * FROM inventory WHERE sku = ? AND merchant_id = ?', (sku, mid)).fetchone())
    return jsonify(updated)


# ---------------------------------------------------------------------------
# Purchase Orders
# ---------------------------------------------------------------------------

@app.route('/api/purchase-orders', methods=['GET'])
@login_required
def po_list():
    db = get_db()
    pos = dict_rows(db.execute(
        'SELECT * FROM purchase_orders WHERE merchant_id = ? ORDER BY created_at DESC',
        (current_merchant_id(),)
    ).fetchall())
    return jsonify({'purchase_orders': pos})


@app.route('/api/purchase-orders', methods=['POST'])
@login_required
def po_create():
    db = get_db()
    data = request.get_json() or {}

    db.execute(
        'INSERT INTO purchase_orders (merchant_id, vendor_name, status, items_json, total_cost) VALUES (?, ?, ?, ?, ?)',
        (current_merchant_id(), data.get('vendor_name', ''), data.get('status', 'draft'),
         json.dumps(data.get('items', [])), data.get('total_cost', 0))
    )
    db.commit()
    audit('po_created', {'vendor': data.get('vendor_name')})

    po = dict_row(db.execute(
        'SELECT * FROM purchase_orders WHERE merchant_id = ? ORDER BY id DESC LIMIT 1',
        (current_merchant_id(),)
    ).fetchone())
    return jsonify(po), 201


@app.route('/api/purchase-orders/<int:po_id>', methods=['PATCH'])
@login_required
def po_update(po_id):
    db = get_db()
    mid = current_merchant_id()
    data = request.get_json() or {}

    po = db.execute('SELECT * FROM purchase_orders WHERE id = ? AND merchant_id = ?', (po_id, mid)).fetchone()
    if not po:
        return jsonify({'error': 'PO not found'}), 404

    updates, params = [], []
    if 'status' in data:
        updates.append('status = ?')
        params.append(data['status'])
    if 'items' in data:
        updates.append('items_json = ?')
        params.append(json.dumps(data['items']))
    if 'total_cost' in data:
        updates.append('total_cost = ?')
        params.append(data['total_cost'])

    if updates:
        params.extend([po_id, mid])
        db.execute(f"UPDATE purchase_orders SET {', '.join(updates)} WHERE id = ? AND merchant_id = ?", params)
        db.commit()

    updated = dict_row(db.execute('SELECT * FROM purchase_orders WHERE id = ?', (po_id,)).fetchone())
    return jsonify(updated)


@app.route('/api/purchase-orders/<int:po_id>/receive', methods=['POST'])
@login_required
def po_receive(po_id):
    db = get_db()
    mid = current_merchant_id()
    data = request.get_json() or {}

    po = db.execute('SELECT * FROM purchase_orders WHERE id = ? AND merchant_id = ?', (po_id, mid)).fetchone()
    if not po:
        return jsonify({'error': 'PO not found'}), 404

    items = data.get('items', [])
    for item in items:
        sku = item.get('sku')
        qty = item.get('qty_received', 0)

        inv = db.execute('SELECT * FROM inventory WHERE sku = ? AND merchant_id = ?', (sku, mid)).fetchone()
        if inv:
            new_warehouse = inv['warehouse_qty'] + qty
            new_available = new_warehouse - inv['reserved_qty']
            db.execute(
                'UPDATE inventory SET warehouse_qty = ?, available_qty = ?, last_updated = ? WHERE sku = ? AND merchant_id = ?',
                (new_warehouse, max(new_available, 0), datetime.utcnow().isoformat(), sku, mid)
            )

    db.execute(
        'UPDATE purchase_orders SET status = ?, received_at = ? WHERE id = ?',
        ('received', datetime.utcnow().isoformat(), po_id)
    )
    db.commit()
    audit('po_received', {'po_id': po_id, 'items': items})

    updated = dict_row(db.execute('SELECT * FROM purchase_orders WHERE id = ?', (po_id,)).fetchone())
    return jsonify(updated)


# ---------------------------------------------------------------------------
# Shipping (ShipStation)
# ---------------------------------------------------------------------------

@app.route('/api/shipping/rates', methods=['GET'])
@login_required
def shipping_rates():
    db = get_db()
    mid = current_merchant_id()
    order_id = request.args.get('order_id')

    if not order_id:
        return jsonify({'error': 'order_id required'}), 400

    order = dict_row(db.execute(
        'SELECT * FROM orders WHERE id = ? AND merchant_id = ?', (order_id, mid)
    ).fetchone())
    if not order:
        return jsonify({'error': 'Order not found'}), 404

    merchant = dict_row(db.execute('SELECT * FROM merchants WHERE id = ?', (mid,)).fetchone())

    from core.shipstation import ShipStationClient, DEMO_RATES

    if merchant.get('shipstation_api_key') and merchant.get('shipstation_api_secret'):
        client = ShipStationClient(merchant['shipstation_api_key'], merchant['shipstation_api_secret'])
        rates = client.fetch_rates_for_order(order)
        if rates:
            return jsonify({'rates': rates, 'order_id': int(order_id)})

    # Return demo rates if no ShipStation creds
    return jsonify({'rates': DEMO_RATES, 'order_id': int(order_id), 'demo': True})


@app.route('/api/shipping/labels', methods=['POST'])
@login_required
def shipping_labels():
    db = get_db()
    mid = current_merchant_id()
    data = request.get_json() or {}
    order_id = data.get('order_id')
    carrier_code = data.get('carrier_code', '')
    service_code = data.get('service_code', '')

    if not order_id:
        return jsonify({'error': 'order_id required'}), 400

    order = dict_row(db.execute(
        'SELECT * FROM orders WHERE id = ? AND merchant_id = ?', (order_id, mid)
    ).fetchone())
    if not order:
        return jsonify({'error': 'Order not found'}), 404

    merchant = dict_row(db.execute('SELECT * FROM merchants WHERE id = ?', (mid,)).fetchone())

    from core.shipstation import ShipStationClient
    import random
    import string

    if merchant.get('shipstation_api_key') and merchant.get('shipstation_api_secret'):
        client = ShipStationClient(merchant['shipstation_api_key'], merchant['shipstation_api_secret'])
        result = client.purchase_label_for_order(order, carrier_code, service_code)

        if result.get('error'):
            return jsonify(result), 400

        tracking = result.get('trackingNumber', '')
    else:
        # Demo mode: generate fake tracking
        tracking = 'VS' + ''.join(random.choices(string.digits, k=12))
        result = {'trackingNumber': tracking, 'labelId': random.randint(10000, 99999), 'demo': True}

    # Update order with tracking
    db.execute(
        'UPDATE orders SET status = ?, carrier = ?, tracking_number = ?, shipped_at = ? WHERE id = ?',
        ('shipped', carrier_code or service_code, tracking, datetime.utcnow().isoformat(), order_id)
    )
    db.commit()
    audit('label_purchased', {'order_id': order_id, 'tracking': tracking, 'carrier': carrier_code})

    return jsonify(result)


@app.route('/api/shipping/labels/<int:label_id>/print', methods=['GET'])
@login_required
def shipping_label_print(label_id):
    # In production, fetch PDF from ShipStation and stream it
    return jsonify({'error': 'Label PDF download requires ShipStation API credentials', 'label_id': label_id}), 501


# ---------------------------------------------------------------------------
# AI Config
# ---------------------------------------------------------------------------

@app.route('/api/ai/config', methods=['GET'])
@login_required
def ai_config_get():
    db = get_db()
    merchant = dict_row(db.execute(
        'SELECT reply_tone, auto_reply_enabled, openai_api_key FROM merchants WHERE id = ?',
        (current_merchant_id(),)
    ).fetchone())
    merchant['has_openai_key'] = bool(merchant.get('openai_api_key'))
    merchant.pop('openai_api_key', None)
    return jsonify(merchant)


@app.route('/api/ai/config', methods=['POST'])
@login_required
def ai_config_set():
    db = get_db()
    mid = current_merchant_id()
    data = request.get_json() or {}

    updates, params = [], []
    if 'reply_tone' in data:
        updates.append('reply_tone = ?')
        params.append(data['reply_tone'])
    if 'auto_reply_enabled' in data:
        updates.append('auto_reply_enabled = ?')
        params.append(1 if data['auto_reply_enabled'] else 0)
    if 'openai_api_key' in data:
        updates.append('openai_api_key = ?')
        params.append(data['openai_api_key'])
    if 'shipstation_api_key' in data:
        updates.append('shipstation_api_key = ?')
        params.append(data['shipstation_api_key'])
    if 'shipstation_api_secret' in data:
        updates.append('shipstation_api_secret = ?')
        params.append(data['shipstation_api_secret'])
    if 'low_stock_threshold' in data:
        updates.append('low_stock_threshold = ?')
        params.append(data['low_stock_threshold'])

    if updates:
        params.append(mid)
        db.execute(f"UPDATE merchants SET {', '.join(updates)} WHERE id = ?", params)
        db.commit()
        audit('ai_config_updated', {k: '***' if 'key' in k else v for k, v in data.items()})

    return jsonify({'ok': True})


# ---------------------------------------------------------------------------
# Audit Log
# ---------------------------------------------------------------------------

@app.route('/api/audit-log', methods=['GET'])
@login_required
def audit_log_list():
    db = get_db()
    mid = current_merchant_id()
    page = int(request.args.get('page', 1))
    action = request.args.get('action')
    from_date = request.args.get('from')
    to_date = request.args.get('to')
    per_page = 50
    offset = (page - 1) * per_page

    query = 'SELECT * FROM audit_log WHERE merchant_id = ?'
    params = [mid]

    if action:
        query += ' AND action = ?'
        params.append(action)
    if from_date:
        query += ' AND created_at >= ?'
        params.append(from_date)
    if to_date:
        query += ' AND created_at <= ?'
        params.append(to_date)

    count_query = query.replace('SELECT *', 'SELECT COUNT(*) as c')
    total = db.execute(count_query, params).fetchone()['c']

    query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
    params.extend([per_page, offset])

    logs = dict_rows(db.execute(query, params).fetchall())
    return jsonify({'logs': logs, 'total': total, 'page': page, 'pages': (total + per_page - 1) // per_page})


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

@app.route('/api/settings', methods=['GET'])
@login_required
def settings_get():
    db = get_db()
    merchant = dict_row(db.execute(
        'SELECT id, business_name, email, plan, reply_tone, auto_reply_enabled, low_stock_threshold FROM merchants WHERE id = ?',
        (current_merchant_id(),)
    ).fetchone())
    return jsonify(merchant)


@app.route('/api/settings', methods=['PATCH'])
@login_required
def settings_update():
    db = get_db()
    mid = current_merchant_id()
    data = request.get_json() or {}

    updates, params = [], []
    for field in ['business_name', 'email', 'reply_tone', 'low_stock_threshold']:
        if field in data:
            updates.append(f'{field} = ?')
            params.append(data[field])

    if 'password' in data and data['password']:
        updates.append('password_hash = ?')
        params.append(hash_password(data['password']))

    if updates:
        params.append(mid)
        db.execute(f"UPDATE merchants SET {', '.join(updates)} WHERE id = ?", params)
        db.commit()
        audit('settings_updated', {k: '***' if k == 'password' else v for k, v in data.items()})

    return jsonify({'ok': True})


# ---------------------------------------------------------------------------
# Demo Data Seeding
# ---------------------------------------------------------------------------

def seed_demo_data(db):
    """Seed demo data for development."""
    existing = db.execute("SELECT id FROM merchants WHERE email = 'fabio@ftpaints.co.uk'").fetchone()
    if existing:
        return  # Already seeded

    # Create demo merchant
    db.execute(
        'INSERT INTO merchants (business_name, email, password_hash, plan, reply_tone, auto_reply_enabled) VALUES (?, ?, ?, ?, ?, ?)',
        ('FT Paints Ltd', 'fabio@ftpaints.co.uk', hash_password('demo1234'), 'pro', 'professional', 0)
    )
    merchant_id = db.execute("SELECT id FROM merchants WHERE email = 'fabio@ftpaints.co.uk'").fetchone()[0]

    # 4 Channels
    channels_data = [
        (merchant_id, 'amazon', 'Amazon UK', '{}', 1, '2024-01-15T10:30:00'),
        (merchant_id, 'ebay', 'eBay Store', '{}', 1, '2024-01-15T10:28:00'),
        (merchant_id, 'woocommerce', 'FTPaints.co.uk', '{}', 1, '2024-01-15T10:25:00'),
        (merchant_id, 'shopify', 'FT Paints Shopify', '{}', 1, '2024-01-15T09:00:00'),
    ]
    for ch in channels_data:
        db.execute('INSERT INTO channels (merchant_id, channel_type, display_name, credentials_json, active, last_sync_at) VALUES (?, ?, ?, ?, ?, ?)', ch)

    # 20 Orders
    orders_data = [
        (merchant_id, 'amazon', 'AMZ-001', 'ORD-2024-001', 'James Wilson', 'james@email.com', '14 Oak Lane, Manchester, M1 4BH',
         json.dumps([{'sku': 'FTP-WHT-5L', 'title': 'Brilliant White 5L', 'qty': 2, 'price': 24.99}]), 49.98, 'GBP', 'shipped', 'RM123456789GB', 'Royal Mail', '2024-01-10T14:00:00', '2024-01-08T09:00:00'),
        (merchant_id, 'ebay', 'EBAY-002', 'ORD-2024-002', 'Sarah Connor', 'sarah@email.com', '7 High Street, Bristol, BS1 2AW',
         json.dumps([{'sku': 'FTP-BLK-1L', 'title': 'Matt Black 1L', 'qty': 1, 'price': 12.99}]), 12.99, 'GBP', 'pending', None, None, None, '2024-01-12T11:00:00'),
        (merchant_id, 'woocommerce', 'WOO-003', 'ORD-2024-003', 'Tom Hardy', 'tom@email.com', '22 Park Road, London, SW1A 2AA',
         json.dumps([{'sku': 'FTP-PRB-2.5L', 'title': 'Primer Base 2.5L', 'qty': 3, 'price': 18.50}]), 55.50, 'GBP', 'shipped', 'DPD98765432', 'DPD', '2024-01-13T09:00:00', '2024-01-11T15:00:00'),
        (merchant_id, 'amazon', 'AMZ-004', 'ORD-2024-004', 'Emily Watson', 'emily@email.com', '5 Church Lane, Birmingham, B1 1BB',
         json.dumps([{'sku': 'FTP-EGS-5L', 'title': 'Eggshell Finish 5L', 'qty': 1, 'price': 34.99}, {'sku': 'FTP-RLR-9', 'title': '9" Roller Set', 'qty': 1, 'price': 8.99}]), 43.98, 'GBP', 'pending', None, None, None, '2024-01-14T08:30:00'),
        (merchant_id, 'shopify', 'SHP-005', 'ORD-2024-005', 'David Smith', 'david@email.com', '88 Queens Road, Edinburgh, EH2 1JQ',
         json.dumps([{'sku': 'FTP-NVY-2.5L', 'title': 'Navy Blue 2.5L', 'qty': 2, 'price': 22.99}]), 45.98, 'GBP', 'shipped', 'HERM12345678', 'Evri', '2024-01-12T16:00:00', '2024-01-10T13:00:00'),
        (merchant_id, 'ebay', 'EBAY-006', 'ORD-2024-006', 'Lisa Chang', 'lisa@email.com', '3 River Walk, Leeds, LS1 4AP',
         json.dumps([{'sku': 'FTP-WHT-5L', 'title': 'Brilliant White 5L', 'qty': 4, 'price': 24.99}]), 99.96, 'GBP', 'pending', None, None, None, '2024-01-15T07:00:00'),
        (merchant_id, 'amazon', 'AMZ-007', 'ORD-2024-007', 'Mark Thompson', 'mark@email.com', '19 Station Road, Liverpool, L1 1JF',
         json.dumps([{'sku': 'FTP-GRN-1L', 'title': 'Forest Green 1L', 'qty': 1, 'price': 14.99}]), 14.99, 'GBP', 'delivered', 'RM987654321GB', 'Royal Mail', '2024-01-06T10:00:00', '2024-01-04T12:00:00'),
        (merchant_id, 'woocommerce', 'WOO-008', 'ORD-2024-008', 'Anna Brown', 'anna@email.com', '45 The Green, Norwich, NR1 3NG',
         json.dumps([{'sku': 'FTP-RED-2.5L', 'title': 'Cherry Red 2.5L', 'qty': 1, 'price': 22.99}, {'sku': 'FTP-BRS-3', 'title': '3" Brush Set', 'qty': 2, 'price': 6.99}]), 36.97, 'GBP', 'shipped', 'UPS1Z999AA10123456784', 'UPS', '2024-01-14T11:00:00', '2024-01-12T10:00:00'),
        (merchant_id, 'shopify', 'SHP-009', 'ORD-2024-009', 'Chris Evans', 'chris@email.com', '67 Mill Lane, Sheffield, S1 2BW',
         json.dumps([{'sku': 'FTP-YLW-1L', 'title': 'Sunflower Yellow 1L', 'qty': 3, 'price': 14.99}]), 44.97, 'GBP', 'pending', None, None, None, '2024-01-15T09:30:00'),
        (merchant_id, 'amazon', 'AMZ-010', 'ORD-2024-010', 'Sophie Turner', 'sophie@email.com', '2 Castle View, York, YO1 7EP',
         json.dumps([{'sku': 'FTP-GRY-5L', 'title': 'Slate Grey 5L', 'qty': 1, 'price': 28.99}]), 28.99, 'GBP', 'shipped', 'FEDEX794644790125', 'FedEx', '2024-01-13T15:00:00', '2024-01-11T09:00:00'),
        (merchant_id, 'ebay', 'EBAY-011', 'ORD-2024-011', 'Ryan Murphy', 'ryan@email.com', '11 Brook Street, Glasgow, G1 5AH',
         json.dumps([{'sku': 'FTP-WHT-5L', 'title': 'Brilliant White 5L', 'qty': 1, 'price': 24.99}, {'sku': 'FTP-MSK-TP', 'title': 'Masking Tape 50m', 'qty': 3, 'price': 3.99}]), 36.96, 'GBP', 'pending', None, None, None, '2024-01-15T11:00:00'),
        (merchant_id, 'woocommerce', 'WOO-012', 'ORD-2024-012', 'Kate Miller', 'kate@email.com', '29 Orchard Road, Bath, BA1 2LR',
         json.dumps([{'sku': 'FTP-CRM-2.5L', 'title': 'Cream Dream 2.5L', 'qty': 2, 'price': 22.99}]), 45.98, 'GBP', 'shipped', 'RM111222333GB', 'Royal Mail', '2024-01-11T14:00:00', '2024-01-09T08:00:00'),
        (merchant_id, 'amazon', 'AMZ-013', 'ORD-2024-013', 'Peter Jones', 'peter@email.com', '8 Victoria Terrace, Cardiff, CF10 1BH',
         json.dumps([{'sku': 'FTP-PRB-2.5L', 'title': 'Primer Base 2.5L', 'qty': 5, 'price': 18.50}]), 92.50, 'GBP', 'pending', None, None, None, '2024-01-15T12:00:00'),
        (merchant_id, 'shopify', 'SHP-014', 'ORD-2024-014', 'Helen Clark', 'helen@email.com', '55 Rose Avenue, Cambridge, CB1 1DX',
         json.dumps([{'sku': 'FTP-BLU-1L', 'title': 'Ocean Blue 1L', 'qty': 2, 'price': 14.99}]), 29.98, 'GBP', 'delivered', 'DPD55566677', 'DPD', '2024-01-05T13:00:00', '2024-01-03T10:00:00'),
        (merchant_id, 'ebay', 'EBAY-015', 'ORD-2024-015', 'Gary Neville', 'gary@email.com', '42 Kings Way, Nottingham, NG1 2AA',
         json.dumps([{'sku': 'FTP-EGS-5L', 'title': 'Eggshell Finish 5L', 'qty': 2, 'price': 34.99}]), 69.98, 'GBP', 'shipped', 'HERM88899900', 'Evri', '2024-01-14T08:00:00', '2024-01-13T07:00:00'),
        (merchant_id, 'amazon', 'AMZ-016', 'ORD-2024-016', 'Fiona Apple', 'fiona@email.com', '16 Elm Grove, Brighton, BN1 3TD',
         json.dumps([{'sku': 'FTP-PNK-1L', 'title': 'Blush Pink 1L', 'qty': 1, 'price': 14.99}]), 14.99, 'GBP', 'cancelled', None, None, None, '2024-01-07T16:00:00'),
        (merchant_id, 'woocommerce', 'WOO-017', 'ORD-2024-017', 'Ian Wright', 'ian@email.com', '33 Lakeside Drive, Coventry, CV1 2SQ',
         json.dumps([{'sku': 'FTP-WHT-5L', 'title': 'Brilliant White 5L', 'qty': 3, 'price': 24.99}, {'sku': 'FTP-RLR-9', 'title': '9" Roller Set', 'qty': 1, 'price': 8.99}]), 83.96, 'GBP', 'pending', None, None, None, '2024-01-15T14:00:00'),
        (merchant_id, 'shopify', 'SHP-018', 'ORD-2024-018', 'Julia Roberts', 'julia@email.com', '77 Sunset Lane, Oxford, OX1 2EP',
         json.dumps([{'sku': 'FTP-GRN-1L', 'title': 'Forest Green 1L', 'qty': 4, 'price': 14.99}]), 59.96, 'GBP', 'shipped', 'RM444555666GB', 'Royal Mail', '2024-01-12T12:00:00', '2024-01-10T11:00:00'),
        (merchant_id, 'ebay', 'EBAY-019', 'ORD-2024-019', 'Kevin Hart', 'kevin@email.com', '9 Meadow Close, Plymouth, PL1 3DH',
         json.dumps([{'sku': 'FTP-BLK-1L', 'title': 'Matt Black 1L', 'qty': 6, 'price': 12.99}]), 77.94, 'GBP', 'pending', None, None, None, '2024-01-15T15:30:00'),
        (merchant_id, 'amazon', 'AMZ-020', 'ORD-2024-020', 'Laura Palmer', 'laura@email.com', '1 Twin Peaks Road, Aberdeen, AB10 1XG',
         json.dumps([{'sku': 'FTP-CRM-2.5L', 'title': 'Cream Dream 2.5L', 'qty': 1, 'price': 22.99}, {'sku': 'FTP-BRS-3', 'title': '3" Brush Set', 'qty': 1, 'price': 6.99}]), 29.98, 'GBP', 'shipped', 'UPS1Z999BB10654321098', 'UPS', '2024-01-14T10:00:00', '2024-01-13T14:00:00'),
    ]
    for o in orders_data:
        db.execute(
            '''INSERT INTO orders (merchant_id, channel, channel_order_id, order_number, customer_name, customer_email,
               address, items_json, total, currency, status, tracking_number, carrier, shipped_at, order_date)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', o
        )

    # 10 Messages
    messages_data = [
        (merchant_id, 'amazon', 'Where is my order? I ordered 5 days ago and still haven\'t received it. Order ORD-2024-002.', 'Sarah Connor', 'sarah@email.com', 'open', None, 'negative', 'where_is_my_order', 'Order ORD-2024-002 - Delivery query'),
        (merchant_id, 'ebay', 'I received the wrong colour paint. I ordered Navy Blue but got Ocean Blue instead.', 'David Smith', 'david@email.com', 'open', None, 'negative', 'wrong_item', 'Wrong item received'),
        (merchant_id, 'woocommerce', 'I\'d like a refund please. The paint tin was dented on arrival and some leaked out.', 'Tom Hardy', 'tom@email.com', 'open', None, 'negative', 'refund_request', 'Refund request - damaged item'),
        (merchant_id, 'amazon', 'Does the Brilliant White come in a 10L tin? I need to paint a large room.', 'Peter Jones', 'peter@email.com', 'open', None, 'neutral', 'product_question', 'Product enquiry - Brilliant White'),
        (merchant_id, 'shopify', 'Thank you so much! The paint arrived quickly and the colour is perfect. Will definitely order again!', 'Helen Clark', 'helen@email.com', 'resolved', None, 'positive', 'general', 'Positive feedback'),
        (merchant_id, 'ebay', 'This is absolutely terrible service. I\'ve been waiting 2 weeks for my order!', 'Ryan Murphy', 'ryan@email.com', 'open', None, 'negative', 'where_is_my_order', 'Urgent - delayed delivery'),
        (merchant_id, 'amazon', 'Hi, is the Eggshell Finish suitable for bathroom walls? Does it resist moisture?', 'Emily Watson', 'emily@email.com', 'open', None, 'neutral', 'product_question', 'Product suitability question'),
        (merchant_id, 'woocommerce', 'I want to cancel my order and get my money back. I found a better price elsewhere.', 'Ian Wright', 'ian@email.com', 'open', None, 'neutral', 'refund_request', 'Cancellation request'),
        (merchant_id, 'shopify', 'Your customer service is outstanding. The replacement was sent same day. Brilliant!', 'Julia Roberts', 'julia@email.com', 'resolved', None, 'positive', 'general', 'Praise for service'),
        (merchant_id, 'ebay', 'Hi there, do you ship to Northern Ireland? And what\'s the delivery charge?', 'Kevin Hart', 'kevin@email.com', 'open', None, 'neutral', 'general', 'Shipping enquiry'),
    ]
    for m in messages_data:
        db.execute(
            '''INSERT INTO messages (merchant_id, channel, body, customer_name, customer_email, status,
               ai_reply, sentiment, intent, subject) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', m
        )

    # 12 Listings
    listings_data = [
        (merchant_id, 'amazon', 'FTP-WHT-5L', 'Brilliant White Emulsion 5L', 'Premium quality brilliant white emulsion paint for interior walls and ceilings.', 24.99, 150, 'active', None),
        (merchant_id, 'ebay', 'FTP-WHT-5L', 'Brilliant White Emulsion 5L', 'Premium quality brilliant white emulsion paint.', 24.99, 150, 'active', None),
        (merchant_id, 'amazon', 'FTP-BLK-1L', 'Matt Black Paint 1L', 'Professional grade matt black paint for furniture and feature walls.', 12.99, 85, 'active', None),
        (merchant_id, 'woocommerce', 'FTP-PRB-2.5L', 'Universal Primer Base 2.5L', 'Multi-surface primer suitable for wood, metal, and plaster.', 18.50, 60, 'active', None),
        (merchant_id, 'amazon', 'FTP-EGS-5L', 'Eggshell Finish 5L', 'Durable eggshell finish for high-traffic areas and kitchens.', 34.99, 45, 'active', None),
        (merchant_id, 'shopify', 'FTP-NVY-2.5L', 'Navy Blue Emulsion 2.5L', 'Rich navy blue emulsion paint for statement walls.', 22.99, 30, 'active', None),
        (merchant_id, 'ebay', 'FTP-GRN-1L', 'Forest Green Paint 1L', 'Deep forest green paint, perfect for accent features.', 14.99, 8, 'active', None),
        (merchant_id, 'woocommerce', 'FTP-RED-2.5L', 'Cherry Red Emulsion 2.5L', 'Vibrant cherry red emulsion for bold interiors.', 22.99, 25, 'active', None),
        (merchant_id, 'amazon', 'FTP-GRY-5L', 'Slate Grey Emulsion 5L', 'Modern slate grey emulsion paint for contemporary spaces.', 28.99, 70, 'active', None),
        (merchant_id, 'shopify', 'FTP-CRM-2.5L', 'Cream Dream Emulsion 2.5L', 'Warm cream emulsion paint for cosy living spaces.', 22.99, 55, 'active', None),
        (merchant_id, 'ebay', 'FTP-RLR-9', '9" Professional Roller Set', 'Complete roller set with tray, frame, and 2 sleeves.', 8.99, 5, 'active', None),
        (merchant_id, 'woocommerce', 'FTP-BRS-3', '3" Premium Brush Set', 'Set of 3 professional paint brushes (1", 2", 3").', 6.99, 120, 'active', None),
    ]
    for l in listings_data:
        db.execute(
            'INSERT INTO listings (merchant_id, channel, sku, title, description, price, quantity, status, image_url) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)', l
        )

    # Inventory
    inventory_data = [
        (merchant_id, 'FTP-WHT-5L', 'Brilliant White Emulsion 5L', 150, 12, 138),
        (merchant_id, 'FTP-BLK-1L', 'Matt Black Paint 1L', 85, 7, 78),
        (merchant_id, 'FTP-PRB-2.5L', 'Universal Primer Base 2.5L', 60, 8, 52),
        (merchant_id, 'FTP-EGS-5L', 'Eggshell Finish 5L', 45, 3, 42),
        (merchant_id, 'FTP-NVY-2.5L', 'Navy Blue Emulsion 2.5L', 30, 4, 26),
        (merchant_id, 'FTP-GRN-1L', 'Forest Green Paint 1L', 8, 1, 7),
        (merchant_id, 'FTP-RED-2.5L', 'Cherry Red Emulsion 2.5L', 25, 1, 24),
        (merchant_id, 'FTP-GRY-5L', 'Slate Grey Emulsion 5L', 70, 2, 68),
        (merchant_id, 'FTP-CRM-2.5L', 'Cream Dream Emulsion 2.5L', 55, 3, 52),
        (merchant_id, 'FTP-RLR-9', '9" Professional Roller Set', 5, 1, 4),
        (merchant_id, 'FTP-BRS-3', '3" Premium Brush Set', 120, 3, 117),
        (merchant_id, 'FTP-YLW-1L', 'Sunflower Yellow 1L', 18, 3, 15),
    ]
    for inv in inventory_data:
        db.execute(
            'INSERT INTO inventory (merchant_id, sku, product_name, warehouse_qty, reserved_qty, available_qty) VALUES (?, ?, ?, ?, ?, ?)', inv
        )

    # 3 Purchase Orders
    po_data = [
        (merchant_id, 'Dulux Trade Supplies', 'received',
         json.dumps([{'sku': 'FTP-WHT-5L', 'title': 'Brilliant White 5L', 'qty': 100, 'cost': 12.50}, {'sku': 'FTP-BLK-1L', 'title': 'Matt Black 1L', 'qty': 50, 'cost': 6.00}]),
         1550.00, '2024-01-02T09:00:00', '2024-01-05T14:00:00'),
        (merchant_id, 'Crown Paints Wholesale', 'sent',
         json.dumps([{'sku': 'FTP-NVY-2.5L', 'title': 'Navy Blue 2.5L', 'qty': 40, 'cost': 11.00}, {'sku': 'FTP-GRN-1L', 'title': 'Forest Green 1L', 'qty': 30, 'cost': 7.00}]),
         650.00, '2024-01-10T11:00:00', None),
        (merchant_id, 'Paint Tools Direct', 'draft',
         json.dumps([{'sku': 'FTP-RLR-9', 'title': '9" Roller Set', 'qty': 50, 'cost': 4.00}, {'sku': 'FTP-BRS-3', 'title': '3" Brush Set', 'qty': 100, 'cost': 3.00}]),
         500.00, '2024-01-14T16:00:00', None),
    ]
    for po in po_data:
        db.execute(
            'INSERT INTO purchase_orders (merchant_id, vendor_name, status, items_json, total_cost, created_at, received_at) VALUES (?, ?, ?, ?, ?, ?, ?)', po
        )

    # Audit log entries
    audit_data = [
        (merchant_id, 'login', json.dumps({'email': 'fabio@ftpaints.co.uk'}), '2024-01-15T08:00:00'),
        (merchant_id, 'order_sync', json.dumps({'channels': 4}), '2024-01-15T08:01:00'),
        (merchant_id, 'label_purchased', json.dumps({'order': 'ORD-2024-001', 'carrier': 'Royal Mail'}), '2024-01-10T14:00:00'),
        (merchant_id, 'order_shipped', json.dumps({'order': 'ORD-2024-003', 'carrier': 'DPD'}), '2024-01-13T09:00:00'),
        (merchant_id, 'channel_sync', json.dumps({'channel': 'Amazon UK'}), '2024-01-15T10:30:00'),
    ]
    for a in audit_data:
        db.execute('INSERT INTO audit_log (merchant_id, action, details_json, created_at) VALUES (?, ?, ?, ?)', a)

    db.commit()


# ---------------------------------------------------------------------------
# App startup
# ---------------------------------------------------------------------------

with app.app_context():
    db = init_db()
    seed_demo_data(db)
    db.close()


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5050))
    app.run(host='0.0.0.0', port=port, debug=True)
