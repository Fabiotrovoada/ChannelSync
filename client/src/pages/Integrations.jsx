import { useState, useEffect } from 'react';
import { api } from '../api/client';

const CATEGORIES = [
  { id: 'marketplace', label: 'Marketplaces', icon: '🏪', color: '#f5c518' },
  { id: 'carrier', label: 'Couriers', icon: '🚚', color: '#3b82f6' },
  { id: 'aggregator', label: 'Aggregators', icon: '📦', color: '#a855f7' },
  { id: '3pl', label: '3PL & Fulfillment', icon: '🏭', color: '#22c55e' },
  { id: 'accounting', label: 'Accounting', icon: '📊', color: '#f97316' },
  { id: 'payments', label: 'Payments', icon: '💳', color: '#ec4899' },
];

const CATALOG = {
  marketplace: [
    { id: 'amazon', name: 'Amazon', desc: 'SP-API — UK, US, DE, FR, IT, ES marketplaces. Full order sync, tracking, and catalog.', emoji: '📦', color: '#FF9900', tier: 'core' },
    { id: 'ebay', name: 'eBay', desc: 'eBay UK + global — fulfillment API, inventory management, tracking push.', emoji: '🏷️', color: '#E53238', tier: 'core' },
    { id: 'shopify', name: 'Shopify', desc: 'Shopify Admin API — orders, products, fulfillments, inventory levels.', emoji: '🛍️', color: '#96BF48', tier: 'core' },
    { id: 'woocommerce', name: 'WooCommerce', desc: 'WooCommerce REST API — orders, products, stock sync.', emoji: '🛒', color: '#9B5C8F', tier: 'core' },
    { id: 'etsy', name: 'Etsy', desc: 'Etsy API v3 — orders, listings, tracking updates, shop management.', emoji: '🎨', color: '#F56400', tier: 'standard' },
    { id: 'walmart', name: 'Walmart', desc: 'Walmart Marketplace API — US orders, inventory, tracking.', emoji: '🛒', color: '#00464F', tier: 'standard' },
    { id: 'tiktok', name: 'TikTok Shop', desc: 'TikTok social commerce — orders, products, affiliate sync.', emoji: '🎵', color: '#FF0050', tier: 'standard' },
    { id: 'onbuy', name: 'OnBuy', desc: 'UK marketplace — orders, tracking, pricing sync.', emoji: '🇬🇧', color: '#00B4E6', tier: 'standard' },
    { id: 'fruugo', name: 'Fruugo', desc: 'International marketplace — European and global expansion.', emoji: '🌍', color: '#7B2D8E', tier: 'standard' },
    { id: 'mirakl', name: 'B&Q / Mirakl', desc: 'Mirakl-based marketplaces — B&Q, Auchan, and other dropship platforms.', emoji: '🏪', color: '#003087', tier: 'standard' },
  ],
  carrier: [
    { id: 'royal_mail', name: 'Royal Mail', desc: 'Click & Drop API — 1st/2nd Class, Signed, Special Delivery.', emoji: '👑', color: '#E60000', tier: 'core' },
    { id: 'dpd', name: 'DPD UK', desc: 'DPD WebConnect API — Next Day, 48hr, Saturday, International.', emoji: '🚚', color: '#E60000', tier: 'core' },
    { id: 'evri', name: 'Evri', desc: 'Formerly Hermes — Evri Courier, Express, and International services.', emoji: '📦', color: '#00B4E6', tier: 'standard' },
    { id: 'dhl', name: 'DHL UK', desc: 'DHL Express, Economy Select, and Freight services for UK + international.', emoji: '✈️', color: '#FFCC00', tier: 'standard' },
    { id: 'ups', name: 'UPS', desc: 'UPS API — Next Day Air, 2nd Day Air, Ground, Worldwide Express.', emoji: '📦', color: '#351C15', tier: 'standard' },
    { id: 'fedex', name: 'FedEx', desc: 'FedEx API — Priority Overnight, 2Day, Ground, International Priority.', emoji: '📦', color: '#4D148C', tier: 'standard' },
    { id: 'yodel', name: 'Yodel', desc: 'Yodel UK — Standard, Express, Morning, and International delivery.', emoji: '🚚', color: '#009A44', tier: 'standard' },
  ],
  aggregator: [
    { id: 'shipstation', name: 'ShipStation', desc: 'Aggregate 40+ carriers through ShipStation — rates, labels, tracking.', emoji: '🚢', color: '#0066CC', tier: 'standard' },
  ],
  '3pl': [
    { id: 'amazon_fba', name: 'Amazon FBA', desc: 'Send inventory to Amazon fulfillment centers. Amazon handles storage, picking, packing, and delivery.', emoji: '📦', color: '#FF9900', tier: 'core' },
  ],
  accounting: [
    { id: 'xero', name: 'Xero', desc: 'Sync orders as invoices, track expenses, manage contacts in Xero.', emoji: '📊', color: '#13B5EA', tier: 'pro' },
    { id: 'quickbooks', name: 'QuickBooks', desc: 'QuickBooks Online — invoices, expenses, bank reconciliation.', emoji: '📊', color: '#2CA01C', tier: 'pro' },
  ],
  payments: [
    { id: 'stripe', name: 'Stripe', desc: 'Track Stripe balance, transactions, and payouts alongside your orders.', emoji: '💳', color: '#635BFF', tier: 'pro' },
    { id: 'paypal', name: 'PayPal', desc: 'PayPal Business — transaction history, balance, and payout tracking.', emoji: '💰', color: '#003087', tier: 'pro' },
  ],
};

const TIER_COLORS = { core: 'var(--accent)', standard: 'var(--text2)', pro: '#a855f7' };
const TIER_LABELS = { core: 'Included', standard: 'Standard', pro: 'Pro' };

export default function Integrations() {
  const [activeCategory, setActiveCategory] = useState('marketplace');
  const [connected, setConnected] = useState({});
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(null);
  const [installing, setInstalling] = useState(false);
  const [config, setConfig] = useState({});

  useEffect(() => {
    api.get('/plugins').then(d => {
      const m = {};
      (d.plugins || []).forEach(p => { m[p.id] = p.is_connected; });
      setConnected(m);
    }).catch(() => {}).finally(() => setLoading(false));
  }, []);

  async function installPlugin(pluginId) {
    setInstalling(true);
    try {
      const result = await api.post(`/plugins/${pluginId}/install`, { config });
      if (result.ok) {
        setConnected(prev => ({ ...prev, [pluginId]: true }));
        setShowModal(null);
        setConfig({});
      }
    } catch (e) {}
    setInstalling(false);
  }

  async function uninstallPlugin(pluginId) {
    if (!window.confirm('Remove this integration?')) return;
    try {
      await api.post(`/plugins/${pluginId}/uninstall`, {});
      setConnected(prev => { const n = { ...prev }; delete n[pluginId]; return n; });
    } catch (e) {}
  }

  const items = CATALOG[activeCategory] || [];
  const category = CATEGORIES.find(c => c.id === activeCategory);

  return (
    <div className="page" style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div className="page-header">
        <div className="page-title-row">
          <h1 className="page-title">Integrations</h1>
          <p className="page-subtitle">Connect your stack — marketplaces, carriers, accounting, and more</p>
        </div>
      </div>

      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* Category sidebar */}
        <div style={{ width: 200, borderRight: '1px solid var(--border)', background: 'var(--surface)', flexShrink: 0, overflowY: 'auto' }}>
          {CATEGORIES.map(cat => (
            <div
              key={cat.id}
              onClick={() => setActiveCategory(cat.id)}
              style={{
                padding: '10px 16px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 10,
                background: activeCategory === cat.id ? 'var(--accent-light)' : 'transparent',
                borderLeft: activeCategory === cat.id ? `3px solid ${cat.color}` : '3px solid transparent',
                color: activeCategory === cat.id ? 'var(--accent)' : 'var(--text2)',
                fontSize: 13.5, fontWeight: activeCategory === cat.id ? 600 : 400,
                transition: 'all 0.1s',
              }}
            >
              <span>{cat.icon}</span>
              <span>{cat.label}</span>
            </div>
          ))}
        </div>

        {/* Content */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '20px 24px' }}>
          <div style={{ marginBottom: 20 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 4 }}>
              <span style={{ fontSize: 22 }}>{category?.icon}</span>
              <h2 style={{ fontSize: 17, fontWeight: 700, color: 'var(--text)' }}>{category?.label}</h2>
            </div>
            <p style={{ fontSize: 13, color: 'var(--text2)' }}>{items.length} integration{items.length !== 1 ? 's' : ''} available</p>
          </div>

          <div className="integrations-grid" style={{ padding: 0 }}>
            {items.map(plugin => (
              <div key={plugin.id} className="integration-card">
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12, marginBottom: 10 }}>
                  <div style={{ width: 42, height: 42, borderRadius: 10, background: plugin.color, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 18, flexShrink: 0 }}>
                    {plugin.emoji}
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 7, marginBottom: 2 }}>
                      <span style={{ fontSize: 14, fontWeight: 700, color: 'var(--text)' }}>{plugin.name}</span>
                      <span style={{ fontSize: 10, fontWeight: 700, padding: '1px 5px', borderRadius: 3, background: TIER_COLORS[plugin.tier] + '20', color: TIER_COLORS[plugin.tier] }}>
                        {TIER_LABELS[plugin.tier]}
                      </span>
                    </div>
                    {connected[plugin.id] && (
                      <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                        <div style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--green)' }} />
                        <span style={{ fontSize: 11, color: 'var(--green)', fontWeight: 600 }}>Connected</span>
                      </div>
                    )}
                  </div>
                </div>
                <p style={{ fontSize: 12.5, color: 'var(--text2)', lineHeight: 1.5, marginBottom: 12 }}>{plugin.desc}</p>
                {connected[plugin.id] ? (
                  <div style={{ display: 'flex', gap: 7 }}>
                    <button className="btn btn-ghost btn-sm" style={{ flex: 1 }} onClick={() => uninstallPlugin(plugin.id)}>Remove</button>
                    <button className="btn btn-ghost btn-sm" style={{ flex: 1 }} onClick={() => { setShowModal(plugin.id); setConfig({}); }}>Configure</button>
                  </div>
                ) : (
                  <button className="btn btn-sm" style={{ width: '100%', justifyContent: 'center', background: plugin.color, color: '#000', fontWeight: 700 }} onClick={() => { setShowModal(plugin.id); setConfig({}); }}>
                    + Connect
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Modal */}
      {showModal && (() => {
        const plugin = items.find(i => i.id === showModal);
        if (!plugin) return null;
        return (
          <div className="modal-overlay" onClick={e => e.target === e.currentTarget && setShowModal(null)}>
            <div className="modal" style={{ maxWidth: 440 }}>
              <div className="modal-header">
                <h3>Connect {plugin.name}</h3>
                <button className="modal-close" onClick={() => setShowModal(null)}>✕</button>
              </div>
              <div className="modal-body">
                <p style={{ fontSize: 13, color: 'var(--text2)', marginBottom: 16, lineHeight: 1.5 }}>
                  Enter your {plugin.name} API credentials from your {plugin.name} developer portal or account settings.
                </p>
                {plugin.id === 'amazon' && <>
                  <div className="form-group"><label className="form-label">SP-API Client ID</label><input className="form-input" value={config.client_id||''} onChange={e => setConfig({...config, client_id: e.target.value})} style={{ fontFamily: 'monospace' }} /></div>
                  <div className="form-group"><label className="form-label">SP-API Client Secret</label><input type="password" className="form-input" value={config.client_secret||''} onChange={e => setConfig({...config, client_secret: e.target.value})} style={{ fontFamily: 'monospace' }} /></div>
                  <div className="form-group"><label className="form-label">Refresh Token</label><input type="password" className="form-input" value={config.refresh_token||''} onChange={e => setConfig({...config, refresh_token: e.target.value})} style={{ fontFamily: 'monospace' }} /></div>
                </>}
                {plugin.id === 'woocommerce' && <>
                  <div className="form-group"><label className="form-label">Store URL</label><input className="form-input" value={config.url||''} onChange={e => setConfig({...config, url: e.target.value})} placeholder="https://shop.example.com" /></div>
                  <div className="form-group"><label className="form-label">Consumer Key</label><input className="form-input" value={config.consumer_key||''} onChange={e => setConfig({...config, consumer_key: e.target.value})} style={{ fontFamily: 'monospace' }} /></div>
                  <div className="form-group"><label className="form-label">Consumer Secret</label><input type="password" className="form-input" value={config.consumer_secret||''} onChange={e => setConfig({...config, consumer_secret: e.target.value})} style={{ fontFamily: 'monospace' }} /></div>
                </>}
                {plugin.id === 'shopify' && <>
                  <div className="form-group"><label className="form-label">Shop Domain (e.g. mystore.myshopify.com)</label><input className="form-input" value={config.shop||''} onChange={e => setConfig({...config, shop: e.target.value})} style={{ fontFamily: 'monospace' }} /></div>
                  <div className="form-group"><label className="form-label">Access Token</label><input type="password" className="form-input" value={config.access_token||''} onChange={e => setConfig({...config, access_token: e.target.value})} style={{ fontFamily: 'monospace' }} /></div>
                </>}
                {plugin.id === 'stripe' && <div className="form-group"><label className="form-label">Stripe Secret Key (sk_live_...)</label><input type="password" className="form-input" value={config.api_key||''} onChange={e => setConfig({...config, api_key: e.target.value})} style={{ fontFamily: 'monospace' }} /></div>}
                {plugin.id === 'xero' && <>
                  <div className="form-group"><label className="form-label">Client ID</label><input className="form-input" value={config.client_id||''} onChange={e => setConfig({...config, client_id: e.target.value})} style={{ fontFamily: 'monospace' }} /></div>
                  <div className="form-group"><label className="form-label">Client Secret</label><input type="password" className="form-input" value={config.client_secret||''} onChange={e => setConfig({...config, client_secret: e.target.value})} style={{ fontFamily: 'monospace' }} /></div>
                </>}
                {(plugin.id === 'royal_mail' || plugin.id === 'dpd') && <>
                  <div className="form-group"><label className="form-label">API Key / Client ID</label><input className="form-input" value={config.client_id||''} onChange={e => setConfig({...config, client_id: e.target.value})} style={{ fontFamily: 'monospace' }} /></div>
                  <div className="form-group"><label className="form-label">API Secret</label><input type="password" className="form-input" value={config.client_secret||''} onChange={e => setConfig({...config, client_secret: e.target.value})} style={{ fontFamily: 'monospace' }} /></div>
                </>}
              </div>
              <div className="modal-footer">
                <button className="btn btn-ghost" onClick={() => setShowModal(null)}>Cancel</button>
                <button className="btn btn-primary" onClick={() => installPlugin(plugin.id)} disabled={installing} style={{ background: plugin.color }}>
                  {installing ? 'Connecting...' : 'Connect'}
                </button>
              </div>
            </div>
          </div>
        );
      })()}
    </div>
  );
}
