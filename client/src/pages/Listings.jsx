import React, { useState, useEffect } from 'react'
import { api } from '../api/client'
import { ChannelBadge, StatusBadge, PageHeader, Pagination, Modal } from '../components/shared'
import { useToast } from '../App'

export default function Listings() {
  const [data, setData] = useState({ listings: [], total: 0, page: 1, pages: 1 })
  const [loading, setLoading] = useState(true)
  const [filters, setFilters] = useState({ channel: '', search: '', page: 1 })
  const [editing, setEditing] = useState(null)
  const [editForm, setEditForm] = useState({})
  const toast = useToast()

  const load = () => {
    setLoading(true)
    const params = {}
    if (filters.channel) params.channel = filters.channel
    if (filters.search) params.search = filters.search
    params.page = filters.page
    api.listings(params).then(setData).finally(() => setLoading(false))
  }

  useEffect(load, [filters])

  const handleEdit = (listing) => {
    setEditing(listing)
    setEditForm({ title: listing.title, price: listing.price, quantity: listing.quantity })
  }

  const handleSave = async () => {
    try {
      await api.updateListing(editing.id, editForm)
      setEditing(null)
      toast('Listing updated', 'success')
      load()
    } catch {
      toast('Failed to update listing', 'error')
    }
  }

  return (
    <div className="page">
      <PageHeader title="Listings" />

      <div className="filters-bar">
        <input
          className="input"
          placeholder="Search listings..."
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
      </div>

      <div className="listings-grid">
        {loading ? (
          Array.from({ length: 8 }, (_, i) => (
            <div key={i} className="listing-card">
              <div className="skeleton" style={{ height: 120 }} />
              <div className="skeleton" style={{ height: 14, marginTop: 8 }} />
              <div className="skeleton" style={{ height: 14, marginTop: 4, width: '60%' }} />
            </div>
          ))
        ) : data.listings.length === 0 ? (
          <p className="text-muted">No listings found</p>
        ) : (
          data.listings.map(listing => (
            <div key={listing.id} className="listing-card" onClick={() => handleEdit(listing)}>
              <div className="listing-image">
                {listing.image_url ? (
                  <img src={listing.image_url} alt={listing.title} />
                ) : (
                  <div className="listing-placeholder">No Image</div>
                )}
              </div>
              <div className="listing-info">
                <div className="listing-header">
                  <ChannelBadge channel={listing.channel} />
                  <StatusBadge status={listing.status} />
                </div>
                <div className="listing-sku mono">{listing.sku}</div>
                <div className="listing-title">{listing.title}</div>
                <div className="listing-footer">
                  <span className="listing-price mono">£{listing.price.toFixed(2)}</span>
                  <span className={`listing-qty ${listing.quantity < 10 ? 'low-stock' : ''}`}>
                    {listing.quantity} in stock
                    {listing.quantity < 10 && ' ⚠'}
                  </span>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      <Pagination page={data.page} pages={data.pages} onPageChange={p => setFilters({ ...filters, page: p })} />

      <Modal open={!!editing} onClose={() => setEditing(null)} title="Edit Listing">
        {editing && (
          <div>
            <div className="form-group">
              <label>Title</label>
              <input className="input" value={editForm.title} onChange={e => setEditForm({ ...editForm, title: e.target.value })} />
            </div>
            <div className="form-group">
              <label>Price (£)</label>
              <input className="input" type="number" step="0.01" value={editForm.price} onChange={e => setEditForm({ ...editForm, price: parseFloat(e.target.value) })} />
            </div>
            <div className="form-group">
              <label>Quantity</label>
              <input className="input" type="number" value={editForm.quantity} onChange={e => setEditForm({ ...editForm, quantity: parseInt(e.target.value) })} />
            </div>
            <div style={{ display: 'flex', gap: 8, marginTop: 16 }}>
              <button className="btn-primary" onClick={handleSave}>Save</button>
              <button className="btn-ghost" onClick={() => setEditing(null)}>Cancel</button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}
