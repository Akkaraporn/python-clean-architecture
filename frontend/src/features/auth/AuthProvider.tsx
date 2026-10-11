import { type ReactNode, useCallback, useEffect, useMemo, useState } from 'react'

import * as authApi from '../../api/auth'
import { isAbortError, onUnauthorized } from '../../api/client'
import { TOKEN_STORAGE_KEY, tokenStorage } from '../../api/tokenStorage'
import type { LoginPayload, RegisterPayload, User } from '../../api/types'
import { AuthContext, type AuthContextValue, type AuthStatus } from './AuthContext'

interface AuthState {
  status: AuthStatus
  user: User | null
}

const SIGNED_OUT: AuthState = { status: 'unauthenticated', user: null }

function initialState(): AuthState {
  return tokenStorage.get() ? { status: 'loading', user: null } : SIGNED_OUT
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>(initialState)

  // A token in storage only means "was signed in"; /me confirms it is still valid.
  useEffect(() => {
    if (!tokenStorage.get()) {
      return
    }
    const controller = new AbortController()
    authApi
      .getMe(controller.signal)
      .then((user) => setState({ status: 'authenticated', user }))
      .catch((error: unknown) => {
        if (!isAbortError(error)) {
          setState(SIGNED_OUT)
        }
      })
    return () => controller.abort()
  }, [])

  // Any authenticated request answered with 401 ends the session everywhere.
  useEffect(() => onUnauthorized(() => setState(SIGNED_OUT)), [])

  // Logging out in one tab logs out the others.
  useEffect(() => {
    function handleStorage(event: StorageEvent) {
      if (event.key === TOKEN_STORAGE_KEY && event.newValue === null) {
        setState(SIGNED_OUT)
      }
    }
    window.addEventListener('storage', handleStorage)
    return () => window.removeEventListener('storage', handleStorage)
  }, [])

  const login = useCallback(async (payload: LoginPayload) => {
    const { access_token } = await authApi.login(payload)
    tokenStorage.set(access_token)
    try {
      const user = await authApi.getMe()
      setState({ status: 'authenticated', user })
    } catch (error) {
      tokenStorage.clear()
      setState(SIGNED_OUT)
      throw error
    }
  }, [])

  const register = useCallback(
    async (payload: RegisterPayload) => {
      await authApi.register(payload)
      await login({ email: payload.email, password: payload.password })
    },
    [login],
  )

  const logout = useCallback(() => {
    tokenStorage.clear()
    setState(SIGNED_OUT)
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({ ...state, login, register, logout }),
    [state, login, register, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
