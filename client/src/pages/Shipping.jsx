import React, { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { api } from '../api/client'
import { PageHeader, Skeleton } from '../components/shared'
import { useToast } from '../App'

const CARRIER_ICONS = {
  royal_mail: '🇬🇧',
  dpd: '📦',
  hermes: '📮',
  ups: '🟤',
  fedex: '🟣',
  stamps_com: '📬',
}

export default function Shipping() {
  const [searchParams] = useSearchParams()
  const [orderId, setOrderId] = useState(searchParams.get('order') || '')
  const [rates, setRates] = useState(null)
  const [loading, setLoading] = useState(false)
  const [purchasing, setPurchasing] = useState(false)
  const [orders, setOrders] = useState([])
  const toast = useToast()

  useEffect(() => {
    api.orders({ status: 'pending', per_page: 100 }).then(d => setOrders(d.orders))
  }, [])

  useEffect(() => {
    if (orderId) fetchRates()
  }, [])

  const fetchRates = async () => {
    if (!orderId) return
    setLoading(true)
    setRates(null)
    try {
      const data = await api.shippingRates(orderId)
      setRates(data)
    } catch {
      toast('Failed to fetch rates', 'error')
    } finally {
      setLoading(false)
    }
  }

  const purchaseLabel = async (rate) => {
    setPurchasing(true)
    try {
      const result = await api.purchaseLabel({
        order_id: parseInt(orderId),
        carrier_code: rate.carrierCode,
        service_code: rate.serviceCode,
      })
      toast(`Label purchased! Tracking: ${result.trackingNumber}`, 'success')
      setRates(null)
    } catch {
      toast('Failed to purchase label', 'error')
    } finally {
      setPurchasing(false)
    }
  }

  return (
    <div className="page">
      <PageHeader title="Shipping" />

      <div className="card">
        <h2 className="card-title">Get Shipping Rates</h2>
        <div className="form-row">
          <div className="form-group" style={{ flex: 1 }}>
            <label>Select Order</label>
            <select className="input" value={orderId} onChange={e => setOrderId(e.target.value)}>
              <option value="">Choose an order...</option>
              {orders.map(o => (
                <option key={o.id} value={o.id}>
                  {o.order_number} — {o.customer_name} (£{o.total.toFixed(2)})
                </option>
              ))}
            </select>
          </div>
          <button className="btn-primary" onClick={fetchRates} disabled={!orderId || loading} style={{ alignSelf: 'flex-end' }}>
            {loading ? 'Fetching...' : 'Get Rates'}
          </button>
        </div>
      </div>

      {loading && (
        <div className="rates-grid" style={{ marginTop: 20 }}>
          {[1,2,3,4,5,6].map(i => (
            <div key={i} className="rate-card">
              <Skeleton height={20} width={120} />
              <Skeleton height={28} width={80} style={{ marginTop: 12 }} />
              <Skeleton height={14} width={100} style={{ marginTop: 8 }} />
            </div>
          ))}
        </div>
      )}

      {rates && (
        <>
          {rates.demo && (
            <div className="demo-notice" style={{ marginTop: 16 }}>
              Demo mode — connect ShipStation in Settings for live rates
            </div>
          )}
          <div className="rates-grid" style={{ marginTop: 20 }}>
            {rates.rates.map((rate, i) => (
              <div key={i} className="rate-card">
                <div className="rate-carrier">
                  <span className="rate-icon">{CARRIER_ICONS[rate.carrierCode] || '📦'}</span>
                  <span className="rate-carrier-name">{rate.carrierCode?.replace('_', ' ')}</span>
                </div>
                <div className="rate-service">{rate.serviceName}</div>
                <div className="rate-price">
                  £{(rate.shipmentCost + (rate.otherCost || 0)).toFixed(2)}
                </div>
                <div className="rate-eta">
                  {rate.estimatedDays ? `${rate.estimatedDays} day${rate.estimatedDays > 1 ? 's' : ''}` : 'Varies'}
                </div>
                <button
                  className="btn-primary btn-sm"
                  onClick={() => purchaseLabel(rate)}
                  disabled={purchasing}
                  style={{ width: '100%', marginTop: 12 }}
                >
                  {purchasing ? 'Purchasing...' : 'Buy Label'}
                </button>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
