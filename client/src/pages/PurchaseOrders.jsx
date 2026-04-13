import React, { useState, useEffect } from 'react'
import { api } from '../api/client'
import DataTable from '../components/DataTable'
import { StatusBadge, PageHeader, Modal } from '../components/shared'
import { useToast } from '../App'

export default function PurchaseOrders() {
  const [pos, setPOs] = useState([])
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [showReceive, setShowReceive] = useState(null)
  const [form, setForm] = useState({ vendor_name: '', items: [{ sku: '', title: '', qty: 0, cost: 0 }], total_cost: 0 })
  const [receiveItems, setReceiveItems] = useState([])
  const toast = useToast()

  const load = () => {
    setLoading(true)
    api.purchaseOrders().then(d => setPOs(d.purchase_orders)).finally(() => setLoading(false))
  }

  useEffect(load, [])

  const handleCreate = async () => {
    try {
      const total = form.items.reduce((s, i) => s + i.qty * i.cost, 0)
      await api.createPO({ ...form, total_cost: total })
      setShowCreate(false)
      setForm({ vendor_name: '', items: [{ sku: '', title: '', qty: 0, cost: 0 }], total_cost: 0 })
      toast('Purchase order created', 'success')
      load()
    } catch {
      toast('Failed to create PO', 'error')
    }
  }

  const handleReceive = async () => {
    try {
      await api.receivePO(showReceive.id, receiveItems)
      setShowReceive(null)
      toast('PO received — inventory updated', 'success')
      load()
    } catch {
      toast('Failed to receive PO', 'error')
    }
  }

  const openReceive = (po) => {
    const items = typeof po.items_json === 'string' ? JSON.parse(po.items_json) : (po.items_json || [])
    setReceiveItems(items.map(i => ({ sku: i.sku, qty_received: i.qty })))
    setShowReceive(po)
  }

  const addItem = () => setForm({ ...form, items: [...form.items, { sku: '', title: '', qty: 0, cost: 0 }] })

  const updateItem = (idx, field, value) => {
    const items = [...form.items]
    items[idx] = { ...items[idx], [field]: field === 'qty' || field === 'cost' ? parseFloat(value) || 0 : value }
    setForm({ ...form, items })
  }

  const columns = [
    { key: 'id', label: 'PO #', render: (v, r) => <span className="mono">PO-{String(r.id).padStart(4, '0')}</span> },
    { key: 'vendor_name', label: 'Vendor' },
    { key: 'status', label: 'Status', render: (v, r) => <StatusBadge status={r.status} /> },
    { key: 'total_cost', label: 'Total', render: (v, r) => <span className="mono">£{(r.total_cost || 0).toFixed(2)}</span> },
    { key: 'items', label: 'Items', render: (v, r) => {
      const items = typeof r.items_json === 'string' ? JSON.parse(r.items_json) : (r.items_json || [])
      return items.length + ' items'
    }},
    { key: 'created_at', label: 'Created', render: (v, r) => r.created_at ? new Date(r.created_at).toLocaleDateString() : '—' },
    { key: 'actions', label: '', sortable: false, render: (v, r) => r.status !== 'received' && (
      <button className="btn-ghost btn-sm" onClick={(e) => { e.stopPropagation(); openReceive(r) }}>
        Receive
      </button>
    )},
  ]

  return (
    <div className="page">
      <PageHeader title="Purchase Orders">
        <button className="btn-primary" onClick={() => setShowCreate(true)}>Create PO</button>
      </PageHeader>

      <div className="card">
        <DataTable columns={columns} data={pos} loading={loading} emptyMessage="No purchase orders" />
      </div>

      <Modal open={showCreate} onClose={() => setShowCreate(false)} title="Create Purchase Order" width={600}>
        <div className="form-group">
          <label>Vendor Name</label>
          <input className="input" value={form.vendor_name} onChange={e => setForm({ ...form, vendor_name: e.target.value })} />
        </div>
        <h3 style={{ margin: '16px 0 8px', fontSize: 14 }}>Items</h3>
        {form.items.map((item, i) => (
          <div key={i} className="form-row" style={{ marginBottom: 8 }}>
            <input className="input" placeholder="SKU" value={item.sku} onChange={e => updateItem(i, 'sku', e.target.value)} style={{ width: 120 }} />
            <input className="input" placeholder="Title" value={item.title} onChange={e => updateItem(i, 'title', e.target.value)} style={{ flex: 1 }} />
            <input className="input" type="number" placeholder="Qty" value={item.qty || ''} onChange={e => updateItem(i, 'qty', e.target.value)} style={{ width: 70 }} />
            <input className="input" type="number" step="0.01" placeholder="Cost" value={item.cost || ''} onChange={e => updateItem(i, 'cost', e.target.value)} style={{ width: 80 }} />
          </div>
        ))}
        <button className="btn-ghost btn-sm" onClick={addItem} style={{ marginBottom: 16 }}>+ Add Item</button>
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="btn-primary" onClick={handleCreate}>Create PO</button>
          <button className="btn-ghost" onClick={() => setShowCreate(false)}>Cancel</button>
        </div>
      </Modal>

      <Modal open={!!showReceive} onClose={() => setShowReceive(null)} title="Receive PO" width={500}>
        {showReceive && (
          <div>
            <p className="text-muted" style={{ marginBottom: 12 }}>Vendor: {showReceive.vendor_name}</p>
            {receiveItems.map((item, i) => (
              <div key={i} className="form-row" style={{ marginBottom: 8 }}>
                <span className="mono" style={{ width: 120 }}>{item.sku}</span>
                <input
                  className="input"
                  type="number"
                  value={item.qty_received}
                  onChange={e => {
                    const items = [...receiveItems]
                    items[i] = { ...items[i], qty_received: parseInt(e.target.value) || 0 }
                    setReceiveItems(items)
                  }}
                  style={{ width: 80 }}
                />
                <span className="text-muted">units</span>
              </div>
            ))}
            <div style={{ display: 'flex', gap: 8, marginTop: 16 }}>
              <button className="btn-primary" onClick={handleReceive}>Confirm Receipt</button>
              <button className="btn-ghost" onClick={() => setShowReceive(null)}>Cancel</button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}
