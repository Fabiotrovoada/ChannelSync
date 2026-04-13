import React, { useState } from 'react'
import { api } from '../api/client'
import { useAuth } from '../App'

export default function Login() {
  const { setUser } = useAuth()
  const [email, setEmail] = useState('fabio@ftpaints.co.uk')
  const [password, setPassword] = useState('demo1234')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const user = await api.login(email, password)
      setUser(user)
    } catch (err) {
      setError(err.error || 'Login failed. Please check your credentials.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-logo">CS</div>
        <h1 className="login-title">ChannelSync</h1>
        <p className="login-sub">Your ecommerce command centre</p>

        <form className="login-form" onSubmit={handleSubmit}>
          {error && (
            <div style={{ padding: '10px 14px', background: 'var(--red-light)', color: 'var(--red)', borderRadius: 6, fontSize: '13.5px', border: '1px solid var(--red)' }}>
              {error}
            </div>
          )}
          <div className="form-group">
            <label className="form-label">Email</label>
            <input
              type="email"
              className="input"
              value={email}
              onChange={e => setEmail(e.target.value)}
              required
              autoComplete="email"
            />
          </div>
          <div className="form-group">
            <label className="form-label">Password</label>
            <input
              type="password"
              className="input"
              value={password}
              onChange={e => setPassword(e.target.value)}
              required
              autoComplete="current-password"
            />
          </div>
          <button type="submit" className="btn btn-primary btn-lg" disabled={loading} style={{ width: '100%', justifyContent: 'center' }}>
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <div className="demo-hint">
          <strong>Demo account:</strong> fabio@ftpaints.co.uk / demo1234
        </div>
      </div>
    </div>
  )
}
