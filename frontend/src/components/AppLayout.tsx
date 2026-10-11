import { Link, Outlet } from 'react-router-dom'

export function AppLayout() {
  return (
    <div className="app">
      <header className="app-header">
        <Link to="/" className="brand">
          Clean Architecture Demo
        </Link>
      </header>
      <main className="app-main">
        <Outlet />
      </main>
    </div>
  )
}
