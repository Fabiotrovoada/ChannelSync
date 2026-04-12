# VendStack — Full Platform Specification

## 1. Concept & Vision

VendStack is an affordable all-in-one ecommerce management platform for small UK sellers (under £200/month), combining Linnworks' inventory power, eDesk's unified messaging, and ShipStation's fulfillment workflow into a single dark-themed command centre. It targets sellers doing £10k-£500k/year on Amazon, eBay, TikTok, WooCommerce and B&Q who are priced out of enterprise tools.

The personality: **dark, premium, data-dense** — like a Bloomberg terminal for ecommerce sellers. Gold accents on near-black backgrounds. No friendly mascot. Pure utility with zero fluff.

---

## 2. Design Language

### Aesthetic Direction
Bloomberg Terminal meets modern SaaS. Data-rich, dark, authoritative. Every pixel earns its place.

### Color Palette
```
--bg:          #080808   (near black — main background)
--bg2:         #111111   (cards, panels)
--bg3:         #181818   (inputs, hover states)
--bg4:         #222222   (borders, dividers)
--border:      #2a2a2a   (subtle borders)
--text:        #f0f0f0   (primary text)
--text2:       #888888   (secondary text)
--text3:       #444444   (muted/disabled text)
--gold:        #f5c518   (primary accent — CTAs, highlights)
--gold2:       #c8a012   (gold hover)
--green:       #22c55e   (success, shipped, positive)
--red:         #ef4444   (error, cancelled, urgent)
--orange:      #f97316   (warning, pending, awaiting)
--blue:        #3b82f6   (info, links)
--purple:      #a855f7   (AI-generated content)
```

### Typography
- **Primary:** Inter (Google Fonts) — clean, professional, highly legible at small sizes
- **Monospace:** JetBrains Mono — for order IDs, SKUs, prices, tracking numbers
- **Scale:** 11px (micro), 12px (caption), 13px (body), 14px (subtitle), 16px (title), 20px (heading), 28px (hero stat)

### Spatial System
- Base unit: 4px
- Component padding: 12–16px
- Card padding: 16–20px
- Section gaps: 20–24px
- Border radius: 8px (small), 12px (cards), 16px (modals)

### Motion Philosophy
- **Micro-interactions only:** 100-150ms ease transitions on hover/focus
- **No decorative animation** — data density is the visual interest
- **Skeleton loaders** on async data (pulsing bg3→bg4)
- **Toast notifications:** slide in from top-right, 3s auto-dismiss

---

## 3. Layout & Structure

### App Shell
```
┌─────────────────────────────────────────────────────┐
│ TOPBAR: Logo | Tabs | Sync Status | Notifications   │  56px
├─────────────────────────────────────────────────────┤
│ STATS BAR: Total Orders | Revenue | Awaiting | ...  │  72px
├──────────┬──────────────────────────────────────────┤
│ SIDEBAR  │  MAIN CONTENT AREA                       │
│  220px   │  (scrollable, flex-1)                   │
│          │                                          │
│ Channels │                                          │
│ Filters  │                                          │
│          │                                          │
└──────────┴──────────────────────────────────────────┘
```

### Pages / Routes
```
/ ................ Dashboard (stats + recent orders)
/orders ........... Orders list (filterable by channel, status, date)
/orders/:id ....... Order detail (items, customer, timeline, actions)
/messages ......... Unified inbox (thread list + thread view)
/listings ......... Product listings grid (search, filter, edit)
/inventory ........ Inventory levels across channels
/purchase-orders .. PO management (create, receive, track)
/shipping ......... ShipStation integration (labels, rates)
/ai-studio ........ AI reply composer, auto-reply config
/channels ......... Connected channels + credentials
/settings ......... Account, billing, notifications
```

### Responsive Strategy
- **≥1280px:** Full layout (sidebar + content)
- **768–1279px:** Sidebar collapses to icon rail
- **<768px:** Sidebar hidden, hamburger menu, stacked stats

---

## 4. Features & Interactions

### 4.1 Authentication
- Email + password login (JWT session)
- Registration with plan selection (Starter £49 / Pro £99 / Scale £199)
- Session persistence via httpOnly cookie
- Logout clears session

### 4.2 Dashboard
- KPI cards: Total Orders, Revenue (shipped), Awaiting Ship, Shipped This Week, Open Messages, Active Channels
- Recent orders table (last 10, with channel badge + status)
- Messages preview (last 5 open threads)
- Sync status indicator per channel
- Quick actions: Sync All, Add Channel, Create PO

### 4.3 Orders
- **List view:** Paginated table (25/50/100 per page), sortable columns
- **Filters:** Channel, Status, Date range, Search (order ID, customer name, SKU)
- **Bulk actions:** Mark shipped, Export CSV, Push to ShipStation
- **Order detail:** Full customer info, item list, order timeline, tracking entry, tracking push to channel
- **Status flow:** Pending → Shipped → Delivered | Cancelled
- **Sync:** Pulls from Amazon SP-API, eBay API, WooCommerce REST API, Mirakl

### 4.4 Messages (Unified Inbox)
- Threads grouped by channel and customer
- Thread view: message history + reply box
- **AI Reply:** One-click AI-generated reply (contextual to message content)
- **AI Composer:** Free-form message composer with tone selector (Professional/Friendly/Empathetic/Firm)
- Auto-tagging: Urgent (negative sentiment), Order-related, Pre-sale, Complaint
- Mark resolved / Reopen
- Template insertion (pre-saved reply templates)

### 4.5 Listings
- Grid view of all channel listings
- Inline edit: Price, quantity, title
- Bulk price adjustment (% or £ amount, filter by channel/keyword)
- Channel-specific listing status
- Image thumbnail, SKU, title, price, quantity, channel badge
- Listing health: Low stock warning (<10 units), Missing description flag

### 4.6 Inventory
- Stock levels aggregated across all channels per SKU
- Central warehouse quantity
- Low stock alerts (configurable threshold per product)
- Stock adjustment log
- Reserved stock (allocated to pending orders)

### 4.7 Purchase Orders
- Create PO to supplier (manual: vendor name, items, quantities, cost)
- Mark received: updates inventory automatically
- PO statuses: Draft → Sent → Partially Received → Received
- Cost tracking vs budget

### 4.8 Shipping (ShipStation)
- Order selection → Fetch carrier rates
- Display: Royal Mail, DPD, Hermes, UPS, FedEx rates side-by-side
- One-click label purchase + print
- Tracking number pushed back to channel (Amazon, eBay)
- Tracking number emailed to customer automatically
- Batch label printing (select multiple orders)

### 4.9 AI Studio
- **Auto-reply engine:** Detects message intent (Where is my order? / Wrong item / Refund request / Product question / General)
- **Sentiment detection:** Flags negative messages for priority handling
- **Reply tone:** Configurable per merchant (Professional/Friendly/Empathetic/Firm)
- **GPT-4 integration (optional):** If OpenAI key provided, uses GPT for generation; otherwise falls back to rule-based
- **Reply templates:** Customizable rule-based templates per intent type
- **AI metrics:** Replies generated, time saved, resolution rate

### 4.10 Channels
- Connect: Amazon SP-API, eBay OAuth, WooCommerce REST API, Shopify API, TikTok Shop, Mirakl/B&Q
- Per-channel: Enable/disable, last sync time, order count, error log
- Credentials stored encrypted (AES-256)

### 4.11 Settings
- Profile: Business name, email, password change
- Billing: Plan display (upgrade CTA if on free tier)
- Notifications: Email alerts for new orders, low stock, urgent messages
- API Keys: OpenAI key, ShipStation key+secret

### 4.12 Audit Log
- All actions logged: Order status changes, shipping labels purchased, channel syncs, user logins
- Filterable by date, action type, user

---

## 5. Component Inventory

### KPI Card
- States: Loading (skeleton), Loaded, Error
- Gold value, grey label, delta indicator (↑↓ vs last week)

### Data Table
- States: Loading (skeleton rows), Empty, Populated, Error
- Sortable columns (click header)
- Row hover: bg2
- Selected row: left gold border

### Status Badge
- Variants: pending (orange), shipped (green), cancelled (red), open (blue), resolved (green muted)
- 10px uppercase monospace text, 2px 7px padding, 4px radius

### Channel Badge
- Amazon: #ff9900 bg, black text
- eBay: #e53238 bg, white text
- WooCommerce: #9b5c8f bg, white text
- Shopify: #96bf48 bg, black text
- TikTok: #ff0050 bg, white text
- Mirakl/B&Q: #003087 bg, white text

### Message Bubble
- Inbound: bg3, left-aligned, 4px 14px 14px 14px radius
- Outbound (AI): gold-tinted bg, right-aligned, 14px 4px 14px 14px radius
- Timestamp below, right-aligned

### Modal
- Centered, max 480px wide, bg2, 16px radius, 24px padding
- Dark overlay (rgba(0,0,0,0.7))
- Close: X button top-right + click outside

### Toast Notification
- Top-right, slide in from right, 3s auto-dismiss
- Success: green left border
- Error: red left border
- Info: blue left border

### Form Controls
- Input: bg3, 1px border, 8px radius, 9px 12px padding
- Select: same as input
- Toggle: 40×22px, gold when on
- Button primary: gold bg, black text, 700 weight
- Button ghost: bg4, border, grey text

---

## 6. Technical Approach

### Stack
- **Backend:** Python 3.9+, Flask 3, SQLite (multi-tenant by merchant_id)
- **Frontend:** React 18 + Vite, plain CSS (no Tailwind), React Router v6
- **File storage:** Local filesystem (uploads/ directory)
- **Auth:** Flask sessions with server-side session store
- **Background jobs:** APScheduler (sync jobs, low stock alerts)
- **Deployment:** Render.com (Python web service) or Railway

### API Design (REST)
```
POST   /api/auth/login
POST   /api/auth/register
POST   /api/auth/logout

GET    /api/dashboard/stats

GET    /api/orders              ?channel=&status=&page=&search=
GET    /api/orders/:id
PATCH  /api/orders/:id          {status, tracking_number}
POST   /api/orders/sync         {channel?}  ← triggers channel adapters
POST   /api/orders/:id/ship     {carrier, tracking_number}  ← pushes to ShipStation

GET    /api/messages            ?status=open
GET    /api/messages/:id
POST   /api/messages/:id/reply  {reply}
POST   /api/messages/:id/ai-reply
POST   /api/messages/ai-compose {context, tone}

GET    /api/channels
POST   /api/channels
PATCH  /api/channels/:id
DELETE /api/channels/:id
POST   /api/channels/:id/sync

GET    /api/listings            ?channel=&search=&page=
PATCH  /api/listings/:id
POST   /api/listings/bulk-update {ids[], changes{price?, quantity?}}

GET    /api/inventory
PATCH  /api/inventory/:sku       {quantity_delta, reason}

GET    /api/purchase-orders
POST   /api/purchase-orders
PATCH  /api/purchase-orders/:id  {status, items[]}
POST   /api/purchase-orders/:id/receive  {items[{sku, qty_received}]}

GET    /api/shipping/rates      ?order_id=   ← fetches from ShipStation
POST   /api/shipping/labels      {order_id, carrier_service_id}
GET    /api/shipping/labels/:id/print  ← PDF download

GET    /api/ai/config
POST   /api/ai/config            {openai_api_key?, reply_tone?, auto_reply_enabled?}

GET    /api/audit-log            ?page=&action=&from=&to=
```

### Data Model

**merchants**
- id (PK), business_name, email, password_hash, plan, created_at
- openai_api_key (encrypted), reply_tone, auto_reply_enabled
- low_stock_threshold (INT, default 10)

**channels**
- id (PK), merchant_id (FK), channel_type, display_name
- credentials_json (encrypted), active (BOOL), last_sync_at
- error_log (TEXT)

**orders**
- id (PK), merchant_id (FK), channel, channel_order_id
- order_number, customer_name, customer_email, address
- items_json (TEXT), total (REAL), currency
- status (pending/shipped/delivered/cancelled), tracking_number
- carrier, shipped_at, order_date, created_at

**messages**
- id (PK), merchant_id (FK), channel, channel_message_id
- subject, body, customer_name, customer_email
- ai_reply, status (open/resolved), order_id (FK nullable)
- sentiment, intent, created_at, replied_at

**listings**
- id (PK), merchant_id (FK), channel, sku (indexed)
- title, description, price, quantity
- status (active/inactive), image_url, created_at

**inventory**
- id (PK), merchant_id (FK), sku (indexed)
- warehouse_qty, reserved_qty, available_qty
- last_updated

**purchase_orders**
- id (PK), merchant_id (FK), vendor_name, status
- items_json, total_cost, created_at, received_at

**audit_log**
- id (PK), merchant_id (FK), action, details_json, created_at

### Channel Adapters (Abstract Base)
```python
class ChannelAdapter(ABC):
    @abstractmethod
    def fetch_orders(since: datetime) -> List[NormalizedOrder]: pass

    @abstractmethod
    def push_tracking(order_id: str, tracking: str, carrier: str): pass

    @abstractmethod
    def fetch_listings() -> List[NormalizedListing]: pass
```

### ShipStation Integration
- Endpoints: GET /orders, POST /orders (create), GET /shipping/rates, POST /shipping/labels
- Auth: API Key + Secret in Basic Auth header
- Flow: Order received → Fetch rates → Purchase label → Push tracking to channel

### Security
- Passwords: SHA-256 hashed (no plaintext, ever)
- API keys in credentials_json: AES-256 encrypted with server key
- All DB queries parameterized (no SQL injection)
- CORS: whitelist only allowed origins in production
- Rate limiting: 100 req/min per merchant on write endpoints

---

## 7. Development Phases

**Phase 1 (This Build):** Full stack — Flask backend + React frontend, all routes wired, ShipStation integration, AI messaging, listings, inventory, PO management.

**Phase 2:** Real channel adapters (Amazon SP-API OAuth, eBay OAuth, WooCommerce API, TikTok API)

**Phase 3:** Multi-user teams, role-based access, webhook receivers

**Phase 4:** Analytics dashboard (revenue charts, channel comparison, trend lines)

---

## 8. File Structure
```
vendstack/
├── SPEC.md
├── app.py                      ← Flask backend (all routes)
├── requirements.txt
├── /adapters                   ← Channel adapter implementations
│   ├── __init__.py
│   ├── base.py
│   ├── amazon.py
│   ├── ebay.py
│   ├── woocommerce.py
│   ├── shopify.py
│   ├── tiktok.py
│   └── mirakl.py
├── /core
│   ├── ai_engine.py            ← AI messaging engine
│   ├── sync_engine.py          ← Multi-channel sync orchestrator
│   └── shipstation.py          ← ShipStation API client
├── /db
│   └── schema.sql
├── /client                     ← React frontend
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── /src
│   │   ├── main.jsx
│   │   ├── App.jsx
│   │   ├── /components
│   │   ├── /pages
│   │   └── /api
│   └── /public
└── /uploads
```
