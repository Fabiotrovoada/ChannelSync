import React, { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { api } from '../api/client'
import { Skeleton } from '../components/shared'
import { useToast } from '../App'

const CARRIER_LOGOS = {
  royal_mail: { icon: '🇬🇧', color: '#E60000', name: 'Royal Mail' },
  dpd: { icon: '📦', color: '#E60000', name: 'DPD' },
  hermes: { icon: '📮', color: '#00B4E6', name: 'Evri' },
  ups: { icon: '🚚', color: '#351C15', name: 'UPS' },
  fedex: { icon: '✈️', color: '#4D148C', name: 'FedEx' },
  yodel: { icon: '📬', color: '#009A44', name: 'Yodel' },
  dhl: { icon: '🚚', color: '#FFCC00', name: 'DHL' },
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
    api.orders({ status: 'pending', per_page: 100 }).then(d => setOrders(d.orders || [])).catch(() => {})
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
      <div className="page-header">
        <div className="page-title-row">
          <h1 className="page-title">Shipping</h1>
          <p className="page-subtitle">Compare rates and buy shipping labels</p>
        </div>
      </div>

      {/* Order Selector Card */}
      <div className="section">
        <div className="card">
          <div className="card-header">
            <div className="card-title">1 · Select Order</div>
          </div>
          <div className="card-body">
            <div className="form-group" style={{ marginBottom: 14 }}>
              <label className="form-label">Order</label>
              <select
                className="form-select"
                value={orderId}
                onChange={e => { setOrderId(e.target.value); setRates(null); }}
                style={{ fontSize: 14 }}
              >
                <option value="">Choose an order to get shipping rates...</option>
                {orders.map(o => (
                  <option key={o.id} value={o.id}>
                    {o.order_number} — {o.customer_name} — £{o.total?.toFixed(2)}
                  </option>
                ))}
              </select>
            </div>
            <button
              className="btn btn-primary btn-lg"
              onClick={fetchRates}
              disabled={!orderId || loading}
              style={{ width: '100%', justifyContent: 'center', fontSize: 15, padding: '13px 24px' }}
            >
              {loading ? (
                <span>Fetching rates...</span>
              ) : (
                <span>Get Shipping Rates ↗</span>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Demo Notice */}
      {rates?.demo && (
        <div className="section" style={{ paddingTop: 0 }}>
          <div className="demo-notice">
            Demo mode — connect ShipStation in Settings for live rates
          </div>
        </div>
      )}

      {/* Loading skeletons */}
      {loading && (
        <div className="section" style={{ paddingTop: 0 }}>
          <div className="rates-grid" style={{ padding: 0 }}>
            {[1,2,3].map(i => (
              <div key={i} className="rate-card">
                <Skeleton height={18} width={100} />
                <Skeleton height={30} width={80} style={{ marginTop: 10 }} />
                <Skeleton height={14} width={120} style={{ marginTop: 8 }} />
                <Skeleton height={38} style={{ marginTop: 14, borderRadius: 6 }} />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Rate Results */}
      {rates && !loading && rates.rates?.length > 0 && (
        <div className="section" style={{ paddingTop: 0 }}>
          <div className="card">
            <div className="card-header">
              <div className="card-title">2 · Choose Rate</div>
              <span style={{ fontSize: 12, color: 'var(--text2)' }}>{rates.rates.length} rates found</span>
            </div>
            <div className="rates-grid" style={{ padding: 14 }}>
              {rates.rates.map((rate, i) => {
                const carrier = CARRIER_LOGOS[rate.carrierCode?.toLowerCase()] || { icon: '📦', color: '#888', name: rate.carrierCode }
                return (
                  <div key={i} className="rate-card">
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
                      <div style={{
                        width: 40, height: 40, borderRadius: 10,
                        background: carrier.color + '20',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        fontSize: 20, flexShrink: 0
                      }}>
                        {carrier.icon}
                      </div>
                      <div>
                        <div style={{ fontSize: 13.5, fontWeight: 700, color: 'var(--text)' }}>{carrier.name}</div>
                        <div style={{ fontSize: 11.5, color: 'var(--text2)', marginTop: 1 }}>{rate.serviceName}</div>
                      </div>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'baseline', gap: 6, marginBottom: 12 }}>
                      <span style={{ fontSize: 26, fontWeight: 800, color: 'var(--accent)' }}>
                        £{(rate.shipmentCost + (rate.otherCost || 0)).toFixed(2)}
                      </span>
                      {rate.estimatedDays && (
                        <span style={{ fontSize: 12, color: 'var(--text3)' }}>
                          · {rate.estimatedDays === 1 ? '1 day' : `${rate.estimatedDays} days`}
                        </span>
                      )}
                    </div>
                    <button
                      className="btn btn-primary"
                      onClick={() => purchaseLabel(rate)}
                      disabled={purchasing}
                      style={{ width: '100%', justifyContent: 'center', padding: '11px 16px' }}
                    >
                      {purchasing ? 'Purchasing...' : 'Buy Label'}
                    </button>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      )}

      {/* No rates found */}
      {rates && !loading && rates.rates?.length === 0 && (
        <div className="section" style={{ paddingTop: 0 }}>
          <div className="card">
            <div className="card-body" style={{ textAlign: 'center', padding: '40px 20px' }}>
              <div style={{ fontSize: 36, marginBottom: 10 }}>📦</div>
              <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text2)' }}>No rates available</div>
              <div style={{ fontSize: 12.5, color: 'var(--text3)', marginTop: 4 }}>Try selecting a different order</div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
