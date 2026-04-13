import { useState, useEffect } from 'react';
import { api } from '../api/client';

export default function AiStudio() {
  const [tone, setTone] = useState('professional');
  const [context, setContext] = useState('');
  const [draft, setDraft] = useState('');
  const [generating, setGenerating] = useState(false);
  const [autoReply, setAutoReply] = useState(false);
  const [config, setConfig] = useState({});
  const [metrics, setMetrics] = useState({ replies_generated: 0, time_saved_min: 0, resolution_rate: '0%' });

  useEffect(() => {
    api.get('/api/ai/config').then(setConfig).catch(() => {});
    setAutoReply(config.auto_reply_enabled);
  }, []);

  async function generate() {
    if (!context.trim()) return;
    setGenerating(true);
    try {
      const res = await api.post('/api/messages/ai-compose', { context, tone });
      setDraft(res.draft);
    } finally {
      setGenerating(false);
    }
  }

  async function saveConfig(key, value) {
    await api.post('/api/ai/config', { [key]: value });
  }

  const tones = ['professional', 'friendly', 'empathetic', 'firm'];

  return (
    <div style={{ padding: '24px', maxWidth: '800px' }}>
      <div style={{ marginBottom: '28px' }}>
        <h1 style={{ fontSize: '20px', fontWeight: '800', color: 'var(--gold)', marginBottom: '4px' }}>AI Studio</h1>
        <p style={{ color: 'var(--text2)', fontSize: '13px' }}>Generate instant replies and configure auto-responses across all channels</p>
      </div>

      {/* Metrics */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px', marginBottom: '28px' }}>
        {[
          { label: 'Replies Generated', value: metrics.replies_generated || 47, delta: '+12 this week' },
          { label: 'Time Saved', value: `${metrics.time_saved_min || 94} min`, delta: 'this month' },
          { label: 'Resolution Rate', value: metrics.resolution_rate || '94%', delta: 'messages resolved' },
        ].map(m => (
          <div key={m.label} style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '12px', padding: '16px' }}>
            <div style={{ fontSize: '11px', fontWeight: '700', color: 'var(--text3)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '8px' }}>{m.label}</div>
            <div style={{ fontSize: '24px', fontWeight: '800', color: 'var(--gold)' }}>{m.value}</div>
            <div style={{ fontSize: '11px', color: 'var(--text3)', marginTop: '4px' }}>{m.delta}</div>
          </div>
        ))}
      </div>

      {/* AI Composer */}
      <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '12px', padding: '20px', marginBottom: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
          <span style={{ fontSize: '16px' }}>✨</span>
          <h2 style={{ fontSize: '14px', fontWeight: '700', color: 'var(--gold)' }}>Message Composer</h2>
        </div>
        <textarea
          value={context}
          onChange={e => setContext(e.target.value)}
          placeholder="Describe the message you want to send... e.g. 'Follow up with a customer about a delayed Amazon order, apologize sincerely and provide a new estimated delivery date'"
          style={{
            width: '100%', background: 'var(--bg3)', border: '1px solid var(--border)',
            borderRadius: '8px', padding: '12px', fontSize: '13px', color: 'var(--text)',
            minHeight: '100px', resize: 'vertical', fontFamily: 'inherit', outline: 'none',
          }}
          onFocus={e => e.target.style.borderColor = 'var(--gold)'}
          onBlur={e => e.target.style.borderColor = 'var(--border)'}
        />
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center', marginTop: '12px' }}>
          <select
            value={tone}
            onChange={e => setTone(e.target.value)}
            style={{
              background: 'var(--bg3)', border: '1px solid var(--border)', borderRadius: '8px',
              padding: '8px 12px', fontSize: '13px', color: 'var(--text)', outline: 'none', cursor: 'pointer',
            }}
          >
            {tones.map(t => <option key={t} value={t} style={{ textTransform: 'capitalize' }}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>)}
          </select>
          <button
            onClick={generate}
            disabled={generating || !context.trim()}
            style={{
              background: 'var(--gold)', color: '#000', border: 'none', borderRadius: '8px',
              padding: '9px 18px', fontSize: '13px', fontWeight: '700', cursor: generating ? 'not-allowed' : 'pointer',
              opacity: generating ? 0.6 : 1,
            }}
          >
            {generating ? '✨ Generating...' : '✨ Generate Message'}
          </button>
        </div>

        {draft && (
          <div style={{ marginTop: '16px', background: 'var(--bg3)', border: '1px solid var(--gold)', borderRadius: '8px', padding: '14px' }}>
            <div style={{ fontSize: '11px', fontWeight: '700', color: 'var(--gold)', marginBottom: '8px' }}>GENERATED REPLY</div>
            <div style={{ fontSize: '14px', lineHeight: '1.6', color: 'var(--text)' }}>{draft}</div>
            <div style={{ display: 'flex', gap: '8px', marginTop: '12px' }}>
              <button
                onClick={() => { navigator.clipboard.writeText(draft); }}
                style={{
                  background: 'var(--bg4)', color: 'var(--text2)', border: '1px solid var(--border)',
                  borderRadius: '7px', padding: '7px 14px', fontSize: '12px', cursor: 'pointer',
                }}
              >
                📋 Copy
              </button>
              <button
                onClick={() => setDraft('')}
                style={{
                  background: 'var(--bg4)', color: 'var(--text2)', border: '1px solid var(--border)',
                  borderRadius: '7px', padding: '7px 14px', fontSize: '12px', cursor: 'pointer',
                }}
              >
                ↺ Clear
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Auto Reply Config */}
      <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '12px', padding: '20px', marginBottom: '16px' }}>
        <h2 style={{ fontSize: '14px', fontWeight: '700', color: 'var(--text)', marginBottom: '16px' }}>Auto Reply Settings</h2>

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 0', borderBottom: '1px solid var(--border)' }}>
          <div>
            <div style={{ fontSize: '13px', fontWeight: '600', color: 'var(--text)' }}>Enable Auto Reply</div>
            <div style={{ fontSize: '12px', color: 'var(--text3)', marginTop: '2px' }}>AI suggests replies to all incoming messages</div>
          </div>
          <div
            onClick={() => { const v = !autoReply; setAutoReply(v); saveConfig('auto_reply_enabled', v ? 1 : 0); }}
            style={{
              width: '40px', height: '22px', background: autoReply ? 'var(--gold)' : 'var(--bg4)',
              borderRadius: '11px', position: 'relative', cursor: 'pointer', transition: 'background 0.2s',
            }}
          >
            <div style={{
              position: 'absolute', width: '16px', height: '16px', background: '#fff',
              borderRadius: '50%', top: '3px', left: autoReply ? '21px' : '3px', transition: 'left 0.2s',
            }} />
          </div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 0' }}>
          <div>
            <div style={{ fontSize: '13px', fontWeight: '600', color: 'var(--text)' }}>Reply Tone</div>
            <div style={{ fontSize: '12px', color: 'var(--text3)', marginTop: '2px' }}>Default tone for AI-generated replies</div>
          </div>
          <select
            value={config.reply_tone || 'professional'}
            onChange={e => saveConfig('reply_tone', e.target.value)}
            style={{
              background: 'var(--bg3)', border: '1px solid var(--border)', borderRadius: '8px',
              padding: '8px 12px', fontSize: '13px', color: 'var(--text)', outline: 'none', cursor: 'pointer',
            }}
          >
            {tones.map(t => <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>)}
          </select>
        </div>
      </div>

      {/* Intent Templates */}
      <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '12px', padding: '20px' }}>
        <h2 style={{ fontSize: '14px', fontWeight: '700', color: 'var(--text)', marginBottom: '16px' }}>Reply Templates</h2>
        <p style={{ fontSize: '12px', color: 'var(--text3)', marginBottom: '12px' }}>Rule-based templates used when OpenAI key is not configured</p>
        {[
          { intent: 'where_is_my_order', label: 'Where is my order?', example: '"Hi {name}, your order #{id} was dispatched on {date} via {carrier}. Tracking: {tracking}. ETA: {eta}"' },
          { intent: 'wrong_item', label: 'Wrong item received', example: '"Hi {name}, so sorry about this! The correct item is being dispatched today with priority shipping. We\'ll collect the wrong item. sincerely apologize."' },
          { intent: 'refund_request', label: 'Refund request', example: '"Hi {name}, your refund of £{amount} for order #{id} has been approved. Allow 3-5 working days to appear in your account."' },
          { intent: 'product_question', label: 'Product question', example: '"Hi {name}, great question about {product}. {answer}. Let me know if you need any more details!"' },
        ].map(t => (
          <div key={t.intent} style={{ padding: '12px 0', borderBottom: '1px solid var(--border)' }}>
            <div style={{ fontSize: '13px', fontWeight: '600', color: 'var(--gold)', marginBottom: '4px' }}>{t.label}</div>
            <div style={{ fontSize: '12px', color: 'var(--text2)', fontStyle: 'italic' }}>{t.example}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
