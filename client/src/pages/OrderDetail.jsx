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
  const [showContact, setShowContact] = useState(false)
  const [contactMsg, setContactMsg] = useState('')
  const [contactTone, setContactTone] = useState('professional')
  const [sending, setSending] = useState(false)
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

  const handleContactCustomer = async () => {
    if (!contactMsg.trim()) return
    setSending(true)
    try {
      // Send message via API — store with channel and order reference
      await api.post('/messages', {
        channel: order.channel,
        order_id: order.id,
        customer_email: order.customer_email,
        customer_name: order.customer_name,
        subject: `Re: Order ${order.order_number}`,
        body: contactMsg,
        direction: 'outbound',
        sentiment: 'neutral',
      })
      toast('Message sent to customer', 'success')
      setShowContact(false)
      setContactMsg('')
    } catch {
      toast('Failed to send message', 'error')
    } finally {
      setSending(false)
    }
  }

  const handleAiCompose = async () => {
    if (!contactMsg.trim()) return
    setSending(true)
    try {
      const res = await api.aiCompose(
        `Write a ${contactTone} reply to a customer about their order ${order.order_number}. Context: ${contactMsg}`,
        contactTone
      )
      setContactMsg(res.draft || '')
    } catch {
      toast('Failed to generate reply', 'error')
    } finally {
      setSending(false)
    }
  }

  if (loading) {
    return (
      <div className="page">
        <div className="page-header">
          <Skeleton height={28} width={200} />
        </div>
        <div style={{ padding: 20 }}>
          <Skeleton height={200} />
        </div>
      </div>
    )
  }

  if (!order) return <div className="page"><div className="page-header"><p>Order not found</p></div></div>

  const items = typeof order.items_json === 'string' ? JSON.parse(order.items_json) : (order.items_json || [])

  return (
    <div className="page">
      <div className="page-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
          <button className="back-btn" onClick={() => navigate('/orders')}>← Back</button>
          <span className="page-title mono">{order.order_number}</span>
          <ChannelBadge channel={order.channel} />
          <StatusBadge status={order.status} />
        </div>
        <div className="page-actions">
          <button className="btn btn-primary btn-sm" onClick={() => setShowContact(true)}>
            💬 Contact Customer
          </button>
        </div>
      </div>

      <div className="detail-grid">
        {/* Customer Card */}
        <div className="card">
          <div className="card-header">
            <div className="card-title">Customer</div>
            <button className="btn btn-secondary btn-sm" onClick={() => setShowContact(true)}>
              💬 Message
            </button>
          </div>
          <div className="card-body" style={{ padding: '12px 16px' }}>
            <div className="detail-field">
              <span className="detail-label">Name</span>
              <span className="detail-value">{order.customer_name}</span>
            </div>
            <div className="detail-field">
              <span className="detail-label">Email</span>
              <span className="detail-value">{order.customer_email}</span>
            </div>
            <div className="detail-field" style={{ borderBottom: 'none' }}>
              <span className="detail-label">Address</span>
              <span className="detail-value" style={{ fontSize: 12.5 }}>{order.address}</span>
            </div>
          </div>
        </div>

        {/* Order Info Card */}
        <div className="card">
          <div className="card-header">
            <div className="card-title">Order Details</div>
          </div>
          <div className="card-body" style={{ padding: '12px 16px' }}>
            <div className="detail-field">
              <span className="detail-label">Channel Order ID</span>
              <span className="detail-value mono">{order.channel_order_id}</span>
            </div>
            <div className="detail-field">
              <span className="detail-label">Order Date</span>
              <span className="detail-value">{order.order_date ? new Date(order.order_date).toLocaleDateString() : '—'}</span>
            </div>
            <div className="detail-field">
              <span className="detail-label">Total</span>
              <span className="detail-value" style={{ fontSize: 18, fontWeight: 800 }}>£{order.total?.toFixed(2)}</span>
            </div>
            {order.tracking_number && (
              <div className="detail-field" style={{ borderBottom: 'none' }}>
                <span className="detail-label">Tracking</span>
                <span className="detail-value mono">{order.tracking_number} ({order.carrier})</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Items */}
      <div className="section">
        <div className="card">
          <div className="card-header">
            <div className="card-title">Items ({items.length})</div>
          </div>
          <div className="table-scroll">
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
                    <td className="mono" style={{ fontSize: 11 }}>{item.sku}</td>
                    <td style={{ fontSize: 13 }}>{item.title}</td>
                    <td>{item.qty}</td>
                    <td className="mono">£{item.price?.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Ship Order */}
      {order.status === 'pending' && (
        <div className="section">
          <div className="card">
            <div className="card-header"><div className="card-title">Ship Order</div></div>
            <div className="card-body">
              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">Carrier</label>
                  <select className="form-select" value={carrier} onChange={e => setCarrier(e.target.value)}>
                    <option value="">Select carrier</option>
                    <option value="Royal Mail">Royal Mail</option>
                    <option value="DPD">DPD</option>
                    <option value="Evri">Evri</option>
                    <option value="UPS">UPS</option>
                    <option value="FedEx">FedEx</option>
                    <option value="Yodel">Yodel</option>
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Tracking Number</label>
                  <input className="form-input" value={tracking} onChange={e => setTracking(e.target.value)} placeholder="Enter tracking number" />
                </div>
                <button className="btn btn-primary" onClick={handleShip} disabled={!tracking} style={{ alignSelf: 'flex-end', whiteSpace: 'nowrap' }}>
                  Mark Shipped
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="section">
        <div className="card">
          <div className="card-header"><div className="card-title">Actions</div></div>
          <div className="card-body">
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              <button className="btn btn-secondary" onClick={() => navigate(`/shipping?order=${order.id}`)}>
                📦 Shipping Rates
              </button>
              {order.status !== 'shipped' && (
                <button className="btn btn-secondary" onClick={() => handleStatusChange('shipped')}>Mark Shipped</button>
              )}
              {order.status === 'shipped' && (
                <button className="btn btn-secondary" onClick={() => handleStatusChange('delivered')}>Mark Delivered</button>
              )}
              {order.status !== 'cancelled' && (
                <button className="btn btn-danger" onClick={() => handleStatusChange('cancelled')}>Cancel Order</button>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Contact Customer Modal */}
      {showContact && (
        <div className="modal-overlay" onClick={e => e.target === e.currentTarget && setShowContact(false)}>
          <div className="modal">
            <div className="modal-header">
              <h3>💬 Message Customer</h3>
              <button className="modal-close" onClick={() => setShowContact(false)}>✕</button>
            </div>
            <div className="modal-body">
              <div style={{ display: 'flex', gap: 8, marginBottom: 14, flexWrap: 'wrap' }}>
                <span className="detail-label" style={{ alignSelf: 'center', marginBottom: 0 }}>To:</span>
                <span style={{ fontSize: 13, fontWeight: 600 }}>{order.customer_name}</span>
                <span style={{ fontSize: 12, color: 'var(--text2)' }}>&lt;{order.customer_email}&gt;</span>
              </div>
              <div className="form-group">
                <label className="form-label">Tone</label>
                <select className="form-select" value={contactTone} onChange={e => setContactTone(e.target.value)} style={{ width: 'auto' }}>
                  <option value="professional">Professional</option>
                  <option value="friendly">Friendly</option>
                  <option value="empathetic">Empathetic</option>
                  <option value="firm">Firm</option>
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Message</label>
                <textarea
                  className="form-textarea"
                  value={contactMsg}
                  onChange={e => setContactMsg(e.target.value)}
                  placeholder="Type your message to the customer..."
                  rows={5}
                  style={{ minHeight: 100 }}
                />
              </div>
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                <button className="btn btn-ai btn-sm" onClick={handleAiCompose} disabled={sending || !contactMsg.trim()}>
                  ✨ AI Assist
                </button>
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setShowContact(false)}>Cancel</button>
              <button className="btn btn-primary" onClick={handleContactCustomer} disabled={sending || !contactMsg.trim()}>
                {sending ? 'Sending...' : 'Send Message'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
