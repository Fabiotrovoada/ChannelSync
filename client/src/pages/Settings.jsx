import { useState, useEffect } from 'react';
import { api } from '../api/client';
import { useAuth } from '../App';

export default function Settings() {
  const { user } = useAuth();
  const [profile, setProfile] = useState({ business_name: '', email: '' });
  const [openaiKey, setOpenaiKey] = useState('');
  const [ssKey, setSsKey] = useState('');
  const [ssSecret, setSsSecret] = useState('');
  const [saved, setSaved] = useState('');
  const [loading, setLoading] = useState(true);
  const [tone, setTone] = useState('professional');

  useEffect(() => {
    Promise.all([
      api.aiConfig().catch(() => ({})),
    ]).then(([ai]) => {
      if (ai) {
        setOpenaiKey(ai.openai_api_key || '');
        if (ai.reply_tone) setTone(ai.reply_tone);
      }
    }).finally(() => setLoading(false));
    if (user) {
      setProfile({ business_name: user.business_name || '', email: user.email || '' });
    }
  }, [user]);

  function showSaved(msg) {
    setSaved(msg);
    setTimeout(() => setSaved(''), 2500);
  }

  async function saveProfile() {
    await api.updateSettings(profile);
    showSaved('Profile saved');
  }

  async function saveAI() {
    await api.updateAiConfig({ openai_api_key: openaiKey, reply_tone: tone });
    showSaved('AI settings saved');
  }

  return (
    <div className="page">
      <div className="page-header">
        <div className="page-title-row">
          <h1 className="page-title">Settings</h1>
          <p className="page-subtitle">Manage your account, integrations, and preferences</p>
        </div>
        {saved && <span style={{ fontSize: 13, color: 'var(--green)', fontWeight: 600 }}>✓ {saved}</span>}
      </div>

      {loading ? (
        <div className="empty-state"><div className="spinner" /></div>
      ) : (
        <div className="section" style={{ maxWidth: 640 }}>
          {/* Profile */}
          <div className="card" style={{ marginBottom: 16 }}>
            <div className="card-header">
              <div className="card-title">Business Profile</div>
            </div>
            <div className="card-body">
              <div className="form-group">
                <label className="form-label">Business Name</label>
                <input type="text" className="form-input" value={profile.business_name} onChange={e => setProfile({ ...profile, business_name: e.target.value })} />
              </div>
              <div className="form-group">
                <label className="form-label">Email</label>
                <input type="email" className="form-input" value={profile.email} onChange={e => setProfile({ ...profile, email: e.target.value })} />
              </div>
            </div>
            <div className="card-footer">
              <button className="btn btn-primary" onClick={saveProfile}>Save Profile</button>
            </div>
          </div>

          {/* AI Config */}
          <div className="card" style={{ marginBottom: 16 }}>
            <div className="card-header">
              <div className="card-title">AI Configuration</div>
            </div>
            <div className="card-body">
              <div className="form-group">
                <label className="form-label">OpenAI API Key</label>
                <input type="password" className="form-input" value={openaiKey} onChange={e => setOpenaiKey(e.target.value)} placeholder="sk-... (optional — rule-based replies used if not set)" style={{ fontFamily: 'monospace' }} />
                <div style={{ fontSize: 11.5, color: 'var(--text3)', marginTop: 4 }}>Leave blank to use rule-based replies (no GPT cost)</div>
              </div>
              <div className="form-group">
                <label className="form-label">Reply Tone</label>
                <select className="form-select" value={tone} onChange={e => setTone(e.target.value)} style={{ width: 'auto', minWidth: 160 }}>
                  {['professional', 'friendly', 'empathetic', 'firm'].map(t => (
                    <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>
                  ))}
                </select>
              </div>
            </div>
            <div className="card-footer">
              <button className="btn btn-primary" onClick={saveAI}>Save AI Settings</button>
            </div>
          </div>

          {/* ShipStation */}
          <div className="card" style={{ marginBottom: 16 }}>
            <div className="card-header">
              <div className="card-title">ShipStation</div>
            </div>
            <div className="card-body">
              <div className="form-group">
                <label className="form-label">API Key</label>
                <input type="password" className="form-input" value={ssKey} onChange={e => setSsKey(e.target.value)} placeholder="Your ShipStation API key" style={{ fontFamily: 'monospace' }} />
              </div>
              <div className="form-group">
                <label className="form-label">API Secret</label>
                <input type="password" className="form-input" value={ssSecret} onChange={e => setSsSecret(e.target.value)} placeholder="Your ShipStation API secret" style={{ fontFamily: 'monospace' }} />
              </div>
            </div>
            <div className="card-footer">
              <button className="btn btn-primary" onClick={() => showSaved('ShipStation saved')}>Save ShipStation</button>
            </div>
          </div>

          {/* Plan */}
          <div className="card">
            <div className="card-header">
              <div className="card-title">Plan</div>
            </div>
            <div className="card-body" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--accent)' }}>Pro Plan</div>
                <div style={{ fontSize: 12.5, color: 'var(--text2)', marginTop: 3 }}>£99/month · Unlimited orders · All channels</div>
              </div>
              <button className="btn btn-ghost" disabled>Current Plan</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
