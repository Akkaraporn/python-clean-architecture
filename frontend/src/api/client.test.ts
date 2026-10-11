import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { jsonResponse, mockFetch, requestHeaders } from '../test/http'
import { ApiError, apiRequest, onUnauthorized } from './client'
import { tokenStorage } from './tokenStorage'

async function captureError(promise: Promise<unknown>): Promise<ApiError> {
  try {
    await promise
  } catch (error) {
    if (error instanceof ApiError) {
      return error
    }
    throw error
  }
  throw new Error('expected the request to fail')
}

beforeEach(() => {
  tokenStorage.clear()
})

afterEach(() => {
  tokenStorage.clear()
})

describe('apiRequest', () => {
  it('prefixes the base URL and returns parsed JSON', async () => {
    const fetchMock = mockFetch(jsonResponse(200, { status: 'ok' }))

    await expect(apiRequest('/health')).resolves.toEqual({ status: 'ok' })
    expect(fetchMock.mock.calls[0]?.[0]).toBe('http://api.test/health')
  })

  it('sends a JSON body with a content type', async () => {
    const fetchMock = mockFetch(jsonResponse(201, {}))

    await apiRequest('/api/auth/register', { method: 'POST', body: { email: 'a@b.co' } })

    const init = fetchMock.mock.calls[0]?.[1]
    expect(init?.method).toBe('POST')
    expect(init?.body).toBe('{"email":"a@b.co"}')
    expect(requestHeaders(fetchMock)['Content-Type']).toBe('application/json')
  })

  it('attaches the stored token only to authenticated requests', async () => {
    tokenStorage.set('abc')
    const fetchMock = mockFetch(jsonResponse(200, {}), jsonResponse(200, {}))

    await apiRequest('/api/users/me', { auth: true })
    await apiRequest('/api/auth/login', { method: 'POST', body: {} })

    expect(requestHeaders(fetchMock, 0).Authorization).toBe('Bearer abc')
    expect(requestHeaders(fetchMock, 1).Authorization).toBeUndefined()
  })

  it('turns a domain error body into an ApiError with its code', async () => {
    mockFetch(jsonResponse(409, { detail: 'already exists', code: 'user_already_exists' }))

    const error = await captureError(apiRequest('/api/auth/register', { method: 'POST' }))

    expect(error.status).toBe(409)
    expect(error.code).toBe('user_already_exists')
    expect(error.message).toBe('already exists')
  })

  it('does not trust an unknown error code from the server', async () => {
    mockFetch(jsonResponse(400, { detail: 'odd', code: 'something_new' }))

    const error = await captureError(apiRequest('/x'))

    expect(error.code).toBe('unknown_error')
  })

  it('maps FastAPI validation errors to per-field messages', async () => {
    mockFetch(
      jsonResponse(422, {
        detail: [
          { loc: ['body', 'email'], msg: 'not a valid email', type: 'value_error' },
          { loc: ['body', 'password'], msg: 'too short', type: 'string_too_short' },
          { loc: ['body', 'password'], msg: 'second message is ignored', type: 'x' },
        ],
      }),
    )

    const error = await captureError(apiRequest('/api/auth/register', { method: 'POST' }))

    expect(error.code).toBe('validation_error')
    expect(error.fieldErrors).toEqual({ email: 'not a valid email', password: 'too short' })
  })

  it('handles an error response that is not JSON', async () => {
    mockFetch(new Response('<html>Bad Gateway</html>', { status: 502 }))

    const error = await captureError(apiRequest('/health'))

    expect(error.status).toBe(502)
    expect(error.code).toBe('unknown_error')
  })

  it('reports an unreachable server as a network error', async () => {
    vi.stubGlobal('fetch', vi.fn<typeof fetch>().mockRejectedValue(new TypeError('Failed to fetch')))

    const error = await captureError(apiRequest('/health'))

    expect(error.status).toBe(0)
    expect(error.code).toBe('network_error')
  })

  it('passes an abort through unchanged', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn<typeof fetch>().mockRejectedValue(new DOMException('aborted', 'AbortError')),
    )

    await expect(apiRequest('/health')).rejects.toMatchObject({ name: 'AbortError' })
  })
})

describe('401 handling', () => {
  it('clears the token and notifies listeners when an authenticated request is rejected', async () => {
    tokenStorage.set('expired-token')
    mockFetch(jsonResponse(401, { detail: 'Token has expired', code: 'token_expired' }))
    const listener = vi.fn()
    const unsubscribe = onUnauthorized(listener)

    const error = await captureError(apiRequest('/api/users/me', { auth: true }))

    expect(error.code).toBe('token_expired')
    expect(tokenStorage.get()).toBeNull()
    expect(listener).toHaveBeenCalledOnce()
    unsubscribe()
  })

  it('leaves the session alone when a login attempt fails', async () => {
    tokenStorage.set('still-valid')
    mockFetch(jsonResponse(401, { detail: 'Invalid email or password', code: 'invalid_credentials' }))
    const listener = vi.fn()
    const unsubscribe = onUnauthorized(listener)

    await captureError(apiRequest('/api/auth/login', { method: 'POST', body: {} }))

    expect(tokenStorage.get()).toBe('still-valid')
    expect(listener).not.toHaveBeenCalled()
    unsubscribe()
  })

  it('stops notifying after unsubscribe', async () => {
    tokenStorage.set('t')
    mockFetch(jsonResponse(401, { detail: 'x', code: 'invalid_token' }))
    const listener = vi.fn()
    onUnauthorized(listener)()

    await captureError(apiRequest('/api/users/me', { auth: true }))

    expect(listener).not.toHaveBeenCalled()
  })
})
