import { describe, expect, it } from 'vitest'

import { hasErrors, validateLogin, validateRegister, type RegisterValues } from './validation'

const VALID: RegisterValues = {
  full_name: 'Jane Doe',
  email: 'jane@example.com',
  password: 's3cret-pass',
  confirmPassword: 's3cret-pass',
}

describe('validateRegister', () => {
  it('accepts valid input', () => {
    expect(validateRegister(VALID)).toEqual({})
  })

  it.each([
    ['full_name', { full_name: '   ' }],
    ['full_name', { full_name: 'x'.repeat(256) }],
    ['email', { email: '' }],
    ['email', { email: 'not-an-email' }],
    ['password', { password: 'short', confirmPassword: 'short' }],
    ['confirmPassword', { confirmPassword: '' }],
    ['confirmPassword', { confirmPassword: 'different-pass' }],
  ])('flags %s', (field, override) => {
    const errors = validateRegister({ ...VALID, ...override })

    expect(Object.keys(errors)).toEqual([field])
  })

  it('measures the password limit in bytes, like bcrypt', () => {
    const thai24 = 'ก'.repeat(24) // 72 bytes
    const thai25 = 'ก'.repeat(25) // 75 bytes, though only 25 characters

    expect(validateRegister({ ...VALID, password: thai24, confirmPassword: thai24 })).toEqual({})
    expect(
      validateRegister({ ...VALID, password: thai25, confirmPassword: thai25 }).password,
    ).toMatch('ยาวเกินไป')
  })
})

describe('validateLogin', () => {
  it('only requires an email and a password', () => {
    expect(validateLogin({ email: 'jane@example.com', password: 'x' })).toEqual({})
    expect(Object.keys(validateLogin({ email: '', password: '' }))).toEqual(['email', 'password'])
  })
})

describe('hasErrors', () => {
  it('ignores empty entries', () => {
    expect(hasErrors({})).toBe(false)
    expect(hasErrors({ email: undefined })).toBe(false)
    expect(hasErrors({ email: 'bad' })).toBe(true)
  })
})
