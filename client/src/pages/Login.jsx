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
      setError(err.error || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-logo">
          <span className="logo-icon" style={{ fontSize: 32 }}>◈</span>
          <h1>VendStack</h1>
          <p className="text-muted">Ecommerce Command Centre</p>
        </div>
        <form onSubmit={handleSubmit}>
          {error && <div className="form-error">{error}</div>}
          <div className="form-group">
            <label>Email</label>
            <input type="email" value={email} onChange={e => setEmail(e.target.value)} required />
          </div>
          <div className="form-group">
            <label>Password</label>
            <input type="password" value={password} onChange={e => setPassword(e.target.value)} required />
          </div>
          <button type="submit" className="btn-primary" disabled={loading} style={{ width: '100%' }}>
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>
        <p className="login-hint">Demo: fabio@ftpaints.co.uk / demo1234</p>
      </div>
    </div>
  )
}
