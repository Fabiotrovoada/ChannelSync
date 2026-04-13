import React, { useState, useEffect, useCallback } from 'react'
import { api } from '../api/client'
import { ChannelBadge, StatusBadge, Pagination, Modal } from '../components/shared'
import { useToast } from '../App'
import { Grid3x3, LayoutList, Package, AlertTriangle } from 'lucide-react'

export default function Listings() {
  const [listings, setListings] = useState([])
  const [loading, setLoading] = useState(true)
  const [filters, setFilters] = useState({ channel: '', search: '', page: 1 })
  const [total, setTotal] = useState(0)
  const [pages, setPages] = useState(1)
  const [editing, setEditing] = useState(null)
  const [editForm, setEditForm] = useState({})
  const [viewMode, setViewMode] = useState('grid')
  const toast = useToast()

  const CHANNELS = [
    { id: '', label: 'All Channels' },
    { id: 'amazon', label: 'Amazon' },
    { id: 'ebay', label: 'eBay' },
    { id: 'woocommerce', label: 'WooCommerce' },
    { id: 'shopify', label: 'Shopify' },
  ]

  const load = useCallback(() => {
    setLoading(true)
    const params = {}
    if (filters.channel) params.channel = filters.channel
    if (filters.search) params.search = filters.search
    params.page = filters.page
    api.listings(params).then(d => {
      setListings(d.listings || [])
      setTotal(d.total || 0)
      setPages(d.pages || 1)
    }).finally(() => setLoading(false))
  }, [filters])

  useEffect(() => { load() }, [load])

  function handleEdit(listing) {
    setEditing(listing)
    setEditForm({ title: listing.title, price: listing.price, quantity: listing.quantity })
  }

  async function handleSave() {
    try {
      await api.updateListing(editing.id, editForm)
      setEditing(null)
      toast('Listing updated', 'success')
      load()
    } catch {
      toast('Failed to update listing', 'error')
    }
  }

  // Group listings by channel, then by category
  const grouped = listings.reduce((acc, listing) => {
    const channel = listing.channel || 'Other'
    const category = listing.category || 'Uncategorized'
    if (!acc[channel]) acc[channel] = {}
    if (!acc[channel][category]) acc[channel][category] = []
    acc[channel][category].push(listing)
    return acc
  }, {})

  return (
    <div className="page">
      <div className="page-header">
        <div className="page-title-row">
          <h1 className="page-title">Listings</h1>
          <p className="page-subtitle">{total > 0 ? `${total} listings across ${Object.keys(grouped).length} channels` : 'Manage your product listings'}</p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button
            className={`btn btn-ghost btn-sm ${viewMode === 'grid' ? '' : ''}`}
            onClick={() => setViewMode(v => v === 'grid' ? 'list' : 'grid')}
            style={{ padding: 7 }}
            title={viewMode === 'grid' ? 'Switch to list view' : 'Switch to grid view'}
          >
            {viewMode === 'grid' ? <LayoutList size={15} /> : <Grid3x3 size={15} />}
          </button>
        </div>
      </div>

      <div className="filters-bar">
        <input
          className="input"
          placeholder="Search by title or SKU..."
          value={filters.search}
          onChange={e => setFilters({ ...filters, search: e.target.value, page: 1 })}
          style={{ width: 200 }}
        />
        <select className="form-select" value={filters.channel} onChange={e => setFilters({ ...filters, channel: e.target.value, page: 1 })} style={{ width: 'auto', minWidth: 130 }}>
          {CHANNELS.map(c => <option key={c.id} value={c.id}>{c.label}</option>)}
        </select>
      </div>

      {loading ? (
        <div className="section">
          <div className={viewMode === 'grid' ? 'listings-grid' : ''}>
            {Array.from({ length: 8 }, (_, i) => (
              viewMode === 'grid' ? (
                <div key={i} className="listing-card">
                  <div className="skeleton" style={{ height: 110 }} />
                  <div className="listing-info">
                    <div className="skeleton" style={{ height: 12, marginBottom: 6 }} />
                    <div className="skeleton" style={{ height: 14, width: '70%' }} />
                  </div>
                </div>
              ) : (
                <div key={i} style={{ padding: '12px 16px', borderBottom: '1px solid var(--border-light)' }}>
                  <div className="skeleton" style={{ height: 14, width: '50%' }} />
                </div>
              )
            ))}
          </div>
        </div>
      ) : listings.length === 0 ? (
        <div className="section">
          <div className="card">
            <div className="card-body" style={{ textAlign: 'center', padding: '60px 20px' }}>
              <Package size={40} style={{ opacity: 0.2, marginBottom: 12 }} />
              <div className="empty-state-title">No listings found</div>
              <div className="empty-state-sub">Try adjusting your search or channel filter</div>
            </div>
          </div>
        </div>
      ) : (
        <div className="section">
          {viewMode === 'grid' ? (
            // Grid view grouped by channel
            Object.entries(grouped).map(([channel, categories]) => (
              <div key={channel} style={{ marginBottom: 24 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
                  <ChannelBadge channel={channel} />
                  <span style={{ fontSize: 13, fontWeight: 700, color: 'var(--text2)' }}>
                    {Object.values(categories).flat().length} listings
                  </span>
                </div>
                <div className="listings-grid" style={{ padding: 0 }}>
                  {Object.entries(categories).map(([category, items]) => (
                    items.map(listing => (
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
                            {category !== 'Uncategorized' && (
                              <span style={{ fontSize: 10, background: 'var(--surface2)', padding: '1px 5px', borderRadius: 3, color: 'var(--text3)', fontWeight: 600 }}>
                                {category}
                              </span>
                            )}
                            <StatusBadge status={listing.status} />
                          </div>
                          <div className="listing-sku">{listing.sku}</div>
                          <div className="listing-title">{listing.title}</div>
                          <div className="listing-footer">
                            <span className="listing-price">£{listing.price?.toFixed(2)}</span>
                            <span className={`listing-qty ${listing.quantity < 10 ? 'low-stock' : ''}`}>
                              {listing.quantity < 10 && <AlertTriangle size={11} style={{ display: 'inline' }} />}
                              {listing.quantity} in stock
                            </span>
                          </div>
                        </div>
                      </div>
                    ))
                  ))}
                </div>
              </div>
            ))
          ) : (
            // List view
            <div className="card">
              <div className="table-scroll">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>SKU</th>
                      <th>Product</th>
                      <th>Channel</th>
                      <th>Category</th>
                      <th>Price</th>
                      <th>Stock</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {listings.map(listing => (
                      <tr key={listing.id} className="clickable" onClick={() => handleEdit(listing)}>
                        <td><span className="mono" style={{ fontSize: 11 }}>{listing.sku}</span></td>
                        <td style={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{listing.title}</td>
                        <td><ChannelBadge channel={listing.channel} /></td>
                        <td style={{ fontSize: 12, color: 'var(--text2)' }}>{listing.category || '—'}</td>
                        <td><span className="mono">£{listing.price?.toFixed(2)}</span></td>
                        <td>
                          <span className={listing.quantity < 10 ? 'text-red' : ''} style={{ fontWeight: 600 }}>
                            {listing.quantity}
                          </span>
                          {listing.quantity < 10 && <AlertTriangle size={11} style={{ display: 'inline', marginLeft: 4, color: 'var(--red)' }} />}
                        </td>
                        <td><StatusBadge status={listing.status} /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {pages > 1 && (
            <div style={{ marginTop: 16 }}>
              <Pagination page={filters.page} pages={pages} onPageChange={p => setFilters(f => ({ ...f, page: p }))} />
            </div>
          )}
        </div>
      )}

      <Modal open={!!editing} onClose={() => setEditing(null)} title="Edit Listing">
        {editing && (
          <div>
            <div className="form-group">
              <label className="form-label">Title</label>
              <input className="form-input" value={editForm.title || ''} onChange={e => setEditForm({ ...editForm, title: e.target.value })} />
            </div>
            <div className="form-row">
              <div className="form-group">
                <label className="form-label">Price (£)</label>
                <input className="form-input" type="number" step="0.01" value={editForm.price || ''} onChange={e => setEditForm({ ...editForm, price: parseFloat(e.target.value) || 0 })} />
              </div>
              <div className="form-group">
                <label className="form-label">Quantity</label>
                <input className="form-input" type="number" value={editForm.quantity || ''} onChange={e => setEditForm({ ...editForm, quantity: parseInt(e.target.value) || 0 })} />
              </div>
            </div>
            <div style={{ display: 'flex', gap: 8, marginTop: 16 }}>
              <button className="btn btn-primary" onClick={handleSave}>Save Changes</button>
              <button className="btn btn-ghost" onClick={() => setEditing(null)}>Cancel</button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}
