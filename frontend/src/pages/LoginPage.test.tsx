import { cleanup, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { tokenStorage } from '../api/tokenStorage'
import { jsonResponse, mockFetch } from '../test/http'
import { deferred, JANE, renderApp } from '../test/renderApp'

const TOKEN = { access_token: 'new-token', token_type: 'bearer' }

beforeEach(() => tokenStorage.clear())
afterEach(() => {
  cleanup()
  tokenStorage.clear()
})

function submitButton() {
  return screen.getByRole('button', { name: /เข้าสู่ระบบ/ })
}

describe('LoginPage', () => {
  it('validates on submit without calling the API and focuses the first bad field', async () => {
    const fetchMock = mockFetch()
    const { user } = renderApp('/login')

    await user.click(submitButton())

    expect(screen.getByText('กรุณากรอกอีเมล')).toBeTruthy()
    expect(screen.getByText('กรุณากรอกรหัสผ่าน')).toBeTruthy()
    expect(screen.getByLabelText('อีเมล').getAttribute('aria-invalid')).toBe('true')
    expect(document.activeElement).toBe(screen.getByLabelText('อีเมล'))
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('can be filled and submitted with the keyboard alone', async () => {
    const fetchMock = mockFetch(jsonResponse(200, TOKEN), jsonResponse(200, JANE))
    const { user, router } = renderApp('/login')

    await user.click(screen.getByLabelText('อีเมล'))
    await user.keyboard('jane@example.com')
    await user.tab()
    await user.keyboard('s3cret-pass{Enter}')

    await waitFor(() => expect(router.state.location.pathname).toBe('/'))
    expect(await screen.findByText('สวัสดี, Jane Doe')).toBeTruthy()
    expect(fetchMock.mock.calls[0]?.[1]?.body).toBe(
      JSON.stringify({ email: 'jane@example.com', password: 's3cret-pass' }),
    )
  })

  it('shows a generic message for wrong credentials and lets the user retry', async () => {
    mockFetch(
      jsonResponse(401, { detail: 'Invalid email or password', code: 'invalid_credentials' }),
    )
    const { user } = renderApp('/login')

    await user.type(screen.getByLabelText('อีเมล'), 'jane@example.com')
    await user.type(screen.getByLabelText('รหัสผ่าน'), 'wrong-pass')
    await user.click(submitButton())

    expect((await screen.findByRole('alert')).textContent).toBe('อีเมลหรือรหัสผ่านไม่ถูกต้อง')
    expect(submitButton().hasAttribute('disabled')).toBe(false)
  })

  it('tells a deactivated user why they cannot sign in', async () => {
    mockFetch(jsonResponse(403, { detail: 'User account is inactive', code: 'inactive_user' }))
    const { user } = renderApp('/login')

    await user.type(screen.getByLabelText('อีเมล'), 'gone@example.com')
    await user.type(screen.getByLabelText('รหัสผ่าน'), 's3cret-pass')
    await user.click(submitButton())

    expect((await screen.findByRole('alert')).textContent).toMatch('ถูกปิดใช้งาน')
  })

  it('reports an unreachable server', async () => {
    vi.stubGlobal('fetch', vi.fn<typeof fetch>().mockRejectedValue(new TypeError('Failed to fetch')))
    const { user } = renderApp('/login')

    await user.type(screen.getByLabelText('อีเมล'), 'jane@example.com')
    await user.type(screen.getByLabelText('รหัสผ่าน'), 's3cret-pass')
    await user.click(submitButton())

    expect((await screen.findByRole('alert')).textContent).toMatch('ไม่สามารถเชื่อมต่อ')
  })

  it('disables the button while sending, so a double click sends one request', async () => {
    const pending = deferred<Response>()
    const fetchMock = mockFetch()
    fetchMock.mockReturnValueOnce(pending.promise)
    const { user } = renderApp('/login')

    await user.type(screen.getByLabelText('อีเมล'), 'jane@example.com')
    await user.type(screen.getByLabelText('รหัสผ่าน'), 's3cret-pass')
    await user.dblClick(submitButton())

    expect(submitButton().hasAttribute('disabled')).toBe(true)
    expect(submitButton().textContent).toBe('กำลังเข้าสู่ระบบ…')
    expect(fetchMock).toHaveBeenCalledOnce()

    pending.resolve(jsonResponse(401, { detail: 'x', code: 'invalid_credentials' }))
    await waitFor(() => expect(submitButton().hasAttribute('disabled')).toBe(false))
  })

  it('sends a signed-in user straight to the home page', async () => {
    tokenStorage.set('stored-token')
    mockFetch(jsonResponse(200, JANE))
    const { router } = renderApp('/login')

    await waitFor(() => expect(router.state.location.pathname).toBe('/'))
  })
})
