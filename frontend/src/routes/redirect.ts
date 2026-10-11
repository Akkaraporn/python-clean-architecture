import type { RedirectState } from './ProtectedRoute'

export const DEFAULT_AFTER_LOGIN = '/profile'

/**
 * Where to go after signing in. Only same-site paths are accepted, so a crafted
 * link cannot bounce the user to another website (open redirect).
 */
export function redirectTarget(state: unknown): string {
  const from = (state as RedirectState | null)?.from
  if (typeof from !== 'string' || !from.startsWith('/') || from.startsWith('//')) {
    return DEFAULT_AFTER_LOGIN
  }
  if (from.startsWith('/login') || from.startsWith('/register')) {
    return DEFAULT_AFTER_LOGIN
  }
  return from
}
