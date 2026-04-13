import React, { useState, useEffect, createContext, useContext } from 'react'
import { BrowserRouter, Routes, Route, Navigate, NavLink, useNavigate } from 'react-router-dom'
import { api } from './api/client'

import Dashboard from './pages/Dashboard'
import Orders from './pages/Orders'
import OrderDetail from './pages/OrderDetail'
import Messages from './pages/Messages'
import Listings from './pages/Listings'
import Inventory from './pages/Inventory'
import PurchaseOrders from './pages/PurchaseOrders'
import Shipping from './pages/Shipping'
import AIStudio from './pages/AIStudio'
import Channels from './pages/Channels'
import Settings from './pages/Settings'
import AuditLog from './pages/AuditLog'
import Login from './pages/Login'
import Integrations from './pages/Integrations'

// Auth context
const AuthContext = createContext(null)
export const useAuth = () => useContext(AuthContext)

// Toast context
const ToastContext = createContext(null)
export const useToast = () => useContext(ToastContext)

function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([])

  const addToast = (message, type = 'info') => {
    const id = Date.now()
    setToasts(prev => [...prev, { id, message, type }])
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 3000)
  }

  return (
    <ToastContext.Provider value={addToast}>
      {children}
      <div className="toast-container">
        {toasts.map(t => (
          <div key={t.id} className={`toast toast-${t.type}`}>
            {t.message}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}

// Sidebar nav items
const NAV = [
  { to: '/', icon: '⊞', label: 'Dashboard' },
  { to: '/orders', icon: '⊞', label: 'Orders' },
  { to: '/messages', icon: '◉', label: 'Messages' },
  { to: '/listings', icon: '▤', label: 'Listings' },
  { to: '/inventory', icon: '▦', label: 'Inventory' },
  { to: '/purchase-orders', icon: '◧', label: 'Purchase Orders' },
  { to: '/shipping', icon: '▷', label: 'Shipping' },
  { to: '/ai-studio', icon: '◆', label: 'AI Studio' },
  { to: '/integrations', icon: '⊛', label: 'Integrations' },
  { to: '/channels', icon: '⊕', label: 'Channels' },
  { to: '/settings', icon: '⚙', label: 'Settings' },
  { to: '/audit-log', icon: '◫', label: 'Audit Log' },
]

function Sidebar({ mobileOpen, onClose }) {
  const navigate = useNavigate()
  const { user, setUser } = useAuth()

  const handleLogout = async () => {
    await api.logout()
    setUser(null)
    navigate('/login')
  }

  const handleNav = (to) => {
    navigate(to)
    onClose()
  }

  return (
    <>
      {/* Mobile overlay backdrop */}
      {mobileOpen && <div className="sidebar-backdrop" onClick={onClose} />}
      
      <aside className={`sidebar ${mobileOpen ? 'sidebar-mobile-open' : ''}`}>
        <div className="sidebar-header">
          <div className="sidebar-logo">
            <div className="sidebar-logo-icon">CS</div>
            <span className="sidebar-logo-text">ChannelSync</span>
          </div>
          <button className="sidebar-close-btn" onClick={onClose}>✕</button>
        </div>
        <nav className="sidebar-nav">
          {NAV.map(item => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) => `nav-item ${isActive ? 'nav-active' : ''}`}
              onClick={() => onClose()}
            >
              <span className="nav-icon">{item.icon}</span>
              <span className="nav-label">{item.label}</span>
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-footer">
          {user && (
            <div className="user-info">
              <div className="user-name">{user.business_name}</div>
              <div className="user-email">{user.email}</div>
            </div>
          )}
          <button className="btn btn-ghost btn-sm" onClick={handleLogout} style={{ width: '100%', justifyContent: 'center' }}>
            Sign out
          </button>
        </div>
      </aside>
    </>
  )
}

function AppShell() {
  const [mobileOpen, setMobileOpen] = useState(false)

  return (
    <div className="app-shell">
      {/* Mobile top bar */}
      <div className="mobile-topbar">
        <button className="hamburger-btn" onClick={() => setMobileOpen(true)}>
          <span /><span /><span />
        </button>
        <div className="mobile-logo">ChannelSync</div>
      </div>

      <Sidebar mobileOpen={mobileOpen} onClose={() => setMobileOpen(false)} />
      
      <main className="main-content">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/orders" element={<Orders />} />
          <Route path="/orders/:id" element={<OrderDetail />} />
          <Route path="/messages" element={<Messages />} />
          <Route path="/listings" element={<Listings />} />
          <Route path="/inventory" element={<Inventory />} />
          <Route path="/purchase-orders" element={<PurchaseOrders />} />
          <Route path="/shipping" element={<Shipping />} />
          <Route path="/ai-studio" element={<AIStudio />} />
          <Route path="/channels" element={<Channels />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/integrations" element={<Integrations />} />
          <Route path="/audit-log" element={<AuditLog />} />
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </main>
    </div>
  )
}

export default function App() {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.me()
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="loading-logo">CS</div>
        <div className="spinner" />
        <span style={{ fontSize: 14, color: 'var(--text2)', marginTop: 12 }}>ChannelSync</span>
      </div>
    )
  }

  return (
    <AuthContext.Provider value={{ user, setUser }}>
      <ToastProvider>
        <BrowserRouter>
          {user ? <AppShell /> : (
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route path="*" element={<Navigate to="/login" />} />
            </Routes>
          )}
        </BrowserRouter>
      </ToastProvider>
    </AuthContext.Provider>
  )
}
