import { useState, useEffect } from 'react';
import { api } from '../api/client';

export default function Channels() {
  const [channels, setChannels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [newChannel, setNewChannel] = useState({ channel_type: 'amazon', display_name: '', credentials: '{}' });

  useEffect(() => { loadChannels(); }, []);

  async function loadChannels() {
    try {
      const data = await api.get('/api/channels');
      setChannels(data);
    } finally {
      setLoading(false);
    }
  }

  async function addChannel() {
    let creds = {};
    try { creds = JSON.parse(newChannel.credentials || '{}'); } catch(e) {}
    await api.createChannel({ channel_type: newChannel.channel_type, display_name: newChannel.display_name, credentials: creds });
    setShowAdd(false);
    setNewChannel({ channel_type: 'amazon', display_name: '', credentials: '{}' });
    loadChannels();
  }

  async function toggleChannel(id, currentActive) {
    await api.post(`/api/channels/${id}/toggle`, { active: !currentActive });
    loadChannels();
  }

  async function syncChannel(id) {
    await api.post(`/api/channels/${id}/sync`, {});
    loadChannels();
  }

  const channelTypes = [
    { id: 'amazon', name: 'Amazon UK', color: '#ff9900', desc: 'SP-API integration for Amazon orders and inventory' },
    { id: 'ebay', name: 'eBay UK', color: '#e53238', desc: 'eBay OAuth for order sync and tracking updates' },
    { id: 'woocommerce', name: 'WooCommerce', color: '#9b5c8f', desc: 'WooCommerce REST API for your self-hosted store' },
    { id: 'shopify', name: 'Shopify', color: '#96bf48', desc: 'Shopify Admin API for orders and inventory' },
    { id: 'tiktok', name: 'TikTok Shop', color: '#ff0050', desc: 'TikTok Shop API for social commerce' },
    { id: 'mirakl', name: 'B&Q Marketplace', color: '#003087', desc: 'Mirakl Connect for B&Q dropship orders' },
    { id: 'noon', name: 'Noon UAE', color: '#f5a623', desc: 'Noon API for Middle East marketplace' },
  ];

  return (
    <div style={{ padding: '24px', maxWidth: '900px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <h1 style={{ fontSize: '20px', fontWeight: '800', color: 'var(--gold)', marginBottom: '4px' }}>Channels</h1>
          <p style={{ color: 'var(--text2)', fontSize: '13px' }}>Connect and manage your marketplace integrations</p>
        </div>
        <button
          onClick={() => setShowAdd(true)}
          style={{ background: 'var(--gold)', color: '#000', border: 'none', borderRadius: '8px', padding: '9px 18px', fontSize: '13px', fontWeight: '700', cursor: 'pointer' }}
        >
          + Add Channel
        </button>
      </div>

      {loading ? (
        <div style={{ color: 'var(--text3)', fontSize: '13px', padding: '40px', textAlign: 'center' }}>Loading channels...</div>
      ) : channels.length === 0 ? (
        <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '12px', padding: '60px 40px', textAlign: 'center' }}>
          <div style={{ fontSize: '40px', marginBottom: '12px', opacity: 0.3 }}>🔌</div>
          <div style={{ fontSize: '15px', fontWeight: '600', color: 'var(--text2)', marginBottom: '8px' }}>No channels connected</div>
          <div style={{ fontSize: '13px', color: 'var(--text3)', marginBottom: '20px' }}>Connect your first marketplace to start syncing orders</div>
          <button onClick={() => setShowAdd(true)} style={{ background: 'var(--gold)', color: '#000', border: 'none', borderRadius: '8px', padding: '9px 18px', fontSize: '13px', fontWeight: '700', cursor: 'pointer' }}>
            + Add Your First Channel
          </button>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {channels.map(ch => {
            const meta = channelTypes.find(t => t.id === ch.channel_type) || {};
            return (
              <div key={ch.id} style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '12px', padding: '16px 20px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                  <div style={{ width: '40px', height: '40px', borderRadius: '8px', background: meta.color || '#444', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '18px', flexShrink: 0 }}>
                    {ch.channel_type === 'amazon' ? '📦' : ch.channel_type === 'ebay' ? '🏷️' : ch.channel_type === 'woocommerce' ? '🛒' : ch.channel_type === 'tiktok' ? '🎵' : ch.channel_type === 'mirakl' ? '🏪' : '📡'}
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: '14px', fontWeight: '700', color: 'var(--text)', marginBottom: '2px' }}>{ch.display_name || meta.name || ch.channel_type}</div>
                    <div style={{ fontSize: '12px', color: 'var(--text3)' }}>{meta.desc || ch.channel_type}</div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <div style={{ width: '7px', height: '7px', borderRadius: '50%', background: ch.active ? 'var(--green)' : 'var(--text3)', boxShadow: ch.active ? '0 0 6px var(--green)' : 'none' }} />
                      <span style={{ fontSize: '12px', color: ch.active ? 'var(--green)' : 'var(--text3)' }}>{ch.active ? 'Active' : 'Inactive'}</span>
                    </div>
                    <button onClick={() => syncChannel(ch.id)} style={{ background: 'var(--bg4)', color: 'var(--text2)', border: '1px solid var(--border)', borderRadius: '7px', padding: '6px 12px', fontSize: '12px', cursor: 'pointer' }}>↻ Sync</button>
                    <button onClick={() => toggleChannel(ch.id, ch.active)} style={{ background: 'var(--bg4)', color: 'var(--text2)', border: '1px solid var(--border)', borderRadius: '7px', padding: '6px 12px', fontSize: '12px', cursor: 'pointer' }}>
                      {ch.active ? 'Disable' : 'Enable'}
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Add Channel Modal */}
      {showAdd && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)', zIndex: 200, display: 'flex', alignItems: 'center', justifyContent: 'center' }} onClick={e => e.target === e.currentTarget && setShowAdd(false)}>
          <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '16px', width: '480px', padding: '24px' }}>
            <div style={{ fontSize: '16px', fontWeight: '700', color: 'var(--text)', marginBottom: '20px' }}>Add Channel</div>
            <div style={{ marginBottom: '14px' }}>
              <label style={{ fontSize: '12px', fontWeight: '600', color: 'var(--text3)', display: 'block', marginBottom: '6px' }}>Channel Type</label>
              <select value={newChannel.channel_type} onChange={e => setNewChannel({ ...newChannel, channel_type: e.target.value })} style={{ width: '100%', background: 'var(--bg3)', border: '1px solid var(--border)', borderRadius: '8px', padding: '9px 12px', fontSize: '13px', color: 'var(--text)', outline: 'none' }}>
                {channelTypes.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
              </select>
            </div>
            <div style={{ marginBottom: '14px' }}>
              <label style={{ fontSize: '12px', fontWeight: '600', color: 'var(--text3)', display: 'block', marginBottom: '6px' }}>Display Name (optional)</label>
              <input type="text" value={newChannel.display_name} onChange={e => setNewChannel({ ...newChannel, display_name: e.target.value })} placeholder="e.g. Amazon UK Store 1" style={{ width: '100%', background: 'var(--bg3)', border: '1px solid var(--border)', borderRadius: '8px', padding: '9px 12px', fontSize: '13px', color: 'var(--text)', outline: 'none' }} />
            </div>
            <div style={{ marginBottom: '20px' }}>
              <label style={{ fontSize: '12px', fontWeight: '600', color: 'var(--text3)', display: 'block', marginBottom: '6px' }}>Credentials (JSON)</label>
              <textarea value={newChannel.credentials} onChange={e => setNewChannel({ ...newChannel, credentials: e.target.value })} placeholder='{"api_key": "...", "marketplace_id": "..."}' style={{ width: '100%', background: 'var(--bg3)', border: '1px solid var(--border)', borderRadius: '8px', padding: '9px 12px', fontSize: '13px', color: 'var(--text)', outline: 'none', minHeight: '80px', resize: 'vertical', fontFamily: 'monospace' }} />
            </div>
            <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
              <button onClick={() => setShowAdd(false)} style={{ background: 'var(--bg4)', color: 'var(--text2)', border: '1px solid var(--border)', borderRadius: '8px', padding: '9px 18px', fontSize: '13px', cursor: 'pointer' }}>Cancel</button>
              <button onClick={addChannel} style={{ background: 'var(--gold)', color: '#000', border: 'none', borderRadius: '8px', padding: '9px 18px', fontSize: '13px', fontWeight: '700', cursor: 'pointer' }}>Add Channel</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
