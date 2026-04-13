import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { KPICard, StatusBadge, ChannelBadge } from '../components/shared'

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    api.dashboardStats().then(setStats).finally(() => setLoading(false))
  }, [])

  return (
    <div className="page">
      <div className="page-header">
        <div className="page-title-row">
          <h1 className="page-title">Dashboard</h1>
          <p className="page-subtitle">Your store at a glance</p>
        </div>
        <div className="page-actions">
          <button className="btn btn-primary btn-sm" onClick={() => api.syncOrders().then(() => window.location.reload())}>
            ↻ Sync All
          </button>
        </div>
      </div>

      {/* KPI Scroll — horizontal on mobile, grid on desktop */}
      <div className="kpi-scroll">
        <KPICard label="Total Orders" value={stats?.total_orders} loading={loading} />
        <KPICard label="Revenue (Shipped)" value={stats?.revenue} loading={loading} prefix="£" />
        <KPICard label="Awaiting Shipment" value={stats?.awaiting_shipment} loading={loading} />
        <KPICard label="Shipped This Week" value={stats?.shipped_this_week} loading={loading} />
        <KPICard label="Open Messages" value={stats?.open_messages} loading={loading} />
        <KPICard label="Active Channels" value={stats?.active_channels} loading={loading} />
      </div>

      {/* Recent Orders — card on mobile, table on desktop */}
      <div className="dashboard-section">
        <div className="dashboard-section-title">Recent Orders</div>
        {loading ? (
          <div className="card">
            <div className="card-body">
              {[1,2,3].map(i => <div key={i} className="skeleton" style={{height:60,marginBottom:8,borderRadius:8}} />)}
            </div>
          </div>
        ) : !stats?.recent_orders?.length ? (
          <div className="empty-state">
            <div className="empty-state-title">No orders yet</div>
          </div>
        ) : (
          <div className="card">
            {/* Desktop table */}
            <div className="table-scroll">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Order</th>
                    <th>Channel</th>
                    <th>Customer</th>
                    <th>Total</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {stats.recent_orders.map(order => (
                    <tr key={order.id} className="clickable" onClick={() => navigate(`/orders/${order.id}`)}>
                      <td><span className="mono" style={{ fontSize: 11 }}>{order.order_number}</span></td>
                      <td><ChannelBadge channel={order.channel} /></td>
                      <td style={{ maxWidth: 120, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{order.customer_name}</td>
                      <td><span className="mono">£{order.total?.toFixed(2)}</span></td>
                      <td><StatusBadge status={order.status} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* Open Messages */}
      <div className="dashboard-section">
        <div className="dashboard-section-title">Open Messages</div>
        {loading ? (
          <div className="card">
            <div className="card-body">
              {[1,2,3].map(i => <div key={i} className="skeleton" style={{height:48,marginBottom:8,borderRadius:8}} />)}
            </div>
          </div>
        ) : !stats?.recent_messages?.length ? (
          <div className="card"><div className="card-body"><p className="text-muted" style={{ fontSize: 13 }}>No open messages</p></div></div>
        ) : (
          <div className="card">
            {stats.recent_messages.map(msg => (
              <div key={msg.id} className="message-preview" onClick={() => navigate('/messages')}>
                <div className="message-preview-header">
                  <ChannelBadge channel={msg.channel} />
                  <span className="message-preview-name">{msg.customer_name}</span>
                  {msg.sentiment === 'negative' && <span className="urgent-tag">URGENT</span>}
                </div>
                <div className="message-preview-body">{msg.body?.slice(0, 90)}...</div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Channel Status */}
      <div className="dashboard-section">
        <div className="dashboard-section-title">Channel Status</div>
        <div className="card">
          <div className="card-body">
            {stats?.channels?.length === 0 && <p className="text-muted" style={{ fontSize: 13 }}>No channels connected</p>}
            {stats?.channels?.map(ch => (
              <div key={ch.id} className="channel-status-row">
                <ChannelBadge channel={ch.channel_type} />
                <span style={{ flex: 1, fontSize: 13, fontWeight: 600, color: 'var(--text)' }}>{ch.display_name || ch.channel_type}</span>
                <div className={`channel-status-dot ${ch.active ? 'dot-green' : 'dot-red'}`} />
                <span style={{ fontSize: 11.5, color: ch.active ? 'var(--green)' : 'var(--text3)' }}>{ch.active ? 'Active' : 'Inactive'}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
