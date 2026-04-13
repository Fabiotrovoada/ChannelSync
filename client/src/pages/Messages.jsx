import React, { useState, useEffect } from 'react'
import { api } from '../api/client'
import { ChannelBadge, StatusBadge, Skeleton } from '../components/shared'
import { useToast } from '../App'

export default function Messages() {
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState(null)
  const [replyText, setReplyText] = useState('')
  const [aiLoading, setAiLoading] = useState(false)
  const [filter, setFilter] = useState('open')
  const toast = useToast()

  const load = () => {
    setLoading(true)
    api.messages({ status: filter }).then(d => setMessages(d.messages)).finally(() => setLoading(false))
  }

  useEffect(load, [filter])

  const handleAiReply = async (msg) => {
    setAiLoading(true)
    try {
      const result = await api.aiReply(msg.id)
      setReplyText(result.reply)
      toast(`AI reply generated (${result.source}) — ${result.intent} / ${result.sentiment}`, 'success')
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

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Messages</h1>
        <div className="page-actions">
          <select className="input" value={filter} onChange={e => setFilter(e.target.value)}>
            <option value="open">Open</option>
            <option value="resolved">Resolved</option>
          </select>
        </div>
      </div>

      <div className="messages-layout">
        <div className="message-list-panel">
          {loading ? (
            Array.from({ length: 6 }, (_, i) => <Skeleton key={i} height={72} style={{ marginBottom: 8 }} />)
          ) : messages.length === 0 ? (
            <p className="text-muted" style={{ padding: 20 }}>No {filter} messages</p>
          ) : (
            messages.map(msg => (
              <div
                key={msg.id}
                className={`message-list-item ${selected?.id === msg.id ? 'message-selected' : ''}`}
                onClick={() => { setSelected(msg); setReplyText(msg.ai_reply || '') }}
              >
                <div className="message-list-header">
                  <ChannelBadge channel={msg.channel} />
                  <span className="message-list-name">{msg.customer_name}</span>
                  {msg.sentiment === 'negative' && <span className="urgent-tag">URGENT</span>}
                  <StatusBadge status={msg.status} />
                </div>
                <div className="message-list-subject">{msg.subject}</div>
                <div className="message-list-preview">{msg.body?.slice(0, 80)}...</div>
                <div className="message-list-meta">
                  {msg.intent && <span className="intent-tag">{msg.intent}</span>}
                  <span className="text-muted text-xs">{new Date(msg.created_at).toLocaleString()}</span>
                </div>
              </div>
            ))
          )}
        </div>

        <div className="message-detail-panel">
          {selected ? (
            <>
              <div className="message-thread-header">
                <h2>{selected.subject || 'Message'}</h2>
                <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                  <ChannelBadge channel={selected.channel} />
                  <span>{selected.customer_name}</span>
                  <span className="text-muted">({selected.customer_email})</span>
                </div>
              </div>

              <div className="message-thread">
                <div className="message-bubble message-inbound">
                  <div className="message-bubble-body">{selected.body}</div>
                  <div className="message-bubble-time">{new Date(selected.created_at).toLocaleString()}</div>
                </div>

                {selected.ai_reply && (
                  <div className="message-bubble message-outbound">
                    <div className="message-bubble-label">AI Reply</div>
                    <div className="message-bubble-body">{selected.ai_reply}</div>
                    {selected.replied_at && <div className="message-bubble-time">{new Date(selected.replied_at).toLocaleString()}</div>}
                  </div>
                )}
              </div>

              {selected.status === 'open' && (
                <div className="message-reply-box">
                  <div className="reply-actions">
                    <button className="btn-ai" onClick={() => handleAiReply(selected)} disabled={aiLoading}>
                      {aiLoading ? 'Generating...' : '◆ AI Reply'}
                    </button>
                  </div>
                  <textarea
                    className="input reply-textarea"
                    value={replyText}
                    onChange={e => setReplyText(e.target.value)}
                    placeholder="Type your reply..."
                    rows={4}
                  />
                  <button className="btn-primary" onClick={handleSendReply} disabled={!replyText}>
                    Send Reply
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
              <p className="text-muted">Select a message to view</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
