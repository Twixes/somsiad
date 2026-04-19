import { useEffect, useState } from 'react'
import { Routes, Route, Navigate, NavLink, useLocation } from 'react-router-dom'
import { getMe, logout, type User } from './api'
import { Login } from './pages/Login'
import { Dashboard } from './pages/Dashboard'
import { Birthday } from './pages/Birthday'
import { Reminders } from './pages/Reminders'
import { Commands } from './pages/Commands'
import { Moderation } from './pages/Moderation'
import { Polls } from './pages/Polls'
import { Burns } from './pages/Burns'
import { Oof } from './pages/Oof'


const TITLES: Record<string, string> = {
  '/': 'Panel',
  '/urodziny': 'Urodziny',
  '/przypomnienia': 'Przypomnienia',
  '/komendy': 'Komendy',
  '/kartoteka': 'Kartoteka',
  '/glosowania': 'Głosowania',
  '/spalenia': 'Spalenia',
  '/oof': 'Oof',
}

export function App() {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const location = useLocation()

  useEffect(() => {
    getMe().then((u) => {
      setUser(u)
      setLoading(false)
    })
  }, [])

  useEffect(() => {
    setSidebarOpen(false)
  }, [location.pathname])

  if (loading) return null
  if (!user) return <Login />

  const handleLogout = async () => {
    await logout()
    setUser(null)
  }

  const title = TITLES[location.pathname] || 'Panel'

  return (
    <div className={sidebarOpen ? 'sidebar-open' : undefined}>
      <aside className="sidebar">
        <div className="sidebar__header">
          <a href="/" className="sidebar__logo">Somsiad</a>
          <span className="sidebar__subtitle">Panel sterowania</span>
        </div>
        <nav className="sidebar__nav">
          <NavLink to="/" end className={({ isActive }) => `sidebar__link${isActive ? ' sidebar__link--active' : ''}`}>
            <span className="sidebar__icon">📊</span>Panel
          </NavLink>
          <NavLink to="/urodziny" className={({ isActive }) => `sidebar__link${isActive ? ' sidebar__link--active' : ''}`}>
            <span className="sidebar__icon">🎂</span>Urodziny
          </NavLink>
          <NavLink to="/przypomnienia" className={({ isActive }) => `sidebar__link${isActive ? ' sidebar__link--active' : ''}`}>
            <span className="sidebar__icon">🍅</span>Przypomnienia
          </NavLink>
          <NavLink to="/komendy" className={({ isActive }) => `sidebar__link${isActive ? ' sidebar__link--active' : ''}`}>
            <span className="sidebar__icon">📈</span>Komendy
          </NavLink>
          <NavLink to="/kartoteka" className={({ isActive }) => `sidebar__link${isActive ? ' sidebar__link--active' : ''}`}>
            <span className="sidebar__icon">📂</span>Kartoteka
          </NavLink>
          <NavLink to="/glosowania" className={({ isActive }) => `sidebar__link${isActive ? ' sidebar__link--active' : ''}`}>
            <span className="sidebar__icon">🗳</span>Głosowania
          </NavLink>
          <NavLink to="/spalenia" className={({ isActive }) => `sidebar__link${isActive ? ' sidebar__link--active' : ''}`}>
            <span className="sidebar__icon">🔥</span>Spalenia
          </NavLink>
          <NavLink to="/oof" className={({ isActive }) => `sidebar__link${isActive ? ' sidebar__link--active' : ''}`}>
            <span className="sidebar__icon">💨</span>Oof
          </NavLink>

        </nav>
        <div className="sidebar__footer">
          <div className="sidebar__user">
            <img src={user.avatar_url} className="sidebar__avatar" alt="" />
            <span className="sidebar__username">{user.display_name}</span>
          </div>
          <button className="sidebar__link sidebar__link--logout" onClick={handleLogout} type="button">
            <span className="sidebar__icon">🚪</span>Wyloguj się
          </button>
        </div>
      </aside>
      <div className="sidebar-overlay" onClick={() => setSidebarOpen(false)} />
      <main className="panel-content">
        <header className="panel-content__header">
          <button
            className="sidebar-toggle"
            onClick={() => setSidebarOpen((v) => !v)}
            type="button"
            aria-label="Menu"
          >
            <span /><span /><span />
          </button>
          <h1 className="panel-content__title">{title}</h1>
        </header>
        <div className="panel-content__body">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/urodziny" element={<Birthday />} />
            <Route path="/przypomnienia" element={<Reminders />} />
            <Route path="/komendy" element={<Commands />} />
            <Route path="/kartoteka" element={<Moderation />} />
            <Route path="/glosowania" element={<Polls />} />
            <Route path="/spalenia" element={<Burns />} />
            <Route path="/oof" element={<Oof />} />

            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </div>
      </main>
    </div>
  )
}
