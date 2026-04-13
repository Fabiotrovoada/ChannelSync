import React from 'react'

// ─── Skeleton ─────────────────────────────────────────────────────────────────
export function Skeleton({ width = '100%', height = 16, style = {} }) {
  return <div className="skeleton" style={{ width, height, borderRadius: 4, ...style }} />
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

// ─── KPI Card ──────────────────────────────────────────────────────────────────
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

// ─── Status Badge ──────────────────────────────────────────────────────────────
const STATUS_COLORS = {
  pending:   { color: '#d97706', bg: '#fffbeb' },
  shipped:   { color: '#059669', bg: '#ecfdf5' },
  delivered: { color: '#059669', bg: '#ecfdf5' },
  cancelled: { color: '#dc2626', bg: '#fef2f2' },
  open:      { color: '#2563eb', bg: '#eff6ff' },
  resolved:  { color: '#059669', bg: '#ecfdf5' },
  draft:     { color: '#6b7280', bg: '#f3f4f6' },
  sent:      { color: '#d97706', bg: '#fffbeb' },
  received:  { color: '#059669', bg: '#ecfdf5' },
  partially_received: { color: '#d97706', bg: '#fffbeb' },
  active:    { color: '#059669', bg: '#ecfdf5' },
  inactive:  { color: '#6b7280', bg: '#f3f4f6' },
}

export function StatusBadge({ status }) {
  const s = STATUS_COLORS[status] || { color: 'var(--text2)', bg: 'var(--surface2)' }
  return (
    <span
      className="status-badge"
      style={{ color: s.color, borderColor: s.color, background: s.bg }}
    >
      {status}
    </span>
  )
}

// ─── Channel Badge ─────────────────────────────────────────────────────────────
const CHANNEL_STYLES = {
  amazon:      { bg: '#FF9900', color: '#000' },
  ebay:        { bg: '#E53238', color: '#fff' },
  woocommerce: { bg: '#9B5C8F', color: '#fff' },
  shopify:     { bg: '#96BF48', color: '#000' },
  tiktok:      { bg: '#FF0050', color: '#fff' },
  mirakl:      { bg: '#003087', color: '#fff' },
  etsy:        { bg: '#F56400', color: '#fff' },
  walmart:     { bg: '#00464F', color: '#fff' },
  onbuy:       { bg: '#00B4E6', color: '#fff' },
  fruugo:      { bg: '#7B2D8E', color: '#fff' },
  royal_mail:  { bg: '#E60000', color: '#fff' },
  dpd:         { bg: '#E60000', color: '#fff' },
  evri:        { bg: '#00B4E6', color: '#fff' },
  dhl:         { bg: '#FFCC00', color: '#000' },
  ups:         { bg: '#351C15', color: '#fff' },
  fedex:       { bg: '#4D148C', color: '#fff' },
  yodel:       { bg: '#009A44', color: '#fff' },
  shipstation: { bg: '#0066CC', color: '#fff' },
  xero:        { bg: '#13B5EA', color: '#fff' },
  stripe:      { bg: '#635BFF', color: '#fff' },
  paypal:      { bg: '#003087', color: '#fff' },
}

export function ChannelBadge({ channel }) {
  const s = CHANNEL_STYLES[channel] || { bg: 'var(--surface2)', color: 'var(--text2)' }
  return (
    <span
      className="channel-badge"
      style={{ background: s.bg, color: s.color }}
    >
      {channel}
    </span>
  )
}

// ─── Modal ─────────────────────────────────────────────────────────────────────
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

// ─── Page Header ───────────────────────────────────────────────────────────────
export function PageHeader({ title, subtitle, actions }) {
  return (
    <div className="page-header">
      <div className="page-title-row">
        <h1 className="page-title">{title}</h1>
        {subtitle && <p className="page-subtitle">{subtitle}</p>}
      </div>
      {actions && <div className="page-actions">{actions}</div>}
    </div>
  )
}

// ─── Pagination ────────────────────────────────────────────────────────────────
export function Pagination({ page, pages, onPageChange }) {
  if (pages <= 1) return null
  return (
    <div className="pagination">
      <button
        className="btn btn-secondary btn-sm"
        disabled={page <= 1}
        onClick={() => onPageChange(page - 1)}
      >
        ← Prev
      </button>
      <span className="pagination-info">Page {page} of {pages}</span>
      <button
        className="btn btn-secondary btn-sm"
        disabled={page >= pages}
        onClick={() => onPageChange(page + 1)}
      >
        Next →
      </button>
    </div>
  )
}
