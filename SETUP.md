# VendStack — Setup Guide

## Quick Start (Development)

### 1. Install dependencies

```bash
# Backend
cd vendstack-full
pip install -r requirements.txt

# Frontend
cd client
npm install
```

### 2. Run the backend

```bash
cd vendstack-full
python3 app.py
```

Backend runs on **http://localhost:5050**

### 3. Run the frontend (new terminal)

```bash
cd vendstack-full/client
npm run dev
```

Frontend runs on **http://localhost:5173** (proxies API calls to Flask on 5050)

### 4. Login

| | |
|---|---|
| **URL** | http://localhost:5173 |
| **Email** | `fabio@ftpaints.co.uk` |
| **Password** | `demo1234` |

---

## Deploy to Render.com (Free Tier)

### 1. Push to GitHub

```bash
cd vendstack-full
git init
git add .
git commit -m "VendStack v1"
gh repo create vendstack --public --push
# OR manually: add remote + git push
```

### 2. Deploy on Render

1. Go to [render.com](https://render.com) → Sign in with GitHub
2. Click **"New +"** → **"Web Service"**
3. Connect your `vendstack` repo
4. Configure:
   - **Name:** `vendstack`
   - **Region:** London
   - **Branch:** `main`
   - **Root Directory:** (leave blank)
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
   - **Plan:** Free

5. Add Environment Variable:
   - `SECRET_KEY` = a random string (e.g. `python -c "import secrets; print(secrets.token_hex(32))"`)

6. Click **"Create Web Service"**

### 3. Update API Client for Production

After deploy, update the API base URL in `client/src/api/client.js`:

```javascript
const BASE = 'https://your-render-url.onrender.com/api';
```

Then rebuild:
```bash
cd client && npm run build
```

---

## Demo Data

The app seeds itself with demo data on first run:

- **Merchant:** FTPaints Ltd (fabio@ftpaints.co.uk / demo1234)
- **Plan:** Pro
- **Channels:** Amazon UK, eBay UK, WooCommerce, TikTok Shop
- **Orders:** 20 realistic orders across channels
- **Messages:** 10 open customer threads
- **Listings:** 12 product listings with SKUs, prices, stock levels
- **Inventory:** Stock levels per SKU
- **Purchase Orders:** 3 POs (draft, sent, received)

---

## API Endpoints

All endpoints require authentication (session cookie).

| Method | Path | Description |
|--------|------|-------------|
| POST | /api/auth/login | Login with email + password |
| POST | /api/auth/register | Create account |
| POST | /api/auth/logout | Logout |
| GET | /api/auth/me | Current merchant info |
| GET | /api/dashboard/stats | KPI statistics |
| GET | /api/orders | List orders (filter by channel, status, search) |
| GET | /api/orders/:id | Order detail |
| PATCH | /api/orders/:id | Update order (status, tracking) |
| POST | /api/orders/sync | Sync all channels |
| POST | /api/orders/:id/ship | Push to ShipStation, get tracking |
| GET | /api/messages | List messages (filter by status) |
| POST | /api/messages/:id/reply | Send reply |
| POST | /api/messages/:id/ai-reply | Generate AI reply |
| POST | /api/messages/ai-compose | Compose from context |
| GET | /api/channels | List connected channels |
| POST | /api/channels | Add channel |
| POST | /api/channels/:id/toggle | Enable/disable channel |
| POST | /api/channels/:id/sync | Sync single channel |
| GET | /api/listings | List all listings |
| PATCH | /api/listings/:id | Update listing |
| POST | /api/listings/bulk-update | Bulk price/qty update |
| GET | /api/inventory | Stock levels |
| PATCH | /api/inventory/:sku | Adjust stock |
| GET | /api/purchase-orders | List POs |
| POST | /api/purchase-orders | Create PO |
| PATCH | /api/purchase-orders/:id | Update PO |
| POST | /api/purchase-orders/:id/receive | Receive PO items |
| GET | /api/shipping/rates | Get carrier rates for order |
| POST | /api/shipping/labels | Purchase shipping label |
| GET | /api/shipping/labels/:id/print | Download label PDF |
| GET | /api/ai/config | Get AI settings |
| POST | /api/ai/config | Update AI settings |
| GET | /api/audit-log | Activity log |

---

## Channel Credentials

When adding a channel, provide credentials as JSON:

**Amazon SP-API:**
```json
{"api_key": "...", "api_secret": "...", "marketplace_id": "ATVPDKIKX0DER"}
```

**eBay OAuth:**
```json
{"client_id": "...", "client_secret": "...", "refresh_token": "..."}
```

**WooCommerce:**
```json
{"url": "https://shop.example.com", "consumer_key": "...", "consumer_secret": "..."}
```

**ShipStation:**
Add in Settings page (API Key + Secret) — used for all label purchasing.

---

## Integrations

### Marketplaces (11 channels)
| Channel | Status | Auth | Key Methods |
|---------|--------|------|-------------|
| Amazon SP-API | ✅ Ready | LWA OAuth 2.0 | fetch_orders, push_tracking, fetch_listings |
| eBay | ✅ Ready | OAuth 2.0 | fetch_orders, push_tracking, fetch_listings |
| WooCommerce | ✅ Ready | REST API Key | fetch_orders, push_tracking, fetch_listings |
| Shopify | ✅ Ready | OAuth 2.0 | fetch_orders, push_tracking, fetch_listings |
| Etsy | ✅ Ready | OAuth 2.0 | fetch_orders, push_tracking, fetch_listings |
| Walmart | ✅ Ready | OAuth 2.0 | fetch_orders, push_tracking, fetch_listings |
| OnBuy | ✅ Ready | API Key | fetch_orders, push_tracking |
| BigCommerce | ✅ Ready | REST API Token | fetch_orders, push_tracking, fetch_listings |
| Fruugo | ✅ Ready | API Key | fetch_orders, push_tracking |
| TikTok Shop | 🔜 Next | OAuth 2.0 | (stub — awaiting TikTok API approval) |
| Mirakl/B&Q | ✅ Ready | API Key | fetch_orders, push_tracking, fetch_listings |

### Carriers (8 direct + ShipStation)
| Carrier | Status | Auth | Key Methods |
|---------|--------|------|-------------|
| Royal Mail | ✅ Ready | OAuth 2.0 | get_rates, create_label, track_package |
| DPD UK | ✅ Ready | JWT | get_rates, create_label, track_package |
| Evri | ✅ Ready | OAuth 2.0 | get_rates, create_label, track_package |
| DHL UK | ✅ Ready | API Key | get_rates, create_label, track_package |
| UPS | ✅ Ready | OAuth 2.0 | get_rates, create_label, track_package |
| FedEx | ✅ Ready | OAuth 2.0 | get_rates, create_label, track_package |
| Yodel | ✅ Ready | API Key | get_rates, create_label, track_package |
| Parcelforce | ✅ Ready | OAuth 2.0 | get_rates, create_label, track_package |
| ShipStation | ✅ Ready | API Key | get_rates, create_label, track_package (fallback) |

### Carrier Credentials Format
```json
{
  "royal_mail": {"client_id": "...", "client_secret": "...", "account_number": "..."},
  "dpd": {"username": "...", "password": "...", "api_key": "...", "account_number": "..."},
  "evri": {"client_id": "...", "client_secret": "...", "base_url": "https://api.evri.com"},
  "dhl": {"api_key": "...", "account_number": "..."},
  "ups": {"client_id": "...", "client_secret": "...", "account_number": "..."},
  "fedex": {"api_key": "...", "api_secret": "...", "account_number": "...", "meter_number": "..."},
  "yodel": {"api_key": "...", "account_id": "..."},
  "parcelforce": {"client_id": "...", "client_secret": "...", "account_number": "..."}
}
```

## Architecture

- **Backend:** Flask 3 + SQLite (multi-tenant, merchant_id on every table)
- **Frontend:** React 18 + Vite + React Router v6
- **Auth:** Server-side sessions with httpOnly cookies
- **AI:** Intent detection + rule-based replies; GPT-4 when OpenAI key provided
- **Shipping:** ShipStation API + 8 direct carrier APIs for rates and label purchase
- **Sync:** Per-channel adapter pattern (all 11 marketplace adapters implemented)
