import { useState, useEffect } from 'react';
import { api } from '../api/client';

export default function Settings() {
  const [profile, setProfile] = useState({ business_name: '', email: '' });
  const [openaiKey, setOpenaiKey] = useState('');
  const [ssKey, setSsKey] = useState('');
  const [ssSecret, setSsSecret] = useState('');
  const [saved, setSaved] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get('/api/auth/me').catch(() => null),
      api.get('/api/ai/config').catch(() => ({})),
    ]).then(([auth, ai]) => {
      if (auth) setProfile({ business_name: auth.business_name || '', email: auth.email || '' });
      if (ai) {
        setOpenaiKey(ai.openai_api_key || '');
        if (ai.reply_tone) setTone(ai.reply_tone);
      }
    }).finally(() => setLoading(false));
  }, []);

  async function saveProfile() {
    await api.post('/api/settings/profile', profile);
    showSaved();
  }

  async function saveAI() {
    await api.post('/api/ai/config', { openai_api_key: openaiKey });
    showSaved();
  }

  async function saveSS() {
    await api.post('/api/settings/shipstation', { api_key: ssKey, api_secret: ssSecret });
    showSaved();
  }

  function showSaved() {
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  }

  const [tone, setTone] = useState('professional');
  const [autoReply, setAutoReply] = useState(false);

  return (
    <div style={{ padding: '24px', maxWidth: '700px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px' }}>
        <div>
          <h1 style={{ fontSize: '20px', fontWeight: '800', color: 'var(--gold)', marginBottom: '4px' }}>Settings</h1>
          <p style={{ color: 'var(--text2)', fontSize: '13px' }}>Manage your account, integrations, and preferences</p>
        </div>
        {saved && <span style={{ fontSize: '12px', color: 'var(--green)', background: 'rgba(34,197,94,0.1)', padding: '4px 10px', borderRadius: '20px' }}>✓ Saved</span>}
      </div>

      {loading ? (
        <div style={{ color: 'var(--text3)', fontSize: '13px', padding: '40px', textAlign: 'center' }}>Loading...</div>
      ) : (
        <>
          {/* Profile */}
          <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '12px', padding: '20px', marginBottom: '16px' }}>
            <h2 style={{ fontSize: '14px', fontWeight: '700', color: 'var(--text)', marginBottom: '16px' }}>Business Profile</h2>
            <div style={{ marginBottom: '12px' }}>
              <label style={{ fontSize: '12px', fontWeight: '600', color: 'var(--text3)', display: 'block', marginBottom: '6px' }}>Business Name</label>
              <input type="text" value={profile.business_name} onChange={e => setProfile({ ...profile, business_name: e.target.value })} style={{ width: '100%', background: 'var(--bg3)', border: '1px solid var(--border)', borderRadius: '8px', padding: '9px 12px', fontSize: '13px', color: 'var(--text)', outline: 'none' }} />
            </div>
            <div style={{ marginBottom: '14px' }}>
              <label style={{ fontSize: '12px', fontWeight: '600', color: 'var(--text3)', display: 'block', marginBottom: '6px' }}>Email</label>
              <input type="email" value={profile.email} onChange={e => setProfile({ ...profile, email: e.target.value })} style={{ width: '100%', background: 'var(--bg3)', border: '1px solid var(--border)', borderRadius: '8px', padding: '9px 12px', fontSize: '13px', color: 'var(--text)', outline: 'none' }} />
            </div>
            <button onClick={saveProfile} style={{ background: 'var(--gold)', color: '#000', border: 'none', borderRadius: '8px', padding: '9px 18px', fontSize: '13px', fontWeight: '700', cursor: 'pointer' }}>Save Profile</button>
          </div>

          {/* AI Config */}
          <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '12px', padding: '20px', marginBottom: '16px' }}>
            <h2 style={{ fontSize: '14px', fontWeight: '700', color: 'var(--text)', marginBottom: '16px' }}>AI Configuration</h2>
            <div style={{ marginBottom: '14px' }}>
              <label style={{ fontSize: '12px', fontWeight: '600', color: 'var(--text3)', display: 'block', marginBottom: '6px' }}>OpenAI API Key</label>
              <input type="password" value={openaiKey} onChange={e => setOpenaiKey(e.target.value)} placeholder="sk-... (optional — rule-based replies used if not set)" style={{ width: '100%', background: 'var(--bg3)', border: '1px solid var(--border)', borderRadius: '8px', padding: '9px 12px', fontSize: '13px', color: 'var(--text)', outline: 'none', fontFamily: 'monospace' }} />
              <div style={{ fontSize: '11px', color: 'var(--text3)', marginTop: '4px' }}>Leave blank to use rule-based replies (no GPT cost). Set for AI-powered reply generation.</div>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 0', borderBottom: '1px solid var(--border)' }}>
              <div>
                <div style={{ fontSize: '13px', fontWeight: '600', color: 'var(--text)' }}>Reply Tone</div>
                <div style={{ fontSize: '12px', color: 'var(--text3)' }}>Default tone for AI-generated replies</div>
              </div>
              <select value={tone} onChange={e => setTone(e.target.value)} style={{ background: 'var(--bg3)', border: '1px solid var(--border)', borderRadius: '8px', padding: '8px 12px', fontSize: '13px', color: 'var(--text)', outline: 'none' }}>
                {['professional', 'friendly', 'empathetic', 'firm'].map(t => <option key={t} value={t} style={{ textTransform: 'capitalize' }}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>)}
              </select>
            </div>
            <button onClick={saveAI} style={{ marginTop: '14px', background: 'var(--gold)', color: '#000', border: 'none', borderRadius: '8px', padding: '9px 18px', fontSize: '13px', fontWeight: '700', cursor: 'pointer' }}>Save AI Settings</button>
          </div>

          {/* ShipStation */}
          <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '12px', padding: '20px', marginBottom: '16px' }}>
            <h2 style={{ fontSize: '14px', fontWeight: '700', color: 'var(--text)', marginBottom: '16px' }}>ShipStation</h2>
            <div style={{ marginBottom: '12px' }}>
              <label style={{ fontSize: '12px', fontWeight: '600', color: 'var(--text3)', display: 'block', marginBottom: '6px' }}>API Key</label>
              <input type="password" value={ssKey} onChange={e => setSsKey(e.target.value)} placeholder="Your ShipStation API key" style={{ width: '100%', background: 'var(--bg3)', border: '1px solid var(--border)', borderRadius: '8px', padding: '9px 12px', fontSize: '13px', color: 'var(--text)', outline: 'none', fontFamily: 'monospace' }} />
            </div>
            <div style={{ marginBottom: '14px' }}>
              <label style={{ fontSize: '12px', fontWeight: '600', color: 'var(--text3)', display: 'block', marginBottom: '6px' }}>API Secret</label>
              <input type="password" value={ssSecret} onChange={e => setSsSecret(e.target.value)} placeholder="Your ShipStation API secret" style={{ width: '100%', background: 'var(--bg3)', border: '1px solid var(--border)', borderRadius: '8px', padding: '9px 12px', fontSize: '13px', color: 'var(--text)', outline: 'none', fontFamily: 'monospace' }} />
            </div>
            <button onClick={saveSS} style={{ background: 'var(--gold)', color: '#000', border: 'none', borderRadius: '8px', padding: '9px 18px', fontSize: '13px', fontWeight: '700', cursor: 'pointer' }}>Save ShipStation</button>
          </div>

          {/* Plan */}
          <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '12px', padding: '20px', marginBottom: '16px' }}>
            <h2 style={{ fontSize: '14px', fontWeight: '700', color: 'var(--text)', marginBottom: '16px' }}>Plan</h2>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{ fontSize: '14px', fontWeight: '700', color: 'var(--gold)' }}>Pro Plan</div>
                <div style={{ fontSize: '12px', color: 'var(--text3)', marginTop: '2px' }}>£99/month · Unlimited orders · All channels</div>
              </div>
              <button disabled style={{ background: 'var(--bg4)', color: 'var(--text3)', border: '1px solid var(--border)', borderRadius: '8px', padding: '9px 18px', fontSize: '13px', cursor: 'not-allowed' }}>Current Plan</button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
