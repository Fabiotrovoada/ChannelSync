import React, { useState, useEffect, useCallback } from 'react'
import { api } from '../api/client'
import { ChannelBadge, StatusBadge, Skeleton } from '../components/shared'
import { useToast } from '../App'
import { CheckSquare, Square, Mail, Send } from 'lucide-react';

const CHANNELS = [
  { id: '', label: 'All Channels' },
  { id: 'amazon', label: 'Amazon' },
  { id: 'ebay', label: 'eBay' },
  { id: 'woocommerce', label: 'WooCommerce' },
  { id: 'shopify', label: 'Shopify' },
  { id: 'tiktok', label: 'TikTok Shop' },
  { id: 'etsy', label: 'Etsy' },
  { id: 'walmart', label: 'Walmart' },
  { id: 'mirakl', label: 'Mirakl' },
];

export default function Messages() {
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState(null)
  const [replyText, setReplyText] = useState('')
  const [aiLoading, setAiLoading] = useState(false)
  const [statusFilter, setStatusFilter] = useState('open')
  const [channelFilter, setChannelFilter] = useState('')
  const [selectedIds, setSelectedIds] = useState(new Set())
  const [bulkTone, setBulkTone] = useState('professional')
  const [bulkSending, setBulkSending] = useState(false)
  const toast = useToast()

  const load = useCallback(() => {
    setLoading(true)
    const params = { status: statusFilter }
    if (channelFilter) params.channel = channelFilter
    api.messages(params).then(d => setMessages(d.messages || [])).finally(() => setLoading(false))
  }, [statusFilter, channelFilter])

  useEffect(() => { load() }, [load])

  const toggleSelect = (id) => {
    setSelectedIds(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const toggleAll = () => {
    if (selectedIds.size === messages.length) {
      setSelectedIds(new Set())
    } else {
      setSelectedIds(new Set(messages.map(m => m.id)))
    }
  }

  const handleAiReply = async (msg) => {
    setAiLoading(true)
    try {
      const result = await api.aiReply(msg.id)
      setReplyText(result.reply)
      toast(`AI reply generated — ${result.intent || 'ready'}`, 'success')
    } catch {
      toast('Failed to generate AI reply', 'error')
    } finally {
      setAiLoading(false)
    }
  }

  const handleSendReply = async () => {
    if (!replyText || !selected) return
    try {
      await api.replyMessage(selected.id, replyText)
      setReplyText('')
      setSelected(null)
      toast('Reply sent', 'success')
      load()
    } catch {
      toast('Failed to send reply', 'error')
    }
  }

  const handleBulkAi = async () => {
    if (selectedIds.size === 0) return
    setBulkSending(true)
    try {
      // Generate AI replies for selected messages
      const ids = Array.from(selectedIds)
      await Promise.all(ids.map(id => api.aiReply(id)))
      toast(`${ids.length} AI replies generated`, 'success')
      setSelectedIds(new Set())
      load()
    } catch {
      toast('Failed to generate AI replies', 'error')
    } finally {
      setBulkSending(false)
    }
  }

  return (
    <div className="page">
      <div className="page-header">
        <div className="page-title-row">
          <h1 className="page-title">Messages</h1>
          {selectedIds.size > 0 && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 4 }}>
              <span style={{ fontSize: 12, color: 'var(--accent)', fontWeight: 600 }}>{selectedIds.size} selected</span>
              <button className="btn btn-sm" style={{ background: 'var(--accent)', color: '#fff' }} onClick={handleBulkAi} disabled={bulkSending}>
                {bulkSending ? 'Generating...' : '✨ AI Reply All'}
              </button>
            </div>
          )}
        </div>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <select className="form-select" value={channelFilter} onChange={e => setChannelFilter(e.target.value)} style={{ width: 'auto', minWidth: 130 }}>
            {CHANNELS.map(c => <option key={c.id} value={c.id}>{c.label}</option>)}
          </select>
          <select className="form-select" value={statusFilter} onChange={e => setStatusFilter(e.target.value)} style={{ width: 'auto', minWidth: 110 }}>
            <option value="open">Open</option>
            <option value="resolved">Resolved</option>
            <option value="all">All</option>
          </select>
        </div>
      </div>

      <div className="messages-layout">
        {/* Message list */}
        <div className="message-list-panel">
          {/* Bulk select header */}
          {messages.length > 0 && (
            <div style={{ padding: '8px 12px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: 8, background: 'var(--surface2)' }}>
              <button
                onClick={toggleAll}
                style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 4, color: 'var(--text2)', display: 'flex' }}
                title="Select all"
              >
                {selectedIds.size === messages.length && messages.length > 0
                  ? <CheckSquare size={16} />
                  : <Square size={16} />
                }
              </button>
              <span style={{ fontSize: 11.5, color: 'var(--text3)' }}>
                {selectedIds.size > 0 ? `${selectedIds.size} of ${messages.length} selected` : `${messages.length} messages`}
              </span>
            </div>
          )}

          {loading ? (
            Array.from({ length: 5 }, (_, i) => <div key={i} style={{ padding: '12px 14px', borderBottom: '1px solid var(--border-light)' }}>
              <Skeleton height={14} width="60%" style={{ marginBottom: 6 }} />
              <Skeleton height={12} width="80%" />
            </div>)
          ) : messages.length === 0 ? (
            <div className="empty-state">
              <Mail size={32} style={{ opacity: 0.2, marginBottom: 8 }} />
              <div className="empty-state-title">No messages</div>
              <div className="empty-state-sub">Try a different filter</div>
            </div>
          ) : (
            messages.map(msg => (
              <div
                key={msg.id}
                className={`message-list-item ${selected?.id === msg.id ? 'message-selected' : ''}`}
                onClick={() => { setSelected(msg); setReplyText(msg.ai_reply || '') }}
              >
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
                  <button
                    onClick={(e) => { e.stopPropagation(); toggleSelect(msg.id) }}
                    style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 2, color: selectedIds.has(msg.id) ? 'var(--accent)' : 'var(--text3)', flexShrink: 0, marginTop: 2, display: 'flex' }}
                  >
                    {selectedIds.has(msg.id) ? <CheckSquare size={15} /> : <Square size={15} />}
                  </button>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div className="message-list-header">
                      <ChannelBadge channel={msg.channel} />
                      <span className="message-list-name">{msg.customer_name}</span>
                      {msg.sentiment === 'negative' && <span className="urgent-tag">URGENT</span>}
                      <StatusBadge status={msg.status} />
                    </div>
                    <div className="message-list-subject">{msg.subject}</div>
                    <div className="message-list-preview">{msg.body?.slice(0, 70)}...</div>
                    <div className="message-list-meta">
                      {msg.intent && <span className="intent-tag">{msg.intent}</span>}
                      <span className="text-muted text-xs">{new Date(msg.created_at).toLocaleString()}</span>
                    </div>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Message detail */}
        <div className="message-detail-panel">
          {selected ? (
            <>
              <div className="message-thread-header">
                <h2>{selected.subject || 'Message'}</h2>
                <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
                  <ChannelBadge channel={selected.channel} />
                  <span style={{ fontSize: 13 }}>{selected.customer_name}</span>
                  <span className="text-muted" style={{ fontSize: 12 }}>&lt;{selected.customer_email}&gt;</span>
                </div>
              </div>

              <div className="message-thread">
                <div className="message-bubble message-inbound">
                  <div className="message-bubble-label">Customer</div>
                  <div className="message-bubble-body">{selected.body}</div>
                  <div className="message-bubble-time">{new Date(selected.created_at).toLocaleString()}</div>
                </div>

                {selected.ai_reply && (
                  <div className="message-bubble message-outbound">
                    <div className="message-bubble-label">AI Suggested Reply</div>
                    <div className="message-bubble-body">{selected.ai_reply}</div>
                    {selected.replied_at && <div className="message-bubble-time">{new Date(selected.replied_at).toLocaleString()}</div>}
                  </div>
                )}
              </div>

              {selected.status === 'open' && (
                <div className="message-reply-box">
                  <div className="reply-actions">
                    <button className="btn btn-ai btn-sm" onClick={() => handleAiReply(selected)} disabled={aiLoading}>
                      {aiLoading ? 'Generating...' : '✨ AI Reply'}
                    </button>
                  </div>
                  <textarea
                    className="input reply-textarea"
                    value={replyText}
                    onChange={e => setReplyText(e.target.value)}
                    placeholder="Type your reply..."
                    rows={4}
                  />
                  <button className="btn btn-primary" onClick={handleSendReply} disabled={!replyText}>
                    <Send size={14} /> Send Reply
                  </button>
                </div>
              )}

              <div className="message-meta-bar">
                {selected.intent && <span className="meta-item">Intent: <strong>{selected.intent}</strong></span>}
                {selected.sentiment && <span className="meta-item">Sentiment: <strong className={`sentiment-${selected.sentiment}`}>{selected.sentiment}</strong></span>}
              </div>
            </>
          ) : (
            <div className="message-empty">
              <Mail size={28} style={{ opacity: 0.2, marginBottom: 8 }} />
              <p className="text-muted">Select a message to view</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
