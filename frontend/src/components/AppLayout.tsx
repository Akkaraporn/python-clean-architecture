import { Link, Outlet } from 'react-router-dom'

import { useAuth } from '../features/auth'

export function AppLayout() {
  const { status, user } = useAuth()

  return (
    <div className="app">
      <header className="app-header">
        <Link to="/" className="brand">
          Clean Architecture Demo
        </Link>
        {status === 'authenticated' && user && <span className="muted">{user.email}</span>}
      </header>
      <main className="app-main">
        <Outlet />
      </main>
    </div>
  )
}
