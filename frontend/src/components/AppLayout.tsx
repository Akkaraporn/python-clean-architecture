import { Link, NavLink, Outlet } from 'react-router-dom'

import { useAuth } from '../features/auth'

export function AppLayout() {
  const { status, user } = useAuth()

  return (
    <div className="app">
      <header className="app-header">
        <Link to="/" className="brand">
          Clean Architecture Demo
        </Link>
        <nav aria-label="บัญชีผู้ใช้" className="app-nav">
          {status === 'authenticated' && user && (
            <NavLink to="/profile" title={user.email}>
              โปรไฟล์
            </NavLink>
          )}
          {status === 'unauthenticated' && (
            <>
              <NavLink to="/login">เข้าสู่ระบบ</NavLink>
              <NavLink to="/register">สมัครสมาชิก</NavLink>
            </>
          )}
        </nav>
      </header>
      <main className="app-main">
        <Outlet />
      </main>
    </div>
  )
}
