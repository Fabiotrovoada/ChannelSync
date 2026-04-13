import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { StatusBadge, ChannelBadge, Skeleton } from '../components/shared'
import { useToast } from '../App'

export default function OrderDetail() {
  const { id } = useParams()
  const [order, setOrder] = useState(null)
  const [loading, setLoading] = useState(true)
  const [tracking, setTracking] = useState('')
  const [carrier, setCarrier] = useState('')
  const navigate = useNavigate()
  const toast = useToast()

  useEffect(() => {
    api.order(id).then(setOrder).finally(() => setLoading(false))
  }, [id])

  const handleShip = async () => {
    if (!tracking) return
    try {
      const updated = await api.shipOrder(id, { carrier, tracking_number: tracking })
      setOrder(updated)
      toast('Order marked as shipped', 'success')
    } catch {
      toast('Failed to ship order', 'error')
    }
  }

  const handleStatusChange = async (status) => {
    try {
      const updated = await api.updateOrder(id, { status })
      setOrder(updated)
      toast(`Status updated to ${status}`, 'success')
    } catch {
      toast('Failed to update status', 'error')
    }
  }

  if (loading) {
    return (
      <div className="page">
        <Skeleton height={28} width={200} />
        <div style={{ marginTop: 20 }}>
          <Skeleton height={200} />
        </div>
      </div>
    )
  }

  if (!order) return <div className="page"><p>Order not found</p></div>

  const items = typeof order.items_json === 'string' ? JSON.parse(order.items_json) : (order.items_json || [])

  return (
    <div className="page">
      <div className="page-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <button className="btn-ghost btn-sm" onClick={() => navigate('/orders')}>← Back</button>
          <h1 className="page-title mono">{order.order_number}</h1>
          <ChannelBadge channel={order.channel} />
          <StatusBadge status={order.status} />
        </div>
      </div>

      <div className="detail-grid">
        <div className="card">
          <h2 className="card-title">Customer</h2>
          <div className="detail-field">
            <span className="detail-label">Name</span>
            <span>{order.customer_name}</span>
          </div>
          <div className="detail-field">
            <span className="detail-label">Email</span>
            <span>{order.customer_email}</span>
          </div>
          <div className="detail-field">
            <span className="detail-label">Address</span>
            <span>{order.address}</span>
          </div>
        </div>

        <div className="card">
          <h2 className="card-title">Order Info</h2>
          <div className="detail-field">
            <span className="detail-label">Channel Order ID</span>
            <span className="mono">{order.channel_order_id}</span>
          </div>
          <div className="detail-field">
            <span className="detail-label">Order Date</span>
            <span>{order.order_date ? new Date(order.order_date).toLocaleString() : '—'}</span>
          </div>
          <div className="detail-field">
            <span className="detail-label">Total</span>
            <span className="kpi-value" style={{ fontSize: 20 }}>£{order.total.toFixed(2)}</span>
          </div>
          {order.tracking_number && (
            <div className="detail-field">
              <span className="detail-label">Tracking</span>
              <span className="mono">{order.tracking_number} ({order.carrier})</span>
            </div>
          )}
        </div>
      </div>

      <div className="card" style={{ marginTop: 20 }}>
        <h2 className="card-title">Items</h2>
        <table className="data-table">
          <thead>
            <tr>
              <th>SKU</th>
              <th>Product</th>
              <th>Qty</th>
              <th>Price</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item, i) => (
              <tr key={i}>
                <td className="mono">{item.sku}</td>
                <td>{item.title}</td>
                <td>{item.qty}</td>
                <td className="mono">£{item.price.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {order.status === 'pending' && (
        <div className="card" style={{ marginTop: 20 }}>
          <h2 className="card-title">Ship Order</h2>
          <div className="form-row">
            <div className="form-group">
              <label>Carrier</label>
              <select className="input" value={carrier} onChange={e => setCarrier(e.target.value)}>
                <option value="">Select carrier</option>
                <option value="Royal Mail">Royal Mail</option>
                <option value="DPD">DPD</option>
                <option value="Evri">Evri</option>
                <option value="UPS">UPS</option>
                <option value="FedEx">FedEx</option>
              </select>
            </div>
            <div className="form-group">
              <label>Tracking Number</label>
              <input className="input" value={tracking} onChange={e => setTracking(e.target.value)} placeholder="Enter tracking number" />
            </div>
            <button className="btn-primary" onClick={handleShip} style={{ alignSelf: 'flex-end' }}>
              Mark Shipped
            </button>
          </div>
        </div>
      )}

      <div className="card" style={{ marginTop: 20 }}>
        <h2 className="card-title">Actions</h2>
        <div style={{ display: 'flex', gap: 8 }}>
          {order.status !== 'shipped' && (
            <button className="btn-ghost" onClick={() => handleStatusChange('shipped')}>Mark Shipped</button>
          )}
          {order.status !== 'delivered' && order.status === 'shipped' && (
            <button className="btn-ghost" onClick={() => handleStatusChange('delivered')}>Mark Delivered</button>
          )}
          {order.status !== 'cancelled' && (
            <button className="btn-ghost" style={{ color: 'var(--red)' }} onClick={() => handleStatusChange('cancelled')}>Cancel</button>
          )}
          <button className="btn-primary" onClick={() => navigate(`/shipping?order=${order.id}`)}>
            Get Shipping Rates
          </button>
        </div>
      </div>
    </div>
  )
}
