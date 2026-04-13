import React, { useState, useEffect } from 'react'
import { api } from '../api/client'
import DataTable from '../components/DataTable'
import { PageHeader, Modal } from '../components/shared'
import { useToast } from '../App'

export default function Inventory() {
  const [data, setData] = useState({ inventory: [], low_stock_threshold: 10 })
  const [loading, setLoading] = useState(true)
  const [adjusting, setAdjusting] = useState(null)
  const [delta, setDelta] = useState(0)
  const [reason, setReason] = useState('')
  const toast = useToast()

  const load = () => {
    setLoading(true)
    api.inventory().then(setData).finally(() => setLoading(false))
  }

  useEffect(load, [])

  const handleAdjust = async () => {
    try {
      await api.updateInventory(adjusting.sku, { quantity_delta: delta, reason })
      setAdjusting(null)
      setDelta(0)
      setReason('')
      toast('Inventory adjusted', 'success')
      load()
    } catch {
      toast('Failed to adjust inventory', 'error')
    }
  }

  const columns = [
    { key: 'sku', label: 'SKU', style: { fontFamily: 'JetBrains Mono, monospace', fontSize: 12 } },
    { key: 'product_name', label: 'Product' },
    { key: 'warehouse_qty', label: 'Warehouse', render: (v, r) => <span className="mono">{r.warehouse_qty ?? 0}</span> },
    { key: 'reserved_qty', label: 'Reserved', render: (v, r) => <span className="mono">{r.reserved_qty ?? 0}</span> },
    {
      key: 'available_qty', label: 'Available', render: (v, r) => (
        <span className={`mono ${r.low_stock ? 'text-red' : ''}`}>
          {r.available_qty ?? 0} {r.low_stock && '⚠'}
        </span>
      )
    },
    { key: 'last_updated', label: 'Updated', render: (v, r) => r.last_updated ? new Date(r.last_updated).toLocaleDateString() : '—' },
    {
      key: 'actions', label: '', sortable: false, render: (v, r) => (
        <button className="btn-ghost btn-sm" onClick={(e) => { e.stopPropagation(); setAdjusting(r) }}>
          Adjust
        </button>
      )
    },
  ]

  const lowStockCount = data.inventory.filter(i => i.low_stock).length

  return (
    <div className="page">
      <PageHeader title="Inventory">
        {lowStockCount > 0 && (
          <span className="alert-badge">{lowStockCount} low stock items</span>
        )}
      </PageHeader>

      <div className="card">
        <DataTable columns={columns} data={data.inventory} loading={loading} emptyMessage="No inventory data" />
      </div>

      <Modal open={!!adjusting} onClose={() => setAdjusting(null)} title="Adjust Stock">
        {adjusting && (
          <div>
            <p className="mono" style={{ marginBottom: 12 }}>{adjusting.sku} — {adjusting.product_name}</p>
            <p className="text-muted" style={{ marginBottom: 16 }}>Current: {adjusting.warehouse_qty} warehouse / {adjusting.available_qty} available</p>
            <div className="form-group">
              <label>Quantity Change (+/-)</label>
              <input className="input" type="number" value={delta} onChange={e => setDelta(parseInt(e.target.value) || 0)} />
            </div>
            <div className="form-group">
              <label>Reason</label>
              <input className="input" value={reason} onChange={e => setReason(e.target.value)} placeholder="e.g. Stock count correction" />
            </div>
            <div style={{ display: 'flex', gap: 8, marginTop: 16 }}>
              <button className="btn-primary" onClick={handleAdjust}>Apply Adjustment</button>
              <button className="btn-ghost" onClick={() => setAdjusting(null)}>Cancel</button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}
