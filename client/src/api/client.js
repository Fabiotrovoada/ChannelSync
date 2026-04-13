const BASE = '/api';

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw { status: res.status, ...data };
  return data;
}

const get = (path) => request(path);
const post = (path, body) => request(path, { method: 'POST', body: JSON.stringify(body) });
const patch = (path, body) => request(path, { method: 'PATCH', body: JSON.stringify(body) });
const del = (path) => request(path, { method: 'DELETE' });

export const api = {
  // Auth
  login: (email, password) => post('/auth/login', { email, password }),
  register: (data) => post('/auth/register', data),
  logout: () => post('/auth/logout'),
  me: () => get('/auth/me'),

  // Dashboard
  dashboardStats: () => get('/dashboard/stats'),

  // Orders
  orders: (params = {}) => {
    const q = new URLSearchParams(params).toString();
    return get(`/orders?${q}`);
  },
  order: (id) => get(`/orders/${id}`),
  updateOrder: (id, data) => patch(`/orders/${id}`, data),
  syncOrders: () => post('/orders/sync'),
  shipOrder: (id, data) => post(`/orders/${id}/ship`, data),

  // Messages
  messages: (params = {}) => {
    const q = new URLSearchParams(params).toString();
    return get(`/messages?${q}`);
  },
  message: (id) => get(`/messages/${id}`),
  replyMessage: (id, reply) => post(`/messages/${id}/reply`, { reply }),
  aiReply: (id) => post(`/messages/${id}/ai-reply`),
  aiCompose: (context, tone) => post('/messages/ai-compose', { context, tone }),

  // Channels
  channels: () => get('/channels'),
  createChannel: (data) => post('/channels', data),
  updateChannel: (id, data) => patch(`/channels/${id}`, data),
  deleteChannel: (id) => del(`/channels/${id}`),
  syncChannel: (id) => post(`/channels/${id}/sync`),

  // Listings
  listings: (params = {}) => {
    const q = new URLSearchParams(params).toString();
    return get(`/listings?${q}`);
  },
  updateListing: (id, data) => patch(`/listings/${id}`, data),
  bulkUpdateListings: (ids, changes) => post('/listings/bulk-update', { ids, changes }),

  // Inventory
  inventory: () => get('/inventory'),
  updateInventory: (sku, data) => patch(`/inventory/${sku}`, data),

  // Purchase Orders
  purchaseOrders: () => get('/purchase-orders'),
  createPO: (data) => post('/purchase-orders', data),
  updatePO: (id, data) => patch(`/purchase-orders/${id}`, data),
  receivePO: (id, items) => post(`/purchase-orders/${id}/receive`, { items }),

  // Shipping
  shippingRates: (orderId) => get(`/shipping/rates?order_id=${orderId}`),
  purchaseLabel: (data) => post('/shipping/labels', data),

  // AI
  aiConfig: () => get('/ai/config'),
  updateAiConfig: (data) => post('/ai/config', data),

  // Audit
  auditLog: (params = {}) => {
    const q = new URLSearchParams(params).toString();
    return get(`/audit-log?${q}`);
  },

  // Settings
  settings: () => get('/settings'),
  updateSettings: (data) => patch('/settings', data),
};
