import { useState, useEffect } from 'react';
import { api } from '../api/client';

const ACTION_COLORS = {
  order_shipped: { color: 'var(--green)', bg: 'rgba(34,197,94,0.1)' },
  label_purchased: { color: 'var(--blue)', bg: 'rgba(59,130,246,0.1)' },
  reply_sent: { color: 'var(--gold)', bg: 'rgba(245,197,24,0.1)' },
  channel_sync: { color: 'var(--purple)', bg: 'rgba(168,85,247,0.1)' },
  login: { color: 'var(--text2)', bg: 'var(--bg3)' },
  order_created: { color: 'var(--orange)', bg: 'rgba(249,115,22,0.1)' },
  inventory_updated: { color: 'var(--green)', bg: 'rgba(34,197,94,0.1)' },
};

const ACTION_LABELS = {
  order_shipped: '📦 Order Shipped',
  label_purchased: '🏷️ Label Purchased',
  reply_sent: '💬 Reply Sent',
  channel_sync: '🔄 Channel Sync',
  login: '🔐 Login',
  order_created: '🛒 Order Created',
  inventory_updated: '📊 Inventory Updated',
  po_created: '📋 PO Created',
  po_received: '✅ PO Received',
};

export default function AuditLog() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const perPage = 50;

  useEffect(() => { loadLogs(); }, [page]);

  async function loadLogs() {
    setLoading(true);
    try {
      const data = await api.get(`/api/audit-log?page=${page}&limit=${perPage}`);
      if (Array.isArray(data)) {
        setLogs(data);
        setTotal(data.length);
      } else if (data.logs) {
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

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '20px', fontWeight: '800', color: 'var(--gold)', marginBottom: '4px' }}>Audit Log</h1>
        <p style={{ color: 'var(--text2)', fontSize: '13px' }}>All activity across your VendStack account</p>
      </div>

      <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '12px', overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr>
              {['Action', 'Details', 'Time'].map(h => (
                <th key={h} style={{ textAlign: 'left', padding: '10px 16px', fontSize: '11px', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.5px', color: 'var(--text3)', borderBottom: '1px solid var(--border)' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              Array.from({ length: 10 }).map((_, i) => (
                <tr key={i}>
                  {['80%', '40%', '60px'].map((w, j) => (
                    <td key={j} style={{ padding: '12px 16px' }}>
                      <div style={{ height: '14px', background: 'var(--bg3)', borderRadius: '4px', width: w, animation: 'pulse 1.5s infinite' }} />
                    </td>
                  ))}
                </tr>
              ))
            ) : logs.length === 0 ? (
              <tr>
                <td colSpan={3} style={{ padding: '60px 40px', textAlign: 'center', color: 'var(--text3)', fontSize: '13px' }}>No activity yet</td>
              </tr>
            ) : (
              logs.map(log => {
                const style = ACTION_COLORS[log.action] || { color: 'var(--text2)', bg: 'var(--bg3)' };
                const label = ACTION_LABELS[log.action] || log.action;
                const details = parseDetails(log.details);
                return (
                  <tr key={log.id} style={{ borderBottom: '1px solid var(--border)' }}>
                    <td style={{ padding: '12px 16px' }}>
                      <span style={{ fontSize: '11px', fontWeight: '700', padding: '3px 8px', borderRadius: '4px', background: style.bg, color: style.color }}>{label}</span>
                    </td>
                    <td style={{ padding: '12px 16px', fontSize: '13px', color: 'var(--text2)', maxWidth: '400px' }}>
                      {log.action === 'order_shipped' && details.order_number && `Order ${details.order_number} marked as shipped`}
                      {log.action === 'label_purchased' && details.carrier && `Label purchased via ${details.carrier}`}
                      {log.action === 'reply_sent' && details.message_id && `Reply sent to customer`}
                      {log.action === 'channel_sync' && details.channel && `Synced ${details.channel}`}
                      {log.action === 'login' && details.email && `Login by ${details.email}`}
                      {log.action === 'order_created' && details.order_number && `New order ${details.order_number}`}
                      {log.action === 'inventory_updated' && details.sku && `Stock updated for ${details.sku}`}
                      {(!log.details || log.action === 'login') && (details.email || label)}
                      {!['order_shipped', 'label_purchased', 'reply_sent', 'channel_sync', 'login', 'order_created', 'inventory_updated'].includes(log.action) && (details.message || log.details || '—')}
                    </td>
                    <td style={{ padding: '12px 16px', fontSize: '12px', color: 'var(--text3)', whiteSpace: 'nowrap' }}>{timeAgo(log.created_at)}</td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {total > perPage && (
        <div style={{ display: 'flex', justifyContent: 'center', gap: '8px', marginTop: '16px' }}>
          <button onClick={() => setPage(p => Math.max(1, p-1))} disabled={page === 1} style={{ background: 'var(--bg4)', color: page === 1 ? 'var(--text3)' : 'var(--text)', border: '1px solid var(--border)', borderRadius: '7px', padding: '7px 14px', fontSize: '12px', cursor: page === 1 ? 'not-allowed' : 'pointer' }}>← Prev</button>
          <span style={{ fontSize: '12px', color: 'var(--text3)', padding: '7px 12px' }}>Page {page}</span>
          <button onClick={() => setPage(p => p+1)} disabled={logs.length < perPage} style={{ background: 'var(--bg4)', color: 'var(--text)', border: '1px solid var(--border)', borderRadius: '7px', padding: '7px 14px', fontSize: '12px', cursor: 'pointer' }}>Next →</button>
        </div>
      )}
    </div>
  );
}
