import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { DataTable, StatusBadge, ChannelBadge, PageHeader, Pagination } from '../components/shared'

export default function Orders() {
  const [data, setData] = useState({ orders: [], total: 0, page: 1, pages: 1 })
  const [loading, setLoading] = useState(true)
  const [filters, setFilters] = useState({ channel: '', status: '', search: '', page: 1 })
  const navigate = useNavigate()

  const load = () => {
    setLoading(true)
    const params = {}
    if (filters.channel) params.channel = filters.channel
    if (filters.status) params.status = filters.status
    if (filters.search) params.search = filters.search
    params.page = filters.page
    api.orders(params).then(setData).finally(() => setLoading(false))
  }

  useEffect(load, [filters])

  const columns = [
    { key: 'order_number', label: 'Order #', style: { fontFamily: 'JetBrains Mono, monospace', fontSize: 12 } },
    { key: 'channel', label: 'Channel', render: r => <ChannelBadge channel={r.channel} /> },
    { key: 'customer_name', label: 'Customer' },
    { key: 'total', label: 'Total', render: r => <span className="mono">£{r.total.toFixed(2)}</span> },
    { key: 'status', label: 'Status', render: r => <StatusBadge status={r.status} /> },
    { key: 'order_date', label: 'Date', render: r => r.order_date ? new Date(r.order_date).toLocaleDateString() : '—' },
    { key: 'tracking_number', label: 'Tracking', render: r => r.tracking_number ? <span className="mono text-xs">{r.tracking_number}</span> : '—' },
  ]

  return (
    <div className="page">
      <PageHeader title="Orders">
        <button className="btn-primary" onClick={() => { api.syncOrders(); load() }}>Sync Orders</button>
      </PageHeader>

      <div className="filters-bar">
        <input
          className="input"
          placeholder="Search orders..."
          value={filters.search}
          onChange={e => setFilters({ ...filters, search: e.target.value, page: 1 })}
        />
        <select className="input" value={filters.channel} onChange={e => setFilters({ ...filters, channel: e.target.value, page: 1 })}>
          <option value="">All Channels</option>
          <option value="amazon">Amazon</option>
          <option value="ebay">eBay</option>
          <option value="woocommerce">WooCommerce</option>
          <option value="shopify">Shopify</option>
        </select>
        <select className="input" value={filters.status} onChange={e => setFilters({ ...filters, status: e.target.value, page: 1 })}>
          <option value="">All Statuses</option>
          <option value="pending">Pending</option>
          <option value="shipped">Shipped</option>
          <option value="delivered">Delivered</option>
          <option value="cancelled">Cancelled</option>
        </select>
      </div>

      <div className="card">
        <DataTable
          columns={columns}
          data={data.orders}
          loading={loading}
          onRowClick={row => navigate(`/orders/${row.id}`)}
          emptyMessage="No orders found"
        />
        <Pagination page={data.page} pages={data.pages} onPageChange={p => setFilters({ ...filters, page: p })} />
      </div>
    </div>
  )
}
