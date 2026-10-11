import { Navigate, Outlet, useLocation } from 'react-router-dom'

import { useAuth } from '../features/auth'

export interface RedirectState {
  /** Where the user was heading before being sent to the login page. */
  from?: string
}

/**
 * Keeps signed-out users away from private pages. This is a user-experience
 * guard only: the real protection is the backend checking the token on every
 * request, which no client-side code can bypass.
 */
export function ProtectedRoute() {
  const { status } = useAuth()
  const location = useLocation()

  if (status === 'loading') {
    // A stored token is being verified; showing the login page now would flash.
    return (
      <p role="status" className="muted">
        กำลังตรวจสอบสถานะการเข้าสู่ระบบ…
      </p>
    )
  }

  if (status === 'unauthenticated') {
    const state: RedirectState = {
      from: `${location.pathname}${location.search}${location.hash}`,
    }
    return <Navigate to="/login" replace state={state} />
  }

  return <Outlet />
}
