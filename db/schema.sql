-- VendStack Database Schema (SQLite)

CREATE TABLE IF NOT EXISTS merchants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    plan TEXT NOT NULL DEFAULT 'starter',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    openai_api_key TEXT,
    shipstation_api_key TEXT,
    shipstation_api_secret TEXT,
    reply_tone TEXT DEFAULT 'professional',
    auto_reply_enabled INTEGER DEFAULT 0,
    low_stock_threshold INTEGER DEFAULT 10
);

CREATE TABLE IF NOT EXISTS channels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    merchant_id INTEGER NOT NULL REFERENCES merchants(id),
    channel_type TEXT NOT NULL,
    display_name TEXT NOT NULL,
    credentials_json TEXT,
    active INTEGER DEFAULT 1,
    last_sync_at TIMESTAMP,
    error_log TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    merchant_id INTEGER NOT NULL REFERENCES merchants(id),
    channel TEXT NOT NULL,
    channel_order_id TEXT,
    order_number TEXT NOT NULL,
    customer_name TEXT NOT NULL,
    customer_email TEXT,
    address TEXT,
    items_json TEXT NOT NULL DEFAULT '[]',
    total REAL NOT NULL DEFAULT 0,
    currency TEXT DEFAULT 'GBP',
    status TEXT NOT NULL DEFAULT 'pending',
    tracking_number TEXT,
    carrier TEXT,
    shipped_at TIMESTAMP,
    order_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    merchant_id INTEGER NOT NULL REFERENCES merchants(id),
    channel TEXT NOT NULL,
    channel_message_id TEXT,
    subject TEXT,
    body TEXT NOT NULL,
    customer_name TEXT NOT NULL,
    customer_email TEXT,
    ai_reply TEXT,
    status TEXT NOT NULL DEFAULT 'open',
    order_id INTEGER REFERENCES orders(id),
    sentiment TEXT,
    intent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    replied_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS listings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    merchant_id INTEGER NOT NULL REFERENCES merchants(id),
    channel TEXT NOT NULL,
    sku TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    price REAL NOT NULL DEFAULT 0,
    quantity INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'active',
    image_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_listings_sku ON listings(sku);

CREATE TABLE IF NOT EXISTS inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    merchant_id INTEGER NOT NULL REFERENCES merchants(id),
    sku TEXT NOT NULL,
    product_name TEXT,
    warehouse_qty INTEGER NOT NULL DEFAULT 0,
    reserved_qty INTEGER NOT NULL DEFAULT 0,
    available_qty INTEGER NOT NULL DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_inventory_sku ON inventory(sku);

CREATE TABLE IF NOT EXISTS purchase_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    merchant_id INTEGER NOT NULL REFERENCES merchants(id),
    vendor_name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft',
    items_json TEXT NOT NULL DEFAULT '[]',
    total_cost REAL NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    received_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    merchant_id INTEGER NOT NULL REFERENCES merchants(id),
    action TEXT NOT NULL,
    details_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_orders_merchant ON orders(merchant_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_messages_merchant ON messages(merchant_id);
CREATE INDEX IF NOT EXISTS idx_messages_status ON messages(status);
CREATE TABLE IF NOT EXISTS carriers (
    id TEXT PRIMARY KEY,
    merchant_id INTEGER NOT NULL REFERENCES merchants(id),
    carrier_type TEXT NOT NULL,
    display_name TEXT NOT NULL,
    credentials_json TEXT,
    active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_carriers_merchant ON carriers(merchant_id);

CREATE INDEX IF NOT EXISTS idx_channels_merchant ON channels(merchant_id);
CREATE INDEX IF NOT EXISTS idx_audit_merchant ON audit_log(merchant_id);
CREATE INDEX IF NOT EXISTS idx_po_merchant ON purchase_orders(merchant_id);
