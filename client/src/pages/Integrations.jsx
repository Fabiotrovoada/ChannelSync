import { useState, useEffect, useCallback } from 'react'
import { api } from '../api/client'
import { useToast } from '../App'
import { LayoutGrid, Truck, Boxes, Factory, Calculator, CreditCard, CheckCircle, XCircle, Plus, Trash2 } from 'lucide-react'

const CATEGORIES = [
  { id: 'marketplace', label: 'Marketplaces', icon: LayoutGrid },
  { id: 'carrier', label: 'Carriers', icon: Truck },
  { id: 'aggregator', label: 'Aggregators', icon: Boxes },
  { id: '3pl', label: '3PL & Fulfillment', icon: Factory },
  { id: 'accounting', label: 'Accounting', icon: Calculator },
  { id: 'payments', label: 'Payments', icon: CreditCard },
];

// All available integrations with their credentials config fields
const CATALOG = {
  marketplace: [
    { id: 'amazon', name: 'Amazon', desc: 'SP-API — UK, US, DE, FR, IT, ES marketplaces.', emoji: '📦', color: '#FF9900', tier: 'core' },
    { id: 'ebay', name: 'eBay', desc: 'eBay UK + global — fulfillment API and inventory.', emoji: '🏷️', color: '#E53238', tier: 'core' },
    { id: 'shopify', name: 'Shopify', desc: 'Shopify Admin API — orders, products, fulfillments.', emoji: '🛍️', color: '#96BF48', tier: 'core' },
    { id: 'woocommerce', name: 'WooCommerce', desc: 'WooCommerce REST API — orders, products, stock.', emoji: '🛒', color: '#9B5C8F', tier: 'core' },
    { id: 'etsy', name: 'Etsy', desc: 'Etsy API v3 — orders, listings, tracking updates.', emoji: '🎨', color: '#F56400', tier: 'standard' },
    { id: 'walmart', name: 'Walmart', desc: 'Walmart Marketplace API — US orders and inventory.', emoji: '🛒', color: '#00464F', tier: 'standard' },
    { id: 'tiktok', name: 'TikTok Shop', desc: 'TikTok social commerce — orders and products.', emoji: '🎵', color: '#FF0050', tier: 'standard' },
    { id: 'onbuy', name: 'OnBuy', desc: 'UK marketplace — orders, tracking, pricing sync.', emoji: '🇬🇧', color: '#00B4E6', tier: 'standard' },
    { id: 'fruugo', name: 'Fruugo', desc: 'International marketplace for European expansion.', emoji: '🌍', color: '#7B2D8E', tier: 'standard' },
    { id: 'mirakl', name: 'Mirakl / B&Q', desc: 'Mirakl-based marketplaces — B&Q, Auchan dropship.', emoji: '🏪', color: '#003087', tier: 'standard' },
  ],
  carrier: [
    { id: 'royal_mail', name: 'Royal Mail', desc: 'Click & Drop — 1st/2nd Class, Signed, Special Delivery.', emoji: '👑', color: '#E60000', tier: 'core' },
    { id: 'dpd', name: 'DPD UK', desc: 'DPD WebConnect API — Next Day, 48hr, Saturday.', emoji: '📦', color: '#E60000', tier: 'core' },
    { id: 'evri', name: 'Evri', desc: 'Formerly Hermes — Evri Courier, Express, International.', emoji: '📮', color: '#00B4E6', tier: 'standard' },
    { id: 'dhl', name: 'DHL UK', desc: 'DHL Express, Economy Select, and Freight.', emoji: '✈️', color: '#FFCC00', tier: 'standard' },
    { id: 'ups', name: 'UPS', desc: 'UPS API — Next Day Air, 2nd Day Air, Ground.', emoji: '📦', color: '#351C15', tier: 'standard' },
    { id: 'fedex', name: 'FedEx', desc: 'FedEx API — Priority Overnight, 2Day, Ground.', emoji: '📦', color: '#4D148C', tier: 'standard' },
    { id: 'yodel', name: 'Yodel', desc: 'Yodel UK — Standard, Express, Morning delivery.', emoji: '🚚', color: '#009A44', tier: 'standard' },
  ],
  aggregator: [
    { id: 'shipstation', name: 'ShipStation', desc: 'Aggregate 40+ carriers — rates, labels, tracking.', emoji: '🚢', color: '#0066CC', tier: 'standard' },
  ],
  '3pl': [
    { id: 'amazon_fba', name: 'Amazon FBA', desc: 'Send inventory to Amazon fulfillment centers.', emoji: '📦', color: '#FF9900', tier: 'core' },
  ],
  accounting: [
    { id: 'xero', name: 'Xero', desc: 'Sync orders as invoices, track expenses.', emoji: '📊', color: '#13B5EA', tier: 'pro' },
    { id: 'quickbooks', name: 'QuickBooks', desc: 'QuickBooks Online — invoices and expenses.', emoji: '📊', color: '#2CA01C', tier: 'pro' },
  ],
  payments: [
    { id: 'stripe', name: 'Stripe', desc: 'Track Stripe balance, transactions, and payouts.', emoji: '💳', color: '#635BFF', tier: 'pro' },
    { id: 'paypal', name: 'PayPal', desc: 'PayPal Business — transactions and payout tracking.', emoji: '💰', color: '#003087', tier: 'pro' },
  ],
};

// Credentials form fields per integration
const CRED_FIELDS = {
  amazon: [
    { key: 'client_id', label: 'SP-API Client ID', type: 'text' },
    { key: 'client_secret', label: 'SP-API Client Secret', type: 'password' },
    { key: 'refresh_token', label: 'Refresh Token', type: 'password' },
  ],
  ebay: [
    { key: 'client_id', label: 'OAuth Client ID', type: 'text' },
    { key: 'client_secret', label: 'OAuth Client Secret', type: 'password' },
    { key: 'dev_id', label: 'Developer ID', type: 'text' },
  ],
  shopify: [
    { key: 'shop', label: 'Shop Domain (e.g. mystore.myshopify.com)', type: 'text' },
    { key: 'access_token', label: 'Access Token', type: 'password' },
  ],
  woocommerce: [
    { key: 'url', label: 'Store URL', type: 'text', placeholder: 'https://shop.example.com' },
    { key: 'consumer_key', label: 'Consumer Key', type: 'text' },
    { key: 'consumer_secret', label: 'Consumer Secret', type: 'password' },
  ],
  etsy: [
    { key: 'api_key', label: 'Etsy API Key', type: 'text' },
    { key: 'api_secret', label: 'API Secret', type: 'password' },
  ],
  stripe: [{ key: 'api_key', label: 'Secret Key (sk_live_...)', type: 'password' }],
  xero: [
    { key: 'client_id', label: 'Client ID', type: 'text' },
    { key: 'client_secret', label: 'Client Secret', type: 'password' },
  ],
  royal_mail: [
    { key: 'client_id', label: 'API Key', type: 'text' },
    { key: 'client_secret', label: 'API Secret', type: 'password' },
  ],
  dpd: [
    { key: 'client_id', label: 'Client ID', type: 'text' },
    { key: 'client_secret', label: 'API Secret', type: 'password' },
  ],
  default: [
    { key: 'api_key', label: 'API Key', type: 'text' },
    { key: 'api_secret', label: 'API Secret', type: 'password' },
  ],
};

const TIER_COLORS = { core: 'var(--accent)', standard: 'var(--text2)', pro: '#a855f7' };
const TIER_LABELS = { core: 'Included', standard: 'Standard', pro: 'Pro' };

export default function Integrations() {
  const [activeCategory, setActiveCategory] = useState('marketplace')
  const [channels, setChannels] = useState([]) // {id, channel_type, display_name, active}
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(null) // plugin id being configured
  const [config, setConfig] = useState({})
  const [connecting, setConnecting] = useState(false)
  const [displayName, setDisplayName] = useState('')
  const toast = useToast()

  const loadChannels = useCallback(() => {
    return api.channels().then(d => {
      setChannels(d.channels || [])
    })
  }, [])

  useEffect(() => {
    Promise.all([loadChannels()]).finally(() => setLoading(false))
  }, [loadChannels])

  function getConnectedChannel(pluginId) {
    return channels.find(ch => ch.channel_type === pluginId)
  }

  async function handleConnect(pluginId) {
    setConnecting(true)
    try {
      const creds = {}
      const fields = CRED_FIELDS[pluginId] || CRED_FIELDS.default
      fields.forEach(f => { if (config[f.key]) creds[f.key] = config[f.key] })
      await api.createChannel({ channel_type: pluginId, display_name: displayName || pluginId, credentials: creds })
      await loadChannels()
      setShowModal(null)
      setConfig({})
      setDisplayName('')
      toast('Connected successfully', 'success')
    } catch (e) {
      toast(e?.error || 'Failed to connect', 'error')
    } finally {
      setConnecting(false)
    }
  }

  async function handleDisconnect(channelId) {
    if (!window.confirm('Remove this integration? You can reconnect anytime.')) return
    try {
      await api.deleteChannel(channelId)
      await loadChannels()
      toast('Disconnected', 'success')
    } catch (e) {
      toast(e?.error || 'Failed to disconnect', 'error')
    }
  }

  const items = CATALOG[activeCategory] || []
  const category = CATEGORIES.find(c => c.id === activeCategory)
  const CatIcon = category?.icon || LayoutGrid

  return (
    <div className="page">
      <div className="page-header">
        <div className="page-title-row">
          <h1 className="page-title">Integrations</h1>
          <p className="page-subtitle">{channels.length} connected · Click any integration to connect or configure</p>
        </div>
      </div>

      <div className="integrations-layout">
        {/* Category sidebar */}
        <div className="integrations-sidebar">
          {CATEGORIES.map(cat => {
            const Icon = cat.icon
            const count = items.filter(i => getConnectedChannel(i.id)).length
            return (
              <button
                key={cat.id}
                className={`cat-btn ${activeCategory === cat.id ? 'active' : ''}`}
                onClick={() => setActiveCategory(cat.id)}
              >
                <Icon size={15} />
                <span style={{ flex: 1 }}>{cat.label}</span>
                {count > 0 && (
                  <span style={{ background: 'var(--accent)', color: '#fff', borderRadius: 10, fontSize: 10, fontWeight: 700, padding: '1px 6px', minWidth: 18, textAlign: 'center' }}>
                    {count}
                  </span>
                )}
              </button>
            )
          })}
        </div>

        {/* Content */}
        <div className="integrations-content">
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
            <Icon size={20} style={{ opacity: 0.6 }} />
            <h2 style={{ fontSize: 16, fontWeight: 700 }}>{category?.label}</h2>
            <span style={{ fontSize: 12, color: 'var(--text3)' }}>({items.length})</span>
          </div>

          {loading ? (
            <div className="integrations-grid">
              {[1,2,3,4].map(i => (
                <div key={i} className="integration-card">
                  <div className="skeleton" style={{ height: 44, width: 44, borderRadius: 10, marginBottom: 12 }} />
                  <div className="skeleton" style={{ height: 14, width: '60%', marginBottom: 6 }} />
                  <div className="skeleton" style={{ height: 12, width: '90%' }} />
                </div>
              ))}
            </div>
          ) : (
            <div className="integrations-grid">
              {items.map(plugin => {
                const connectedCh = getConnectedChannel(plugin.id)
                const credFields = CRED_FIELDS[plugin.id] || CRED_FIELDS.default
                return (
                  <div key={plugin.id} className="integration-card">
                    <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12, marginBottom: 10 }}>
                      <div style={{
                        width: 44, height: 44, borderRadius: 10, background: plugin.color,
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        fontSize: 20, flexShrink: 0
                      }}>
                        {plugin.emoji}
                      </div>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 7, marginBottom: 2, flexWrap: 'wrap' }}>
                          <span style={{ fontSize: 14, fontWeight: 700 }}>{plugin.name}</span>
                          <span style={{ fontSize: 10, fontWeight: 700, padding: '1px 5px', borderRadius: 3, background: TIER_COLORS[plugin.tier] + '20', color: TIER_COLORS[plugin.tier] }}>
                            {TIER_LABELS[plugin.tier]}
                          </span>
                        </div>
                        {connectedCh ? (
                          <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                            <CheckCircle size={12} style={{ color: 'var(--green)' }} />
                            <span style={{ fontSize: 11, color: 'var(--green)', fontWeight: 600 }}>Connected</span>
                          </div>
                        ) : (
                          <span style={{ fontSize: 11, color: 'var(--text3)' }}>Not connected</span>
                        )}
                      </div>
                    </div>
                    <p style={{ fontSize: 12, color: 'var(--text2)', lineHeight: 1.5, marginBottom: 12 }}>{plugin.desc}</p>
                    {connectedCh ? (
                      <div style={{ display: 'flex', gap: 7 }}>
                        <button
                          className="btn btn-ghost btn-sm"
                          style={{ flex: 1 }}
                          onClick={() => { setShowModal(plugin.id); setDisplayName(connectedCh.display_name || ''); setConfig({}) }}
                        >
                          Configure
                        </button>
                        <button
                          className="btn btn-danger btn-sm"
                          onClick={() => handleDisconnect(connectedCh.id)}
                        >
                          <Trash2 size={12} />
                        </button>
                      </div>
                    ) : (
                      <button
                        className="btn btn-sm"
                        onClick={() => { setShowModal(plugin.id); setDisplayName(plugin.name); setConfig({}) }}
                        style={{ width: '100%', justifyContent: 'center', background: plugin.color, color: '#000', fontWeight: 700 }}
                      >
                        <Plus size={13} /> Connect
                      </button>
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </div>

      {/* Connect / Configure Modal */}
      {showModal && (() => {
        const plugin = items.find(i => i.id === showModal)
        if (!plugin) return null
        const connectedCh = getConnectedChannel(plugin.id)
        const isEditing = !!connectedCh
        const credFields = CRED_FIELDS[plugin.id] || CRED_FIELDS.default
        return (
          <div className="modal-overlay" onClick={e => e.target === e.currentTarget && setShowModal(null)}>
            <div className="modal">
              <div className="modal-header">
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <div style={{ width: 32, height: 32, borderRadius: 8, background: plugin.color, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 16 }}>
                    {plugin.emoji}
                  </div>
                  <div>
                    <h3 style={{ fontSize: 15, fontWeight: 700 }}>{isEditing ? 'Configure' : 'Connect'} {plugin.name}</h3>
                    {isEditing && <span style={{ fontSize: 11, color: 'var(--green)' }}>Connected</span>}
                  </div>
                </div>
                <button className="modal-close" onClick={() => setShowModal(null)}>✕</button>
              </div>
              <div className="modal-body">
                <div className="form-group">
                  <label className="form-label">Display Name</label>
                  <input
                    className="form-input"
                    value={displayName}
                    onChange={e => setDisplayName(e.target.value)}
                    placeholder={`e.g. ${plugin.name} UK Store`}
                  />
                </div>
                {credFields.map(field => (
                  <div key={field.key} className="form-group">
                    <label className="form-label">{field.label}</label>
                    <input
                      type={field.type}
                      className="form-input"
                      value={config[field.key] || ''}
                      onChange={e => setConfig({ ...config, [field.key]: e.target.value })}
                      placeholder={field.placeholder}
                      style={{ fontFamily: field.type === 'password' ? 'inherit' : 'monospace' }}
                    />
                  </div>
                ))}
              </div>
              <div className="modal-footer">
                <button className="btn btn-secondary" onClick={() => setShowModal(null)}>Cancel</button>
                <button
                  className="btn btn-primary"
                  onClick={() => handleConnect(plugin.id)}
                  disabled={connecting}
                  style={{ background: plugin.color, color: '#000' }}
                >
                  {connecting ? 'Connecting...' : isEditing ? 'Save Changes' : 'Connect'}
                </button>
              </div>
            </div>
          </div>
        )
      })()}
    </div>
  )
}
