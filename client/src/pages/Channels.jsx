import { useState, useEffect } from 'react';
import { api } from '../api/client';

export default function Channels() {
  const [channels, setChannels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [newChannel, setNewChannel] = useState({ channel_type: 'amazon', display_name: '', credentials: '{}' });
  const [saving, setSaving] = useState(false);
  const toast = () => {};

  useEffect(() => { loadChannels(); }, []);

  async function loadChannels() {
    try {
      const data = await api.channels();
      setChannels(data.channels || []);
    } finally {
      setLoading(false);
    }
  }

  async function addChannel() {
    let creds = {};
    try { creds = JSON.parse(newChannel.credentials || '{}'); } catch(e) {}
    setSaving(true);
    try {
      await api.createChannel({ channel_type: newChannel.channel_type, display_name: newChannel.display_name, credentials: creds });
      setShowAdd(false);
      setNewChannel({ channel_type: 'amazon', display_name: '', credentials: '{}' });
      loadChannels();
    } finally {
      setSaving(false);
    }
  }

  async function toggleChannel(id, currentActive) {
    await api.updateChannel(id, { active: !currentActive });
    loadChannels();
  }

  async function syncChannel(id) {
    await api.syncChannel(id);
    loadChannels();
  }

  const channelTypes = [
    { id: 'amazon', name: 'Amazon UK', color: '#FF9900', emoji: '📦', desc: 'SP-API for Amazon orders and inventory' },
    { id: 'ebay', name: 'eBay UK', color: '#E53238', emoji: '🏷️', desc: 'eBay OAuth for order sync and tracking' },
    { id: 'woocommerce', name: 'WooCommerce', color: '#9B5C8F', emoji: '🛒', desc: 'WooCommerce REST API' },
    { id: 'shopify', name: 'Shopify', color: '#96BF48', emoji: '🛍️', desc: 'Shopify Admin API' },
    { id: 'tiktok', name: 'TikTok Shop', color: '#FF0050', emoji: '🎵', desc: 'TikTok Shop social commerce' },
    { id: 'mirakl', name: 'B&Q / Mirakl', color: '#003087', emoji: '🏪', desc: 'Mirakl Connect for dropship orders' },
    { id: 'noon', name: 'Noon UAE', color: '#F5A623', emoji: '🌍', desc: 'Noon API for Middle East marketplace' },
  ];

  return (
    <div className="page">
      <div className="page-header">
        <div className="page-title-row">
          <h1 className="page-title">Channels</h1>
          <p className="page-subtitle">Connect and manage your marketplace integrations</p>
        </div>
        <div className="page-actions">
          <button className="btn btn-primary" onClick={() => setShowAdd(true)}>+ Add Channel</button>
        </div>
      </div>

      <div className="section">
        {loading ? (
          <div className="empty-state">
            <div className="spinner" />
          </div>
        ) : channels.length === 0 ? (
          <div className="card">
            <div className="card-body" style={{ textAlign: 'center', padding: '60px 40px' }}>
              <div style={{ fontSize: 40, marginBottom: 12 }}>🔌</div>
              <div className="empty-state-title">No channels connected</div>
              <div className="empty-state-sub" style={{ marginBottom: 20 }}>Connect your first marketplace to start syncing orders</div>
              <button className="btn btn-primary" onClick={() => setShowAdd(true)}>+ Add Your First Channel</button>
            </div>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {channels.map(ch => {
              const meta = channelTypes.find(t => t.id === ch.channel_type) || { name: ch.channel_type, color: '#888', emoji: '📡', desc: '' };
              return (
                <div key={ch.id} className="card">
                  <div className="card-body" style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
                    <div style={{ width: 44, height: 44, borderRadius: 10, background: meta.color, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 20, flexShrink: 0 }}>
                      {meta.emoji}
                    </div>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text)', marginBottom: 2 }}>{ch.display_name || meta.name}</div>
                      <div style={{ fontSize: 12, color: 'var(--text2)' }}>{meta.desc}</div>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <div style={{ width: 8, height: 8, borderRadius: '50%', background: ch.active ? 'var(--green)' : 'var(--text3)' }} />
                        <span style={{ fontSize: 12, color: ch.active ? 'var(--green)' : 'var(--text3)', fontWeight: 600 }}>{ch.active ? 'Active' : 'Inactive'}</span>
                      </div>
                      <button className="btn btn-ghost btn-sm" onClick={() => syncChannel(ch.id)}>↻ Sync</button>
                      <button className="btn btn-ghost btn-sm" onClick={() => toggleChannel(ch.id, ch.active)}>
                        {ch.active ? 'Disable' : 'Enable'}
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Add Channel Modal */}
      {showAdd && (
        <div className="modal-overlay" onClick={e => e.target === e.currentTarget && setShowAdd(false)}>
          <div className="modal">
            <div className="modal-header">
              <h3>Add Channel</h3>
              <button className="modal-close" onClick={() => setShowAdd(false)}>✕</button>
            </div>
            <div className="modal-body">
              <div className="form-group">
                <label className="form-label">Channel Type</label>
                <select className="form-select" value={newChannel.channel_type} onChange={e => setNewChannel({ ...newChannel, channel_type: e.target.value })}>
                  {channelTypes.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Display Name (optional)</label>
                <input type="text" className="form-input" value={newChannel.display_name} onChange={e => setNewChannel({ ...newChannel, display_name: e.target.value })} placeholder="e.g. Amazon UK Store 1" />
              </div>
              <div className="form-group">
                <label className="form-label">Credentials (JSON)</label>
                <textarea className="form-textarea" value={newChannel.credentials} onChange={e => setNewChannel({ ...newChannel, credentials: e.target.value })} placeholder='{"api_key": "...", "marketplace_id": "..."}' style={{ fontFamily: 'monospace', fontSize: 12 }} />
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-ghost" onClick={() => setShowAdd(false)}>Cancel</button>
              <button className="btn btn-primary" onClick={addChannel} disabled={saving}>{saving ? 'Adding...' : 'Add Channel'}</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
