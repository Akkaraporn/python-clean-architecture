import { act, cleanup, render, screen, waitFor } from '@testing-library/react'
import { useEffect } from 'react'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'

import { apiRequest } from '../../api/client'
import { TOKEN_STORAGE_KEY, tokenStorage } from '../../api/tokenStorage'
import type { User } from '../../api/types'
import { jsonResponse, mockFetch, requestHeaders } from '../../test/http'
import type { AuthContextValue } from './AuthContext'
import { AuthProvider } from './AuthProvider'
import { useAuth } from './useAuth'

const JANE: User = {
  id: '6f1c2c8e-0000-4000-8000-000000000001',
  email: 'jane@example.com',
  full_name: 'Jane Doe',
  is_active: true,
  created_at: '2030-01-01T00:00:00Z',
}

let auth: AuthContextValue

function Probe() {
  const value = useAuth()
  // Exposes the latest context value to the test body after each render.
  useEffect(() => {
    auth = value
  })
  return <p data-testid="status">{value.status}</p>
}

function renderProvider() {
  render(
    <AuthProvider>
      <Probe />
    </AuthProvider>,
  )
}

function status(): string | null {
  return screen.getByTestId('status').textContent
}

beforeEach(() => {
  tokenStorage.clear()
})

afterEach(() => {
  cleanup()
  tokenStorage.clear()
})

describe('AuthProvider', () => {
  it('starts signed out when no token is stored, without calling the API', () => {
    const fetchMock = mockFetch()

    renderProvider()

    expect(status()).toBe('unauthenticated')
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('restores the session from a stored token after a page reload', async () => {
    tokenStorage.set('stored-token')
    const fetchMock = mockFetch(jsonResponse(200, JANE))

    renderProvider()

    // Waits on /me instead of assuming the token is still good.
    expect(status()).toBe('loading')
    await waitFor(() => expect(status()).toBe('authenticated'))
    expect(auth.user).toEqual(JANE)
    expect(requestHeaders(fetchMock).Authorization).toBe('Bearer stored-token')
  })

  it('drops a stored token that the API rejects', async () => {
    tokenStorage.set('expired-token')
    mockFetch(jsonResponse(401, { detail: 'Token has expired', code: 'token_expired' }))

    renderProvider()

    await waitFor(() => expect(status()).toBe('unauthenticated'))
    expect(tokenStorage.get()).toBeNull()
  })

  it('login stores the token and loads the user', async () => {
    mockFetch(
      jsonResponse(200, { access_token: 'new-token', token_type: 'bearer' }),
      jsonResponse(200, JANE),
    )
    renderProvider()

    await act(() => auth.login({ email: JANE.email, password: 'pw' }))

    expect(status()).toBe('authenticated')
    expect(auth.user).toEqual(JANE)
    expect(tokenStorage.get()).toBe('new-token')
  })

  it('a failed login keeps the user signed out and rethrows', async () => {
    mockFetch(jsonResponse(401, { detail: 'Invalid email or password', code: 'invalid_credentials' }))
    renderProvider()

    await expect(auth.login({ email: JANE.email, password: 'wrong' })).rejects.toMatchObject({
      code: 'invalid_credentials',
    })
    expect(status()).toBe('unauthenticated')
    expect(tokenStorage.get()).toBeNull()
  })

  it('register creates the account and signs in', async () => {
    const fetchMock = mockFetch(
      jsonResponse(201, JANE),
      jsonResponse(200, { access_token: 'new-token', token_type: 'bearer' }),
      jsonResponse(200, JANE),
    )
    renderProvider()

    await act(() => auth.register({ email: JANE.email, password: 'pw', full_name: 'Jane Doe' }))

    expect(status()).toBe('authenticated')
    expect(fetchMock.mock.calls.map((call) => call[0])).toEqual([
      'http://api.test/api/auth/register',
      'http://api.test/api/auth/login',
      'http://api.test/api/users/me',
    ])
  })

  it('logout clears the token and the user', async () => {
    tokenStorage.set('stored-token')
    mockFetch(jsonResponse(200, JANE))
    renderProvider()
    await waitFor(() => expect(status()).toBe('authenticated'))

    act(() => auth.logout())

    expect(status()).toBe('unauthenticated')
    expect(auth.user).toBeNull()
    expect(tokenStorage.get()).toBeNull()
  })

  it('signs out when any authenticated request gets a 401', async () => {
    tokenStorage.set('stored-token')
    mockFetch(
      jsonResponse(200, JANE),
      jsonResponse(401, { detail: 'Invalid token', code: 'invalid_token' }),
    )
    renderProvider()
    await waitFor(() => expect(status()).toBe('authenticated'))

    await act(async () => {
      await apiRequest('/api/users/me', { auth: true }).catch(() => undefined)
    })

    expect(status()).toBe('unauthenticated')
  })

  it('signs out when another tab removes the token', async () => {
    tokenStorage.set('stored-token')
    mockFetch(jsonResponse(200, JANE))
    renderProvider()
    await waitFor(() => expect(status()).toBe('authenticated'))

    act(() => {
      window.dispatchEvent(
        new StorageEvent('storage', { key: TOKEN_STORAGE_KEY, newValue: null }),
      )
    })

    expect(status()).toBe('unauthenticated')
  })

  it('useAuth outside the provider fails with a clear message', () => {
    expect(() => render(<Probe />)).toThrow('useAuth must be used inside <AuthProvider>')
  })
})
