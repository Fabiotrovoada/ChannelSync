import { useState, useEffect } from 'react';
import { api } from '../api/client';

export default function AiStudio() {
  const [tone, setTone] = useState('professional');
  const [context, setContext] = useState('');
  const [draft, setDraft] = useState('');
  const [generating, setGenerating] = useState(false);
  const [autoReply, setAutoReply] = useState(false);
  const [config, setConfig] = useState({});
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    api.aiConfig().then(setConfig).catch(() => {});
  }, []);

  async function generate() {
    if (!context.trim()) return;
    setGenerating(true);
    try {
      const res = await api.aiCompose(context, tone);
      setDraft(res.draft || '');
    } finally {
      setGenerating(false);
    }
  }

  async function saveConfig(key, value) {
    await api.updateAiConfig({ [key]: value });
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  }

  const tones = ['professional', 'friendly', 'empathetic', 'firm'];
  const metrics = [
    { label: 'Replies Generated', value: 47, delta: '+12 this week' },
    { label: 'Time Saved', value: '94 min', delta: 'this month' },
    { label: 'Resolution Rate', value: '94%', delta: 'messages resolved' },
  ];

  return (
    <div className="page">
      <div className="page-header">
        <div className="page-title-row">
          <h1 className="page-title">AI Studio</h1>
          <p className="page-subtitle">Generate instant replies and configure auto-responses</p>
        </div>
        {saved && (
          <div style={{ fontSize: 13, color: 'var(--green)', fontWeight: 600 }}>✓ Saved</div>
        )}
      </div>

      {/* Metrics */}
      <div className="kpi-grid">
        {metrics.map(m => (
          <div key={m.label} className="kpi-card">
            <div className="kpi-value">{m.value}</div>
            <div className="kpi-label">{m.label}</div>
            <div className="kpi-delta" style={{ color: 'var(--text3)' }}>{m.delta}</div>
          </div>
        ))}
      </div>

      <div className="ai-layout">
        {/* Composer */}
        <div className="ai-panel">
          <div className="ai-panel-header">✨ Message Composer</div>
          <div className="ai-panel-body">
            <textarea
              className="form-textarea"
              value={context}
              onChange={e => setContext(e.target.value)}
              placeholder="Describe the message you want to send... e.g. 'Follow up with a customer about a delayed Amazon order, apologize sincerely and provide a new estimated delivery date'"
              rows={5}
              style={{ marginBottom: 12 }}
            />
            <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 12 }}>
              <select className="form-select" value={tone} onChange={e => setTone(e.target.value)} style={{ width: 'auto', minWidth: 140 }}>
                {tones.map(t => <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>)}
              </select>
              <button className="btn btn-ai" onClick={generate} disabled={generating || !context.trim()} style={{ flex: 1, justifyContent: 'center' }}>
                {generating ? '✨ Generating...' : '✨ Generate Message'}
              </button>
            </div>
            {draft && (
              <div style={{ background: 'var(--surface2)', border: '1px solid var(--accent)', borderRadius: 10, padding: 14 }}>
                <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--accent)', marginBottom: 8, textTransform: 'uppercase', letterSpacing: 0.5 }}>Generated Reply</div>
                <div style={{ fontSize: 14, lineHeight: 1.6, color: 'var(--text)', marginBottom: 12 }}>{draft}</div>
                <div style={{ display: 'flex', gap: 8 }}>
                  <button className="btn btn-ghost btn-sm" onClick={() => navigator.clipboard.writeText(draft)}>📋 Copy</button>
                  <button className="btn btn-ghost btn-sm" onClick={() => setDraft('')}>↺ Clear</button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Settings */}
        <div className="ai-panel">
          <div className="ai-panel-header">⚙️ Auto Reply Settings</div>
          <div className="ai-panel-body">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 0', borderBottom: '1px solid var(--border-light)' }}>
              <div>
                <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text)' }}>Enable Auto Reply</div>
                <div style={{ fontSize: 12, color: 'var(--text2)', marginTop: 2 }}>AI suggests replies to all incoming messages</div>
              </div>
              <div className={`toggle ${autoReply ? 'on' : ''}`} onClick={() => { const v = !autoReply; setAutoReply(v); saveConfig('auto_reply_enabled', v ? 1 : 0); }} />
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 0' }}>
              <div>
                <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text)' }}>Reply Tone</div>
                <div style={{ fontSize: 12, color: 'var(--text2)', marginTop: 2 }}>Default tone for AI-generated replies</div>
              </div>
              <select className="form-select" value={config.reply_tone || 'professional'} onChange={e => saveConfig('reply_tone', e.target.value)} style={{ width: 'auto', minWidth: 140 }}>
                {tones.map(t => <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>)}
              </select>
            </div>

            <div style={{ marginTop: 24 }}>
              <div className="section-title">Reply Templates</div>
              <p style={{ fontSize: 12, color: 'var(--text3)', marginBottom: 12 }}>Rule-based templates used when no OpenAI key is configured</p>
              {[
                { intent: 'where_is_my_order', label: 'Where is my order?', example: '"Hi {name}, your order #{id} was dispatched on {date} via {carrier}. Tracking: {tracking}. ETA: {eta}"' },
                { intent: 'wrong_item', label: 'Wrong item received', example: '"Hi {name}, so sorry! The correct item is being dispatched today with priority shipping."' },
                { intent: 'refund_request', label: 'Refund request', example: '"Hi {name}, your refund of £{amount} for order #{id} has been approved. Allow 3-5 working days."' },
                { intent: 'product_question', label: 'Product question', example: '"Hi {name}, great question about {product}. {answer}. Let me know if you need more details!"' },
              ].map(t => (
                <div key={t.intent} className="template-item">
                  <div className="template-label">{t.label}</div>
                  <div className="template-example">{t.example}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
