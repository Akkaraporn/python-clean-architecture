import { createContext } from 'react'

import type { LoginPayload, RegisterPayload, User } from '../../api/types'

/**
 * `loading` while a stored token is being checked against the API on page load,
 * so route guards can wait instead of flashing the login page.
 */
export type AuthStatus = 'loading' | 'authenticated' | 'unauthenticated'

export interface AuthContextValue {
  status: AuthStatus
  user: User | null
  login(payload: LoginPayload): Promise<void>
  /** Creates the account, then signs in with the same credentials. */
  register(payload: RegisterPayload): Promise<void>
  logout(): void
}

export const AuthContext = createContext<AuthContextValue | null>(null)
