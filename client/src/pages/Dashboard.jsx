import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { KPICard, DataTable, StatusBadge, ChannelBadge } from '../components/shared'

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    api.dashboardStats().then(setStats).finally(() => setLoading(false))
  }, [])

  const orderCols = [
    { key: 'order_number', label: 'Order', style: { fontFamily: 'JetBrains Mono, monospace', fontSize: 12 } },
    { key: 'channel', label: 'Channel', render: r => <ChannelBadge channel={r.channel} /> },
    { key: 'customer_name', label: 'Customer' },
    { key: 'total', label: 'Total', render: r => <span className="mono">£{r.total.toFixed(2)}</span> },
    { key: 'status', label: 'Status', render: r => <StatusBadge status={r.status} /> },
  ]

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Dashboard</h1>
        <div className="page-actions">
          <button className="btn-primary" onClick={() => api.syncOrders().then(() => window.location.reload())}>
            Sync All
          </button>
        </div>
      </div>

      <div className="kpi-grid">
        <KPICard label="Total Orders" value={stats?.total_orders} loading={loading} />
        <KPICard label="Revenue (Shipped)" value={stats?.revenue} loading={loading} prefix="£" />
        <KPICard label="Awaiting Shipment" value={stats?.awaiting_shipment} loading={loading} />
        <KPICard label="Shipped This Week" value={stats?.shipped_this_week} loading={loading} />
        <KPICard label="Open Messages" value={stats?.open_messages} loading={loading} />
        <KPICard label="Active Channels" value={stats?.active_channels} loading={loading} />
      </div>

      <div className="dashboard-grid">
        <div className="card">
          <h2 className="card-title">Recent Orders</h2>
          <DataTable
            columns={orderCols}
            data={stats?.recent_orders}
            loading={loading}
            onRowClick={row => navigate(`/orders/${row.id}`)}
          />
        </div>

        <div className="card">
          <h2 className="card-title">Open Messages</h2>
          {loading ? (
            <div className="skeleton-list">
              {[1,2,3,4,5].map(i => <div key={i} className="skeleton" style={{height:48,marginBottom:8}} />)}
            </div>
          ) : (
            <div className="message-preview-list">
              {stats?.recent_messages?.map(msg => (
                <div key={msg.id} className="message-preview" onClick={() => navigate('/messages')}>
                  <div className="message-preview-header">
                    <ChannelBadge channel={msg.channel} />
                    <span className="message-preview-name">{msg.customer_name}</span>
                    {msg.sentiment === 'negative' && <span className="urgent-tag">URGENT</span>}
                  </div>
                  <div className="message-preview-body">{msg.body?.slice(0, 100)}...</div>
                </div>
              ))}
              {(!stats?.recent_messages || stats.recent_messages.length === 0) && (
                <p className="text-muted">No open messages</p>
              )}
            </div>
          )}
        </div>
      </div>

      <div className="card" style={{ marginTop: 20 }}>
        <h2 className="card-title">Channel Status</h2>
        <div className="channel-status-grid">
          {stats?.channels?.map(ch => (
            <div key={ch.id} className="channel-status-card">
              <ChannelBadge channel={ch.channel_type} />
              <span className="channel-status-name">{ch.display_name}</span>
              <span className={`channel-status-dot ${ch.active ? 'dot-green' : 'dot-red'}`} />
              <span className="text-muted text-xs">
                {ch.last_sync_at ? `Synced ${new Date(ch.last_sync_at).toLocaleString()}` : 'Never synced'}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
