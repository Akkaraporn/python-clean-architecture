import { cleanup, screen, waitFor } from '@testing-library/react'
import type { UserEvent } from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'

import { tokenStorage } from '../api/tokenStorage'
import { jsonResponse, mockFetch } from '../test/http'
import { JANE, renderApp } from '../test/renderApp'

beforeEach(() => tokenStorage.clear())
afterEach(() => {
  cleanup()
  tokenStorage.clear()
})

interface FormInput {
  name?: string
  email?: string
  password?: string
  confirm?: string
}

async function fillAndSubmit(user: UserEvent, input: FormInput = {}) {
  const {
    name = 'Jane Doe',
    email = 'jane@example.com',
    password = 's3cret-pass',
    confirm = password,
  } = input
  if (name) await user.type(screen.getByLabelText('ชื่อ-นามสกุล'), name)
  if (email) await user.type(screen.getByLabelText('อีเมล'), email)
  if (password) await user.type(screen.getByLabelText('รหัสผ่าน'), password)
  if (confirm) await user.type(screen.getByLabelText('ยืนยันรหัสผ่าน'), confirm)
  await user.click(screen.getByRole('button', { name: /สมัครสมาชิก/ }))
}

function errorFor(label: string): string | null {
  const input = screen.getByLabelText(label)
  const ids = input.getAttribute('aria-describedby')?.split(' ') ?? []
  const errorId = ids.find((id) => id.endsWith('-error'))
  return errorId ? (document.getElementById(errorId)?.textContent ?? null) : null
}

describe('RegisterPage', () => {
  it('checks every field before calling the API', async () => {
    const fetchMock = mockFetch()
    const { user } = renderApp('/register')

    await fillAndSubmit(user, {
      name: ' ',
      email: 'not-an-email',
      password: 'short',
      confirm: 'other',
    })

    expect(errorFor('ชื่อ-นามสกุล')).toBe('กรุณากรอกชื่อ-นามสกุล')
    expect(errorFor('อีเมล')).toBe('รูปแบบอีเมลไม่ถูกต้อง')
    expect(errorFor('รหัสผ่าน')).toMatch('อย่างน้อย 8')
    expect(errorFor('ยืนยันรหัสผ่าน')).toBe('รหัสผ่านไม่ตรงกัน')
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('clears an error as soon as the field is fixed', async () => {
    mockFetch()
    const { user } = renderApp('/register')
    await fillAndSubmit(user, { confirm: 'mismatch' })
    expect(errorFor('ยืนยันรหัสผ่าน')).toBe('รหัสผ่านไม่ตรงกัน')

    await user.clear(screen.getByLabelText('ยืนยันรหัสผ่าน'))
    await user.type(screen.getByLabelText('ยืนยันรหัสผ่าน'), 's3cret-pass')

    expect(errorFor('ยืนยันรหัสผ่าน')).toBeNull()
  })

  it('creates the account, signs in and opens the profile', async () => {
    const fetchMock = mockFetch(
      jsonResponse(201, JANE),
      jsonResponse(200, { access_token: 'new-token', token_type: 'bearer' }),
      jsonResponse(200, JANE),
      jsonResponse(200, JANE),
    )
    const { user, router } = renderApp('/register')

    await fillAndSubmit(user)

    await waitFor(() => expect(router.state.location.pathname).toBe('/profile'))
    expect(await screen.findByText('Jane Doe')).toBeTruthy()
    // The confirmation is checked in the browser and never sent.
    expect(fetchMock.mock.calls[0]?.[1]?.body).toBe(
      JSON.stringify({ email: 'jane@example.com', password: 's3cret-pass', full_name: 'Jane Doe' }),
    )
  })

  it('shows a taken email next to the email field', async () => {
    mockFetch(jsonResponse(409, { detail: 'exists', code: 'user_already_exists' }))
    const { user } = renderApp('/register')

    await fillAndSubmit(user)

    await waitFor(() => expect(errorFor('อีเมล')).toBe('อีเมลนี้ถูกใช้แล้ว'))
    expect(document.activeElement).toBe(screen.getByLabelText('อีเมล'))
    expect(screen.queryByRole('alert')).toBeNull()
  })

  it('shows server-side validation errors on the matching field', async () => {
    // Passes the loose client check but the server's validator rejects it.
    mockFetch(
      jsonResponse(422, {
        detail: [{ loc: ['body', 'email'], msg: 'special-use domain', type: 'value_error' }],
      }),
    )
    const { user } = renderApp('/register')

    await fillAndSubmit(user, { email: 'jane@example.test' })

    await waitFor(() => expect(errorFor('อีเมล')).toBe('รูปแบบอีเมลไม่ถูกต้อง'))
  })
})
