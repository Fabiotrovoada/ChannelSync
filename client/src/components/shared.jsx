import React from 'react'

// --- Skeleton Loader ---
export function Skeleton({ width = '100%', height = 16, style = {} }) {
  return (
    <div className="skeleton" style={{ width, height, borderRadius: 4, ...style }} />
  )
}

export function SkeletonRows({ count = 5 }) {
  return Array.from({ length: count }, (_, i) => (
    <div key={i} style={{ display: 'flex', gap: 12, marginBottom: 8 }}>
      <Skeleton width={60} height={14} />
      <Skeleton width="40%" height={14} />
      <Skeleton width={80} height={14} />
      <Skeleton width={60} height={14} />
    </div>
  ))
}

// --- KPI Card ---
export function KPICard({ label, value, delta, loading, prefix = '' }) {
  if (loading) {
    return (
      <div className="kpi-card">
        <Skeleton height={26} width={70} />
        <Skeleton height={11} width={90} style={{ marginTop: 6 }} />
      </div>
    )
  }
  return (
    <div className="kpi-card">
      <div className="kpi-value">{prefix}{typeof value === 'number' ? value.toLocaleString() : value ?? '—'}</div>
      <div className="kpi-label">{label}</div>
      {delta !== undefined && (
        <div className={`kpi-delta ${delta >= 0 ? 'delta-up' : 'delta-down'}`}>
          {delta >= 0 ? '↑' : '↓'} {Math.abs(delta)}%
        </div>
      )}
    </div>
  )
}

// --- Status Badge ---
const STATUS_COLORS = {
  pending: 'var(--orange)',
  shipped: 'var(--green)',
  delivered: 'var(--green)',
  cancelled: 'var(--red)',
  open: 'var(--blue)',
  resolved: '#4ade80',
  draft: 'var(--text3)',
  sent: 'var(--orange)',
  received: 'var(--green)',
  'partially_received': 'var(--orange)',
  active: 'var(--green)',
  inactive: 'var(--text3)',
}

export function StatusBadge({ status }) {
  const color = STATUS_COLORS[status] || 'var(--text2)'
  return (
    <span className="status-badge" style={{ color, borderColor: color }}>
      {status}
    </span>
  )
}

// --- Channel Badge ---
const CHANNEL_STYLES = {
  amazon: { bg: '#ff9900', color: '#000' },
  ebay: { bg: '#e53238', color: '#fff' },
  woocommerce: { bg: '#9b5c8f', color: '#fff' },
  shopify: { bg: '#96bf48', color: '#000' },
  tiktok: { bg: '#ff0050', color: '#fff' },
  mirakl: { bg: '#003087', color: '#fff' },
}

export function ChannelBadge({ channel }) {
  const style = CHANNEL_STYLES[channel] || { bg: 'var(--bg4)', color: 'var(--text)' }
  return (
    <span className="channel-badge" style={{ background: style.bg, color: style.color }}>
      {channel}
    </span>
  )
}

// --- Data Table ---
export function DataTable({ columns, data, loading, onRowClick, emptyMessage = 'No data' }) {
  if (loading) {
    return <div className="data-table-wrap"><SkeletonRows count={8} /></div>
  }

  if (!data || data.length === 0) {
    return <div className="data-table-empty">{emptyMessage}</div>
  }

  return (
    <div className="data-table-wrap">
      <table className="data-table">
        <thead>
          <tr>
            {columns.map(col => (
              <th key={col.key} style={col.style}>{col.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, i) => (
            <tr key={row.id || i} onClick={() => onRowClick?.(row)} className={onRowClick ? 'clickable' : ''}>
              {columns.map(col => (
                <td key={col.key} style={col.style}>
                  {col.render ? col.render(row) : row[col.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

// --- Modal ---
export function Modal({ open, onClose, title, children, width = 480 }) {
  if (!open) return null
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" style={{ maxWidth: width }} onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h3>{title}</h3>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>
        <div className="modal-body">{children}</div>
      </div>
    </div>
  )
}

// --- Page Header ---
export function PageHeader({ title, children }) {
  return (
    <div className="page-header">
      <h1 className="page-title">{title}</h1>
      <div className="page-actions">{children}</div>
    </div>
  )
}

// --- Pagination ---
export function Pagination({ page, pages, onPageChange }) {
  if (pages <= 1) return null
  return (
    <div className="pagination">
      <button className="btn-ghost btn-sm" disabled={page <= 1} onClick={() => onPageChange(page - 1)}>← Prev</button>
      <span className="pagination-info">Page {page} of {pages}</span>
      <button className="btn-ghost btn-sm" disabled={page >= pages} onClick={() => onPageChange(page + 1)}>Next →</button>
    </div>
  )
}
