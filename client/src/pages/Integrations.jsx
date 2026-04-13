import { useState, useEffect } from 'react';
import { api } from '../api/client';

const PLUGIN_CATEGORIES = [
  { id: 'marketplace', label: 'Marketplaces', icon: '🏪', color: '#f5c518' },
  { id: 'carrier', label: 'Couriers', icon: '🚚', color: '#3b82f6' },
  { id: 'aggregator', label: 'Aggregators', icon: '📦', color: '#a855f7' },
  { id: '3pl', label: '3PL & Fulfillment', icon: '🏭', color: '#22c55e' },
  { id: 'accounting', label: 'Accounting', icon: '📊', color: '#f97316' },
  { id: 'payments', label: 'Payments', icon: '💳', color: '#ec4899' },
  { id: 'returns', label: 'Returns', icon: '↩️', color: '#ef4444' },
  { id: 'repricer', label: 'Repricer', icon: '📈', color: '#06b6d4' },
  { id: 'dropship', label: 'Dropship', icon: '✈️', color: '#84cc16' },
];

const PLUGIN_CATALOG = {
  marketplace: [
    { id: 'amazon', name: 'Amazon', description: 'Amazon SP-API — UK, US, DE, FR, IT, ES marketplaces. Full order sync, tracking, and catalog management.', icon: '📦', color: '#FF9900', connected: false, tier: 'core' },
    { id: 'ebay', name: 'eBay', description: 'eBay UK + global — fulfillment API, inventory management, tracking push.', icon: '🏷️', color: '#E53238', connected: false, tier: 'core' },
    { id: 'shopify', name: 'Shopify', description: 'Shopify Admin API — orders, products, fulfillments, inventory levels.', icon: '🛍️', color: '#96BF48', connected: false, tier: 'core' },
    { id: 'woocommerce', name: 'WooCommerce', description: 'WooCommerce REST API — orders, products, stock sync. Works with Self-hosted + WooCommerce.com.', icon: '🛒', color: '#9B5C8F', connected: false, tier: 'core' },
    { id: 'etsy', name: 'Etsy', description: 'Etsy API v3 — orders, listings, tracking updates, shop management.', icon: '🎨', color: '#F56400', connected: false, tier: 'standard' },
    { id: 'walmart', name: 'Walmart', description: 'Walmart Marketplace API — US orders, inventory, tracking.', icon: '🛒', color: '#00464F', connected: false, tier: 'standard' },
    { id: 'bigcommerce', name: 'BigCommerce', description: 'BigCommerce REST API v3 — full catalog, orders, and inventory sync.', icon: '💻', color: '#1A1A1A', connected: false, tier: 'standard' },
    { id: 'onbuy', name: 'OnBuy', description: 'UK marketplace — orders, tracking, pricing sync.', icon: '🇬🇧', color: '#00B4E6', connected: false, tier: 'standard' },
    { id: 'fruugo', name: 'Fruugo', description: 'International marketplace — European and global expansion.', icon: '🌍', color: '#7B2D8E', connected: false, tier: 'standard' },
    { id: 'tiktok', name: 'TikTok Shop', description: 'TikTok social commerce — orders, products, affiliate sync.', icon: '🎵', color: '#FF0050', connected: false, tier: 'standard' },
    { id: 'mirakl', name: 'B&Q / Mirakl', description: 'Mirakl-based marketplaces — B&Q, Auchan, and other dropship platforms.', icon: '🏪', color: '#003087', connected: false, tier: 'standard' },
    { id: 'magento', name: 'Magento 2', description: 'Magento Open Source + Commerce REST API — enterprise catalog and orders.', icon: '🛍️', color: '#F46F25', connected: false, tier: 'pro' },
    { id: 'prestashop', name: 'PrestaShop', description: 'PrestaShop 1.7+ REST API — European open-source ecommerce platform.', icon: '🛒', color: '#1A1A1A', connected: false, tier: 'pro' },
  ],
  carrier: [
    { id: 'royal_mail', name: 'Royal Mail', description: 'Click & Drop API — 1st/2nd Class, Signed, Special Delivery, International.', icon: '👑', color: '#E60000', connected: false, tier: 'core' },
    { id: 'dpd', name: 'DPD UK', description: 'DPD WebConnect API — Next Day, 48hr, Saturday, International services.', icon: '🚚', color: '#E60000', connected: false, tier: 'core' },
    { id: 'evri', name: 'Evri', description: 'Formerly Hermes — Evri Courier, Express, and International services.', icon: '📦', color: '#00B4E6', connected: false, tier: 'standard' },
    { id: 'dhl', name: 'DHL UK', description: 'DHL Express, Economy Select, and Freight services for UK + international.', icon: '✈️', color: '#FFCC00', connected: false, tier: 'standard' },
    { id: 'ups', name: 'UPS', description: 'UPS API — Next Day Air, 2nd Day Air, Ground, Worldwide Express.', icon: '📦', color: '#351C15', connected: false, tier: 'standard' },
    { id: 'fedex', name: 'FedEx', description: 'FedEx API — Priority Overnight, 2Day, Ground, International Priority.', icon: '📦', color: '#4D148C', connected: false, tier: 'standard' },
    { id: 'yodel', name: 'Yodel', description: 'Yodel UK — Standard, Express, Morning, and International delivery.', icon: '🚚', color: '#009A44', connected: false, tier: 'standard' },
    { id: 'parcelforce', name: 'Parcelforce', description: 'Parcelforce Express 24, 48, AM, and International via Royal Mail Group.', icon: '📦', color: '#CC0000', connected: false, tier: 'standard' },
  ],
  aggregator: [
    { id: 'shipstation', name: 'ShipStation', description: 'Aggregate 40+ carriers through ShipStation — rates, labels, tracking.', icon: '🚢', color: '#0066CC', connected: false, tier: 'standard' },
  ],
  '3pl': [
    { id: 'amazon_fba', name: 'Amazon FBA', description: 'Send inventory to Amazon fulfillment centers. Amazon handles storage, picking, packing, and delivery. Track FBA orders.', icon: '📦', color: '#FF9900', connected: false, tier: 'core' },
  ],
  accounting: [
    { id: 'xero', name: 'Xero', description: 'Sync orders as invoices, track expenses, manage contacts in Xero accounting.', icon: '📊', color: '#13B5EA', connected: false, tier: 'pro' },
    { id: 'quickbooks', name: 'QuickBooks', description: 'QuickBooks Online integration — invoices, expenses, bank reconciliation.', icon: '#', color: '#2CA01C', connected: false, tier: 'pro' },
    { id: 'freeagent', name: 'FreeAgent', description: 'UK accounting for freelancers and small businesses — expenses and invoicing.', icon: '📊', color: '#00A499', connected: false, tier: 'pro' },
  ],
  payments: [
    { id: 'stripe', name: 'Stripe', description: 'Track Stripe balance, transactions, and payouts alongside your orders.', icon: '💳', color: '#635BFF', connected: false, tier: 'pro' },
    { id: 'paypal', name: 'PayPal', description: 'PayPal Business — transaction history, balance, and payout tracking.', icon: '💰', color: '#003087', connected: false, tier: 'pro' },
  ],
  returns: [
    { id: 'loop_returns', name: 'Loop Returns', description: 'Automated returns portal — branded experience, instant refunds, exchanges.', icon: '↩️', color: '#00D4AA', connected: false, tier: 'pro' },
    { id: 'returnprime', name: 'ReturnPrime', description: 'One-click returns for Shopify — prepaid labels, automated refund processing.', icon: '↩️', color: '#6366F1', connected: false, tier: 'pro' },
  ],
  repricer: [
    { id: 'repricer', name: 'Repricer', description: 'Automated repricing across Amazon, eBay — stay competitive with rule-based repricing.', icon: '📈', color: '#10B981', connected: false, tier: 'standard' },
  ],
  dropship: [
    { id: 'bjbd', name: 'B&J Dropship', description: 'Access to 100,000+ products from UK distributors. Auto-import listings, place orders directly to suppliers.', icon: '✈️', color: '#0EA5E9', connected: false, tier: 'standard' },
  ],
};

const TIER_LABELS = { core: 'Included', standard: 'Standard', pro: 'Pro' };
const TIER_COLORS = { core: 'var(--gold)', standard: 'var(--text2)', pro: 'var(--purple)' };

export default function Integrations() {
  const [activeCategory, setActiveCategory] = useState('marketplace');
  const [plugins, setPlugins] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(null);
  const [installing, setInstalling] = useState(false);
  const [config, setConfig] = useState({});
  const [connected, setConnected] = useState({});
  const [health, setHealth] = useState({});

  useEffect(() => {
    loadPlugins();
  }, []);

  async function loadPlugins() {
    try {
      const data = await api.get('/api/plugins');
      const pluginMap = {};
      const healthMap = {};
      if (data.plugins) {
        data.plugins.forEach(p => {
          pluginMap[p.id] = p.is_connected;
          if (p.is_connected) healthMap[p.id] = p.health_status;
        });
      }
      setConnected(pluginMap);
      setHealth(healthMap);
    } catch(e) {}
    setLoading(false);
  }

  async function installPlugin(pluginId) {
    setInstalling(true);
    try {
      const result = await api.post(`/api/plugins/${pluginId}/install`, { config });
      if (result.ok) {
        setConnected(prev => ({ ...prev, [pluginId]: true }));
        setHealth(prev => ({ ...prev, [pluginId]: 'ok' }));
        setShowModal(null);
        setConfig({});
      }
    } catch(e) {}
    setInstalling(false);
  }

  async function uninstallPlugin(pluginId) {
    if (!confirm('Remove this integration?')) return;
    try {
      await api.post(`/api/plugins/${pluginId}/uninstall`, {});
      setConnected(prev => { const n = { ...prev }; delete n[pluginId]; return n; });
      setHealth(prev => { const n = { ...prev }; delete n[pluginId]; return n; });
    } catch(e) {}
  }

  const category = PLUGIN_CATEGORIES.find(c => c.id === activeCategory);
  const items = PLUGIN_CATALOG[activeCategory] || [];

  return (
    <div style={{ display: 'flex', height: '100%', overflow: 'hidden' }}>
      {/* Sidebar */}
      <div style={{ width: '220px', background: 'var(--bg2)', borderRight: '1px solid var(--border)', padding: '16px 0', flexShrink: 0 }}>
        <div style={{ padding: '0 16px 12px', borderBottom: '1px solid var(--border)', marginBottom: '8px' }}>
          <div style={{ fontSize: '13px', fontWeight: '800', color: 'var(--gold)', letterSpacing: '1px', textTransform: 'uppercase' }}>Integrations</div>
          <div style={{ fontSize: '11px', color: 'var(--text3)', marginTop: '2px' }}>Connect your stack</div>
        </div>
        {PLUGIN_CATEGORIES.map(cat => (
          <div
            key={cat.id}
            onClick={() => setActiveCategory(cat.id)}
            style={{
              padding: '9px 16px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '10px',
              background: activeCategory === cat.id ? 'var(--bg3)' : 'transparent',
              borderLeft: activeCategory === cat.id ? `3px solid ${cat.color}` : '3px solid transparent',
              color: activeCategory === cat.id ? 'var(--text)' : 'var(--text2)',
              fontSize: '13px', fontWeight: activeCategory === cat.id ? '600' : '400',
              transition: 'all 0.1s',
            }}
          >
            <span style={{ fontSize: '14px' }}>{cat.icon}</span>
            <span>{cat.label}</span>
            <span style={{ marginLeft: 'auto', fontSize: '11px', color: 'var(--text3)' }}>
              {items.filter(i => connected[i.id]).length}/{items.length}
            </span>
          </div>
        ))}
      </div>

      {/* Content */}
      <div style={{ flex: 1, overflow: 'auto', padding: '24px' }}>
        <div style={{ marginBottom: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '4px' }}>
            <span style={{ fontSize: '24px' }}>{category?.icon}</span>
            <h1 style={{ fontSize: '20px', fontWeight: '800', color: 'var(--text)' }}>{category?.label}</h1>
          </div>
          <p style={{ fontSize: '13px', color: 'var(--text3)' }}>
            {items.length} integration{items.length !== 1 ? 's' : ''} available
            {activeCategory === 'marketplace' ? ' — sell everywhere from one dashboard' : ''}
            {activeCategory === 'carrier' ? ' — compare rates and print labels instantly' : ''}
          </p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '14px' }}>
          {items.map(plugin => (
            <div
              key={plugin.id}
              style={{
                background: 'var(--bg2)', border: `1px solid ${connected[plugin.id] ? plugin.color : 'var(--border)'}`,
                borderRadius: '12px', padding: '16px',
                transition: 'all 0.15s',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px', marginBottom: '10px' }}>
                <div style={{
                  width: '40px', height: '40px', borderRadius: '10px',
                  background: plugin.color, display: 'flex', alignItems: 'center',
                  justifyContent: 'center', fontSize: '18px', flexShrink: 0,
                  boxShadow: connected[plugin.id] ? `0 0 12px ${plugin.color}40` : 'none',
                }}>
                  {plugin.icon}
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '2px' }}>
                    <span style={{ fontSize: '14px', fontWeight: '700', color: 'var(--text)' }}>{plugin.name}</span>
                    <span style={{
                      fontSize: '10px', fontWeight: '700', padding: '2px 6px', borderRadius: '4px',
                      background: TIER_COLORS[plugin.tier] + '20', color: TIER_COLORS[plugin.tier],
                    }}>
                      {TIER_LABELS[plugin.tier]}
                    </span>
                  </div>
                  {connected[plugin.id] && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '4px', marginTop: '2px' }}>
                      <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--green)', boxShadow: '0 0 6px var(--green)' }} />
                      <span style={{ fontSize: '11px', color: 'var(--green)' }}>Connected</span>
                      {health[plugin.id] && (
                        <span style={{ fontSize: '11px', color: 'var(--text3)' }}>· {health[plugin.id]}</span>
                      )}
                    </div>
                  )}
                </div>
              </div>

              <p style={{ fontSize: '12px', color: 'var(--text2)', lineHeight: '1.5', marginBottom: '12px' }}>
                {plugin.description}
              </p>

              <div style={{ display: 'flex', gap: '8px' }}>
                {connected[plugin.id] ? (
                  <>
                    <button
                      onClick={() => uninstallPlugin(plugin.id)}
                      style={{
                        flex: 1, padding: '7px', borderRadius: '7px', fontSize: '12px', fontWeight: '600',
                        background: 'var(--bg4)', color: 'var(--text2)', border: '1px solid var(--border)',
                        cursor: 'pointer',
                      }}
                    >
                      Remove
                    </button>
                    <button
                      onClick={() => { setShowModal(plugin.id); setConfig({}); }}
                      style={{
                        flex: 1, padding: '7px', borderRadius: '7px', fontSize: '12px', fontWeight: '600',
                        background: plugin.color + '15', color: plugin.color, border: `1px solid ${plugin.color}40`,
                        cursor: 'pointer',
                      }}
                    >
                      Configure
                    </button>
                  </>
                ) : (
                  <button
                    onClick={() => { setShowModal(plugin.id); setConfig({}); }}
                    style={{
                      flex: 1, padding: '8px', borderRadius: '7px', fontSize: '12px', fontWeight: '700',
                      background: plugin.color, color: '#000', border: 'none', cursor: 'pointer',
                    }}
                  >
                    + Connect
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Modal */}
      {showModal && (() => {
        const plugin = items.find(i => i.id === showModal);
        if (!plugin) return null;
        return (
          <div style={{
            position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)', zIndex: 200,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }} onClick={e => e.target === e.currentTarget && setShowModal(null)}>
            <div style={{
              background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '16px',
              width: '100%', maxWidth: '440px', padding: '24px',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px' }}>
                <div style={{ width: '36px', height: '36px', borderRadius: '8px', background: plugin.color, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '16px' }}>{plugin.icon}</div>
                <div>
                  <div style={{ fontSize: '15px', fontWeight: '700', color: 'var(--text)' }}>Connect {plugin.name}</div>
                  <div style={{ fontSize: '12px', color: 'var(--text3)' }}>{plugin.description.substring(0, 60)}...</div>
                </div>
              </div>

              <div style={{ marginBottom: '16px' }}>
                <p style={{ fontSize: '12px', color: 'var(--text2)', marginBottom: '12px', lineHeight: '1.5' }}>
                  Enter your {plugin.name} API credentials. You can find these in your {plugin.name} developer portal or account settings.
                </p>
                {plugin.id === 'amazon' && (
                  <>
                    <div style={{ marginBottom: '10px' }}>
                      <label style={{ fontSize: '11px', fontWeight: '600', color: 'var(--text3)', display: 'block', marginBottom: '4px' }}>SP-API Client ID</label>
                      <input type='text' value={config.client_id || ''} onChange={e => setConfig({...config, client_id: e.target.value})} style={{ width: '100%', background: 'var(--bg3)', border: '1px solid var(--border)', borderRadius: '8px', padding: '9px 12px', fontSize: '13px', color: 'var(--text)', outline: 'none', fontFamily: 'monospace' }} />
                    </div>
                    <div style={{ marginBottom: '10px' }}>
                      <label style={{ fontSize: '11px', fontWeight: '600', color: 'var(--text3)', display: 'block', marginBottom: '4px' }}>SP-API Client Secret</label>
                      <input type='password' value={config.client_secret || ''} onChange={e => setConfig({...config, client_secret: e.target.value})} style={{ width: '100%', background: 'var(--bg3)', border: '1px solid var(--border)', borderRadius: '8px', padding: '9px 12px', fontSize: '13px', color: 'var(--text)', outline: 'none', fontFamily: 'monospace' }} />
                    </div>
                    <div style={{ marginBottom: '10px' }}>
                      <label style={{ fontSize: '11px', fontWeight: '600', color: 'var(--text3)', display: 'block', marginBottom: '4px' }}>Refresh Token</label>
                      <input type='password' value={config.refresh_token || ''} onChange={e => setConfig({...config, refresh_token: e.target.value})} style={{ width: '100%', background: 'var(--bg3)', border: '1px solid var(--border)', borderRadius: '8px', padding: '9px 12px', fontSize: '13px', color: 'var(--text)', outline: 'none', fontFamily: 'monospace' }} />
                    </div>
                  </>
                )}
                {plugin.id === 'xero' && (
                  <>
                    <div style={{ marginBottom: '10px' }}>
                      <label style={{ fontSize: '11px', fontWeight: '600', color: 'var(--text3)', display: 'block', marginBottom: '4px' }}>Client ID</label>
                      <input type='text' value={config.client_id || ''} onChange={e => setConfig({...config, client_id: e.target.value})} style={{ width: '100%', background: 'var(--bg3)', border: '1px solid var(--border)', borderRadius: '8px', padding: '9px 12px', fontSize: '13px', color: 'var(--text)', outline: 'none', fontFamily: 'monospace' }} />
                    </div>
                    <div style={{ marginBottom: '10px' }}>
                      <label style={{ fontSize: '11px', fontWeight: '600', color: 'var(--text3)', display: 'block', marginBottom: '4px' }}>Client Secret</label>
                      <input type='password' value={config.client_secret || ''} onChange={e => setConfig({...config, client_secret: e.target.value})} style={{ width: '100%', background: 'var(--bg3)', border: '1px solid var(--border)', borderRadius: '8px', padding: '9px 12px', fontSize: '13px', color: 'var(--text)', outline: 'none', fontFamily: 'monospace' }} />
                    </div>
                    <div style={{ marginBottom: '10px' }}>
                      <label style={{ fontSize: '11px', fontWeight: '600', color: 'var(--text3)', display: 'block', marginBottom: '4px' }}>Tenant ID</label>
                      <input type='text' value={config.tenant_id || ''} onChange={e => setConfig({...config, tenant_id: e.target.value})} style={{ width: '100%', background: 'var(--bg3)', border: '1px solid var(--border)', borderRadius: '8px', padding: '9px 12px', fontSize: '13px', color: 'var(--text)', outline: 'none', fontFamily: 'monospace' }} />
                    </div>
                  </>
                )}
                {plugin.id === 'stripe' && (
                  <div style={{ marginBottom: '10px' }}>
                    <label style={{ fontSize: '11px', fontWeight: '600', color: 'var(--text3)', display: 'block', marginBottom: '4px' }}>Stripe Secret Key (sk_live_...)</label>
                    <input type='password' value={config.api_key || ''} onChange={e => setConfig({...config, api_key: e.target.value})} style={{ width: '100%', background: 'var(--bg3)', border: '1px solid var(--border)', borderRadius: '8px', padding: '9px 12px', fontSize: '13px', color: 'var(--text)', outline: 'none', fontFamily: 'monospace' }} />
                  </div>
                )}
                {(plugin.id === 'royal_mail' || plugin.id === 'dpd' || plugin.id === 'yodel' || plugin.id === 'parcelforce') && (
                  <>
                    <div style={{ marginBottom: '10px' }}>
                      <label style={{ fontSize: '11px', fontWeight: '600', color: 'var(--text3)', display: 'block', marginBottom: '4px' }}>API Key / Client ID</label>
                      <input type='text' value={config.client_id || ''} onChange={e => setConfig({...config, client_id: e.target.value})} style={{ width: '100%', background: 'var(--bg3)', border: '1px solid var(--border)', borderRadius: '8px', padding: '9px 12px', fontSize: '13px', color: 'var(--text)', outline: 'none', fontFamily: 'monospace' }} />
                    </div>
                    <div style={{ marginBottom: '10px' }}>
                      <label style={{ fontSize: '11px', fontWeight: '600', color: 'var(--text3)', display: 'block', marginBottom: '4px' }}>API Secret / Password</label>
                      <input type='password' value={config.client_secret || ''} onChange={e => setConfig({...config, client_secret: e.target.value})} style={{ width: '100%', background: 'var(--bg3)', border: '1px solid var(--border)', borderRadius: '8px', padding: '9px 12px', fontSize: '13px', color: 'var(--text)', outline: 'none', fontFamily: 'monospace' }} />
                    </div>
                  </>
                )}
                {(plugin.id === 'woocommerce') && (
                  <>
                    <div style={{ marginBottom: '10px' }}>
                      <label style={{ fontSize: '11px', fontWeight: '600', color: 'var(--text3)', display: 'block', marginBottom: '4px' }}>Store URL</label>
                      <input type='text' value={config.url || ''} onChange={e => setConfig({...config, url: e.target.value})} placeholder='https://shop.example.com' style={{ width: '100%', background: 'var(--bg3)', border: '1px solid var(--border)', borderRadius: '8px', padding: '9px 12px', fontSize: '13px', color: 'var(--text)', outline: 'none' }} />
                    </div>
                    <div style={{ marginBottom: '10px' }}>
                      <label style={{ fontSize: '11px', fontWeight: '600', color: 'var(--text3)', display: 'block', marginBottom: '4px' }}>Consumer Key</label>
                      <input type='text' value={config.consumer_key || ''} onChange={e => setConfig({...config, consumer_key: e.target.value})} style={{ width: '100%', background: 'var(--bg3)', border: '1px solid var(--border)', borderRadius: '8px', padding: '9px 12px', fontSize: '13px', color: 'var(--text)', outline: 'none', fontFamily: 'monospace' }} />
                    </div>
                    <div style={{ marginBottom: '10px' }}>
                      <label style={{ fontSize: '11px', fontWeight: '600', color: 'var(--text3)', display: 'block', marginBottom: '4px' }}>Consumer Secret</label>
                      <input type='password' value={config.consumer_secret || ''} onChange={e => setConfig({...config, consumer_secret: e.target.value})} style={{ width: '100%', background: 'var(--bg3)', border: '1px solid var(--border)', borderRadius: '8px', padding: '9px 12px', fontSize: '13px', color: 'var(--text)', outline: 'none', fontFamily: 'monospace' }} />
                    </div>
                  </>
                )}
                {(plugin.id === 'shopify') && (
                  <>
                    <div style={{ marginBottom: '10px' }}>
                      <label style={{ fontSize: '11px', fontWeight: '600', color: 'var(--text3)', display: 'block', marginBottom: '4px' }}>Shop Domain (e.g. mystore.myshopify.com)</label>
                      <input type='text' value={config.shop || ''} onChange={e => setConfig({...config, shop: e.target.value})} style={{ width: '100%', background: 'var(--bg3)', border: '1px solid var(--border)', borderRadius: '8px', padding: '9px 12px', fontSize: '13px', color: 'var(--text)', outline: 'none', fontFamily: 'monospace' }} />
                    </div>
                    <div style={{ marginBottom: '10px' }}>
                      <label style={{ fontSize: '11px', fontWeight: '600', color: 'var(--text3)', display: 'block', marginBottom: '4px' }}>Access Token (from Shopify Partner Dashboard)</label>
                      <input type='password' value={config.access_token || ''} onChange={e => setConfig({...config, access_token: e.target.value})} style={{ width: '100%', background: 'var(--bg3)', border: '1px solid var(--border)', borderRadius: '8px', padding: '9px 12px', fontSize: '13px', color: 'var(--text)', outline: 'none', fontFamily: 'monospace' }} />
                    </div>
                  </>
                )}
              </div>

              <div style={{ display: 'flex', gap: '8px' }}>
                <button onClick={() => setShowModal(null)} style={{ flex: 1, padding: '9px', borderRadius: '8px', fontSize: '13px', fontWeight: '600', background: 'var(--bg4)', color: 'var(--text2)', border: '1px solid var(--border)', cursor: 'pointer' }}>Cancel</button>
                <button
                  onClick={() => installPlugin(plugin.id)}
                  disabled={installing}
                  style={{
                    flex: 1, padding: '9px', borderRadius: '8px', fontSize: '13px', fontWeight: '700',
                    background: installing ? 'var(--bg4)' : plugin.color,
                    color: '#000', border: 'none', cursor: installing ? 'not-allowed' : 'pointer',
                    opacity: installing ? 0.6 : 1,
                  }}
                >
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
