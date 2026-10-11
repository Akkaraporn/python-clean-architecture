import { cleanup, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'

import { tokenStorage } from '../api/tokenStorage'
import { jsonResponse, mockFetch } from '../test/http'
import { deferred, JANE, renderApp } from '../test/renderApp'

const TOKEN = { access_token: 'new-token', token_type: 'bearer' }
const EXPIRED = { detail: 'Token has expired', code: 'token_expired' }

beforeEach(() => tokenStorage.clear())
afterEach(() => {
  cleanup()
  tokenStorage.clear()
})

describe('ProtectedRoute', () => {
  it('sends a signed-out visitor to login, then back to the page they wanted', async () => {
    mockFetch(jsonResponse(200, TOKEN), jsonResponse(200, JANE), jsonResponse(200, JANE))
    const { user, router } = renderApp('/profile')

    await waitFor(() => expect(router.state.location.pathname).toBe('/login'))
    await user.type(screen.getByLabelText('อีเมล'), 'jane@example.com')
    await user.type(screen.getByLabelText('รหัสผ่าน'), 's3cret-pass{Enter}')

    await waitFor(() => expect(router.state.location.pathname).toBe('/profile'))
    expect(await screen.findByText('jane@example.com')).toBeTruthy()
  })

  it('waits for the stored token to be checked instead of flashing the login page', async () => {
    tokenStorage.set('stored-token')
    const session = deferred<Response>()
    const fetchMock = mockFetch()
    fetchMock.mockReturnValueOnce(session.promise).mockResolvedValueOnce(jsonResponse(200, JANE))
    const { router } = renderApp('/profile')

    expect(screen.getByRole('status').textContent).toMatch('กำลังตรวจสอบ')
    expect(router.state.location.pathname).toBe('/profile')

    session.resolve(jsonResponse(200, JANE))

    expect(await screen.findByText('Jane Doe')).toBeTruthy()
    expect(router.state.location.pathname).toBe('/profile')
  })

  it('sends the user to login when the stored token turns out to be invalid', async () => {
    tokenStorage.set('tampered-token')
    mockFetch(jsonResponse(401, { detail: 'Invalid token', code: 'invalid_token' }))
    const { router } = renderApp('/profile')

    await waitFor(() => expect(router.state.location.pathname).toBe('/login'))
    expect(tokenStorage.get()).toBeNull()
  })
})

describe('ProfilePage', () => {
  it('shows the account returned by /users/me', async () => {
    tokenStorage.set('stored-token')
    const fetchMock = mockFetch(jsonResponse(200, JANE), jsonResponse(200, JANE))
    renderApp('/profile')

    expect(await screen.findByText('Jane Doe')).toBeTruthy()
    expect(screen.getByText('jane@example.com')).toBeTruthy()
    expect(screen.getByText('ใช้งานอยู่')).toBeTruthy()
    expect(document.querySelector('time')?.getAttribute('dateTime')).toBe(JANE.created_at)
    expect(fetchMock.mock.calls.map((call) => call[0])).toEqual([
      'http://api.test/api/users/me',
      'http://api.test/api/users/me',
    ])
  })

  it('logout clears the token and returns to the login page', async () => {
    tokenStorage.set('stored-token')
    mockFetch(jsonResponse(200, JANE), jsonResponse(200, JANE))
    const { user, router } = renderApp('/profile')
    await screen.findByText('Jane Doe')

    await user.click(screen.getByRole('button', { name: 'ออกจากระบบ' }))

    expect(router.state.location.pathname).toBe('/login')
    expect(tokenStorage.get()).toBeNull()
    expect(screen.getByRole('link', { name: 'เข้าสู่ระบบ' })).toBeTruthy()
  })

  it('a token that expires while on the page sends the user to login', async () => {
    tokenStorage.set('stored-token')
    mockFetch(jsonResponse(200, JANE), jsonResponse(401, EXPIRED))
    const { router } = renderApp('/profile')

    await waitFor(() => expect(router.state.location.pathname).toBe('/login'))
    expect(tokenStorage.get()).toBeNull()
  })

  it('offers a retry when loading fails for another reason', async () => {
    tokenStorage.set('stored-token')
    mockFetch(
      jsonResponse(200, JANE),
      new Response('Bad Gateway', { status: 502 }),
      jsonResponse(200, JANE),
    )
    const { user } = renderApp('/profile')

    expect((await screen.findByRole('alert')).textContent).toBe('โหลดข้อมูลโปรไฟล์ไม่สำเร็จ')
    await user.click(screen.getByRole('button', { name: 'ลองใหม่' }))

    expect(await screen.findByText('Jane Doe')).toBeTruthy()
    expect(screen.queryByRole('alert')).toBeNull()
  })
})
