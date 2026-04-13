import React, { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { StatusBadge, ChannelBadge } from '../components/shared'
import DataTable from '../components/DataTable'
import { useToast } from '../App'
import { CheckSquare, Square, RefreshCw } from 'lucide-react'

const CHANNEL_OPTIONS = [
  { id: '', label: 'All Channels' },
  { id: 'amazon', label: 'Amazon' },
  { id: 'ebay', label: 'eBay' },
  { id: 'woocommerce', label: 'WooCommerce' },
  { id: 'shopify', label: 'Shopify' },
  { id: 'tiktok', label: 'TikTok Shop' },
  { id: 'etsy', label: 'Etsy' },
  { id: 'mirakl', label: 'Mirakl' },
]

const COLUMNS = [
  {
    key: 'order_number', label: 'Order', width: 130, sortable: true,
    render: v => <span className="mono" style={{ fontSize: 11, fontWeight: 600 }}>{v}</span>,
  },
  {
    key: 'channel', label: 'Channel', width: 100, sortable: true,
    render: v => <ChannelBadge channel={v} />,
  },
  {
    key: 'customer_name', label: 'Customer', sortable: true,
    render: v => <span style={{ maxWidth: 150, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', display: 'block' }}>{v}</span>,
  },
  {
    key: 'total', label: 'Total', width: 90, sortable: true,
    render: v => <span className="mono">£{(v || 0).toFixed(2)}</span>,
  },
  {
    key: 'status', label: 'Status', width: 110, sortable: true,
    render: v => <StatusBadge status={v} />,
  },
  {
    key: 'order_date', label: 'Date', width: 100, sortable: true,
    render: v => v ? new Date(v).toLocaleDateString() : '—',
  },
  {
    key: 'tracking_number', label: 'Tracking', sortable: true,
    render: v => <span className="mono text-muted" style={{ fontSize: 11 }}>{v || '—'}</span>,
  },
]

export default function Orders() {
  const [orders, setOrders] = useState([])
  const [loading, setLoading] = useState(true)
  const [filters, setFilters] = useState({ channel: '', status: '', search: '', page: 1 })
  const [selectedIds, setSelectedIds] = useState(new Set())
  const [total, setTotal] = useState(0)
  const [pages, setPages] = useState(1)
  const navigate = useNavigate()
  const toast = useToast()

  const load = useCallback(() => {
    setLoading(true)
    const params = {}
    if (filters.channel) params.channel = filters.channel
    if (filters.status) params.status = filters.status
    if (filters.search) params.search = filters.search
    params.page = filters.page
    api.orders(params).then(d => {
      setOrders(d.orders || [])
      setTotal(d.total || 0)
      setPages(d.pages || 1)
      setSelectedIds(prev => {
        const next = new Set()
        prev.forEach(id => { if (d.orders?.some(o => o.id === id)) next.add(id) })
        return next
      })
    }).finally(() => setLoading(false))
  }, [filters])

  useEffect(() => { load() }, [load])

  const toggleSelect = (id, e) => {
    e?.stopPropagation()
    setSelectedIds(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const toggleAll = () => {
    if (selectedIds.size === orders.length) setSelectedIds(new Set())
    else setSelectedIds(new Set(orders.map(o => o.id)))
  }

  const handleBulkStatus = async (status) => {
    const ids = Array.from(selectedIds)
    try {
      await Promise.all(ids.map(id => api.updateOrder(id, { status })))
      toast(`${ids.length} orders marked as ${status}`, 'success')
      setSelectedIds(new Set())
      load()
    } catch {
      toast('Failed to update orders', 'error')
    }
  }

  const handleSync = async () => {
    try {
      await api.syncOrders()
      toast('Orders synced', 'success')
      load()
    } catch {
      toast('Sync failed', 'error')
    }
  }

  return (
    <div className="page">
      <div className="page-header">
        <div className="page-title-row">
          <h1 className="page-title">Orders</h1>
          <p className="page-subtitle">
            {total > 0 ? `${total} orders` : 'Manage your orders'} · Drag columns to reorder · Click headers to sort
          </p>
        </div>
        <div className="page-actions">
          <button className="btn btn-secondary btn-sm" onClick={handleSync} disabled={loading}>
            <RefreshCw size={13} /> Sync
          </button>
        </div>
      </div>

      {/* Bulk Actions Bar */}
      {selectedIds.size > 0 && (
        <div style={{
          display: 'flex', alignItems: 'center', gap: 10, padding: '10px 20px',
          background: 'var(--accent-light)', borderBottom: '1px solid var(--border)',
          flexWrap: 'wrap',
        }}>
          <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--accent)' }}>
            {selectedIds.size} selected
          </span>
          <button className="btn btn-sm" style={{ background: 'var(--accent)', color: '#fff' }} onClick={() => handleBulkStatus('shipped')}>
            Mark Shipped
          </button>
          <button className="btn btn-secondary btn-sm" onClick={() => handleBulkStatus('delivered')}>
            Mark Delivered
          </button>
          <button className="btn btn-danger btn-sm" onClick={() => handleBulkStatus('cancelled')}>
            Cancel
          </button>
          <button className="btn btn-ghost btn-sm" onClick={toggleAll} style={{ marginLeft: 'auto' }}>
            Clear selection
          </button>
        </div>
      )}

      {/* Filters */}
      <div className="filters-bar">
        <input
          className="input"
          placeholder="Search by order #, customer..."
          value={filters.search}
          onChange={e => setFilters({ ...filters, search: e.target.value, page: 1 })}
          style={{ width: 200 }}
        />
        <select className="form-select" value={filters.channel} onChange={e => setFilters({ ...filters, channel: e.target.value, page: 1 })} style={{ width: 'auto', minWidth: 130 }}>
          {CHANNEL_OPTIONS.map(c => <option key={c.id} value={c.id}>{c.label}</option>)}
        </select>
        <select className="form-select" value={filters.status} onChange={e => setFilters({ ...filters, status: e.target.value, page: 1 })} style={{ width: 'auto', minWidth: 130 }}>
          <option value="">All Statuses</option>
          <option value="pending">Pending</option>
          <option value="shipped">Shipped</option>
          <option value="delivered">Delivered</option>
          <option value="cancelled">Cancelled</option>
        </select>
      </div>

      {/* Table */}
      <div className="card" style={{ margin: '0 16px 16px' }}>
        <DataTable
          columns={COLUMNS}
          data={orders}
          loading={loading}
          emptyMessage="No orders found"
          onRowClick={row => navigate(`/orders/${row.id}`)}
        />

        {/* Pagination */}
        {pages > 1 && (
          <div className="pagination">
            <button
              className="btn btn-secondary btn-sm"
              onClick={() => setFilters(f => ({ ...f, page: Math.max(1, f.page - 1) }))}
              disabled={filters.page === 1}
            >
              ← Prev
            </button>
            <span className="pagination-info">Page {filters.page} of {pages}</span>
            <button
              className="btn btn-secondary btn-sm"
              onClick={() => setFilters(f => ({ ...f, page: f.page + 1 }))}
              disabled={filters.page >= pages}
            >
              Next →
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
