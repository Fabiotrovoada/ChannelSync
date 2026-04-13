import React, { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { StatusBadge, ChannelBadge, Skeleton } from '../components/shared'
import { useToast } from '../App'
import { CheckSquare, Square, Package, RefreshCw } from 'lucide-react'

export default function Orders() {
  const [orders, setOrders] = useState([])
  const [loading, setLoading] = useState(true)
  const [filters, setFilters] = useState({ channel: '', status: '', search: '', page: 1 })
  const [selectedIds, setSelectedIds] = useState(new Set())
  const [total, setTotal] = useState(0)
  const [pages, setPages] = useState(1)
  const navigate = useNavigate()
  const toast = useToast()

  const CHANNELS = [
    { id: '', label: 'All Channels' },
    { id: 'amazon', label: 'Amazon' },
    { id: 'ebay', label: 'eBay' },
    { id: 'woocommerce', label: 'WooCommerce' },
    { id: 'shopify', label: 'Shopify' },
    { id: 'tiktok', label: 'TikTok Shop' },
    { id: 'etsy', label: 'Etsy' },
    { id: 'mirakl', label: 'Mirakl' },
  ]

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

  const toggleSelect = (id) => {
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
          <p className="page-subtitle">{total > 0 ? `${total} orders total` : 'Manage your orders'}</p>
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
          display: 'flex', alignItems: 'center', gap: 12, padding: '10px 20px',
          background: 'var(--accent-light)', borderBottom: '1px solid var(--border)',
          flexWrap: 'wrap'
        }}>
          <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--accent)' }}>
            {selectedIds.size} order{selectedIds.size !== 1 ? 's' : ''} selected
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
          <button className="btn btn-ghost btn-sm" onClick={() => setSelectedIds(new Set())} style={{ marginLeft: 'auto' }}>
            Clear
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
          {CHANNELS.map(c => <option key={c.id} value={c.id}>{c.label}</option>)}
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
      <div className="card" style={{ margin: '0 16px 16px', borderRadius: 'var(--radius)' }}>
        <div className="table-scroll">
          <table className="data-table">
            <thead>
              <tr>
                <th style={{ width: 40 }}>
                  <button onClick={toggleAll} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text3)', display: 'flex', padding: 4 }}>
                    {selectedIds.size === orders.length && orders.length > 0 ? <CheckSquare size={15} /> : <Square size={15} />}
                  </button>
                </th>
                <th>Order</th>
                <th>Channel</th>
                <th>Customer</th>
                <th>Total</th>
                <th>Status</th>
                <th>Date</th>
                <th>Tracking</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                Array.from({ length: 8 }).map((_, i) => (
                  <tr key={i}>
                    <td><Skeleton height={14} width={20} /></td>
                    {[120, 80, 120, 70, 70, 80, 100].map((w, j) => (
                      <td key={j}><Skeleton height={14} width={w} /></td>
                    ))}
                  </tr>
                ))
              ) : orders.length === 0 ? (
                <tr><td colSpan={8}><div className="empty-state"><Package size={32} style={{ opacity: 0.2, marginBottom: 8 }} /><div className="empty-state-title">No orders found</div></div></td></tr>
              ) : (
                orders.map(order => (
                  <tr
                    key={order.id}
                    className="clickable"
                    onClick={() => navigate(`/orders/${order.id}`)}
                    style={{ background: selectedIds.has(order.id) ? 'var(--accent-light)' : '' }}
                  >
                    <td onClick={e => { e.stopPropagation(); toggleSelect(order.id) }}>
                      <button style={{ background: 'none', border: 'none', cursor: 'pointer', color: selectedIds.has(order.id) ? 'var(--accent)' : 'var(--text3)', display: 'flex', padding: 4 }}>
                        {selectedIds.has(order.id) ? <CheckSquare size={15} /> : <Square size={15} />}
                      </button>
                    </td>
                    <td><span className="mono" style={{ fontSize: 11 }}>{order.order_number}</span></td>
                    <td><ChannelBadge channel={order.channel} /></td>
                    <td style={{ maxWidth: 140, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{order.customer_name}</td>
                    <td><span className="mono">£{order.total?.toFixed(2)}</span></td>
                    <td><StatusBadge status={order.status} /></td>
                    <td style={{ fontSize: 12, color: 'var(--text2)' }}>{order.order_date ? new Date(order.order_date).toLocaleDateString() : '—'}</td>
                    <td style={{ fontSize: 11, color: 'var(--text3)' }}>{order.tracking_number || '—'}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {pages > 1 && (
          <div className="pagination">
            <button className="btn btn-secondary btn-sm" onClick={() => setFilters(f => ({ ...f, page: Math.max(1, f.page - 1) }))} disabled={filters.page === 1}>
              ← Prev
            </button>
            <span className="pagination-info">Page {filters.page} of {pages}</span>
            <button className="btn btn-secondary btn-sm" onClick={() => setFilters(f => ({ ...f, page: f.page + 1 }))} disabled={filters.page >= pages}>
              Next →
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
