import { useState, useEffect } from 'react';
import { api } from '../api/client';
import { Activity } from 'lucide-react';

const ACTION_COLORS = {
  order_shipped: { color: 'var(--green)', bg: 'var(--green-light)' },
  label_purchased: { color: 'var(--accent)', bg: 'var(--accent-light)' },
  reply_sent: { color: 'var(--gold)', bg: 'var(--gold-light)' },
  channel_sync: { color: 'var(--purple)', bg: 'var(--purple-light)' },
  login: { color: 'var(--text2)', bg: 'var(--surface2)' },
  order_created: { color: 'var(--orange)', bg: 'var(--orange-light)' },
  inventory_updated: { color: 'var(--green)', bg: 'var(--green-light)' },
  order_update: { color: 'var(--accent)', bg: 'var(--accent-light)' },
  order_sync: { color: 'var(--purple)', bg: 'var(--purple-light)' },
  po_created: { color: 'var(--gold)', bg: 'var(--gold-light)' },
  po_received: { color: 'var(--green)', bg: 'var(--green-light)' },
};

const ACTION_LABELS = {
  order_shipped: 'Order Shipped',
  label_purchased: 'Label Purchased',
  reply_sent: 'Reply Sent',
  channel_sync: 'Channel Sync',
  login: 'Login',
  order_created: 'Order Created',
  order_update: 'Order Update',
  order_sync: 'Order Sync',
  inventory_updated: 'Inventory Updated',
  po_created: 'PO Created',
  po_received: 'PO Received',
};

export default function AuditLog() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);

  useEffect(() => { loadLogs(); }, [page]);

  async function loadLogs() {
    setLoading(true);
    try {
      const data = await api.auditLog({ page, limit: 50 });
      if (data.logs) {
        setLogs(data.logs);
        setTotal(data.total || 0);
      }
    } finally {
      setLoading(false);
    }
  }

  function timeAgo(iso) {
    if (!iso) return '';
    const d = new Date(iso);
    const diff = Math.floor((Date.now() - d.getTime()) / 1000);
    if (diff < 60) return 'Just now';
    if (diff < 3600) return `${Math.floor(diff/60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff/3600)}h ago`;
    return `${Math.floor(diff/86400)}d ago`;
  }

  function parseDetails(details) {
    try {
      if (typeof details === 'string') return JSON.parse(details);
      return details;
    } catch { return {}; }
  }

  function renderDetails(log) {
    const details = parseDetails(log.details_json || log.details);
    if (!details || Object.keys(details).length === 0) return '—';
    if (log.action === 'order_shipped') return `Order ${details.order || details.order_number} shipped via ${details.carrier || details.carrier_code}`;
    if (log.action === 'label_purchased') return `Label purchased for ${details.order || details.order_number} via ${details.carrier}`;
    if (log.action === 'reply_sent') return 'Reply sent to customer';
    if (log.action === 'channel_sync') return `Synced ${details.channel || details.channel_name}: ${details.orders || 0} orders`;
    if (log.action === 'login') return details.email ? `Login by ${details.email}` : 'New login';
    if (log.action === 'order_created') return `New order ${details.order_number || details.order}`;
    if (log.action === 'order_update') {
      const changes = details.changes || {};
      const keys = Object.keys(changes);
      return keys.length > 0 ? `Updated ${keys.join(', ')}` : 'Order updated';
    }
    if (log.action === 'order_sync') return `Synced ${details.channels || details.channels_count || 0} channels`;
    if (log.action === 'inventory_updated') return `Stock updated for ${details.sku}`;
    return details.message || `${log.action}`;
  }

  return (
    <div className="page">
      <div className="page-header">
        <div className="page-title-row">
          <h1 className="page-title">Audit Log</h1>
          <p className="page-subtitle">All activity across your ChannelSync account</p>
        </div>
        <div style={{ fontSize: 12, color: 'var(--text3)' }}>
          {total > 0 && `${total} events`}
        </div>
      </div>

      <div className="section">
        <div className="card">
          <div className="table-scroll">
            <table className="data-table">
              <thead>
                <tr>
                  <th style={{ width: 160 }}>Action</th>
                  <th>Details</th>
                  <th style={{ width: 100 }}>Time</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  Array.from({ length: 8 }).map((_, i) => (
                    <tr key={i}>
                      <td><div className="skeleton" style={{ height: 14, width: 100 }} /></td>
                      <td><div className="skeleton" style={{ height: 14, width: '60%' }} /></td>
                      <td><div className="skeleton" style={{ height: 14, width: 60 }} /></td>
                    </tr>
                  ))
                ) : logs.length === 0 ? (
                  <tr>
                    <td colSpan={3}>
                      <div className="empty-state">
                        <Activity size={36} style={{ opacity: 0.2, marginBottom: 8 }} />
                        <div className="empty-state-title">No activity yet</div>
                        <div className="empty-state-sub">Actions will appear here as you use ChannelSync</div>
                      </div>
                    </td>
                  </tr>
                ) : (
                  logs.map(log => {
                    const style = ACTION_COLORS[log.action] || { color: 'var(--text2)', bg: 'var(--surface2)' };
                    const label = ACTION_LABELS[log.action] || log.action;
                    return (
                      <tr key={log.id}>
                        <td>
                          <span style={{
                            fontSize: 10.5, fontWeight: 700, padding: '3px 8px', borderRadius: 4,
                            background: style.bg, color: style.color, display: 'inline-block',
                            textTransform: 'uppercase', letterSpacing: 0.4,
                          }}>
                            {label}
                          </span>
                        </td>
                        <td style={{ fontSize: 13, color: 'var(--text2)' }}>{renderDetails(log)}</td>
                        <td style={{ fontSize: 11.5, color: 'var(--text3)', whiteSpace: 'nowrap' }}>{timeAgo(log.created_at)}</td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>

        {total > 50 && (
          <div className="pagination">
            <button
              className="btn btn-secondary btn-sm"
              onClick={() => setPage(p => Math.max(1, p-1))}
              disabled={page === 1}
            >
              ← Prev
            </button>
            <span className="pagination-info">Page {page}</span>
            <button
              className="btn btn-secondary btn-sm"
              onClick={() => setPage(p => p+1)}
              disabled={logs.length < 50}
            >
              Next →
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
