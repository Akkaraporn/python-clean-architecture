import { describe, expect, it } from 'vitest'

import { ApiError } from '../../api/client'
import { describeAuthError } from './errorMessages'
import { LOGIN_FIELDS, REGISTER_FIELDS } from './validation'

describe('describeAuthError', () => {
  it('puts a duplicate email next to the email field', () => {
    const result = describeAuthError(
      new ApiError(409, 'user_already_exists', 'exists'),
      REGISTER_FIELDS,
    )

    expect(result).toEqual({ formError: null, fieldErrors: { email: 'อีเมลนี้ถูกใช้แล้ว' } })
  })

  it('reports bad credentials without saying which part was wrong', () => {
    const result = describeAuthError(
      new ApiError(401, 'invalid_credentials', 'Invalid email or password'),
      LOGIN_FIELDS,
    )

    expect(result.formError).toBe('อีเมลหรือรหัสผ่านไม่ถูกต้อง')
    expect(result.fieldErrors).toEqual({})
  })

  it('maps server validation errors to the matching fields in Thai', () => {
    const result = describeAuthError(
      new ApiError(422, 'validation_error', 'Invalid input', {
        email: 'value is not a valid email address',
        unknown_field: 'ignored',
      }),
      REGISTER_FIELDS,
    )

    expect(result).toEqual({ formError: null, fieldErrors: { email: 'รูปแบบอีเมลไม่ถูกต้อง' } })
  })

  it('falls back to a form message when a 422 names no known field', () => {
    const result = describeAuthError(new ApiError(422, 'validation_error', 'x', {}), LOGIN_FIELDS)

    expect(result.formError).toMatch('ข้อมูลไม่ถูกต้อง')
  })

  it.each([
    [new ApiError(403, 'inactive_user', 'x'), 'บัญชีนี้ถูกปิดใช้งาน'],
    [new ApiError(0, 'network_error', 'x'), 'ไม่สามารถเชื่อมต่อเซิร์ฟเวอร์ได้'],
    [new ApiError(500, 'unknown_error', 'x'), 'เกิดข้อผิดพลาด'],
    [new Error('not an api error'), 'เกิดข้อผิดพลาด'],
  ])('describes %s as a form-level message', (error, expected) => {
    expect(describeAuthError(error, LOGIN_FIELDS).formError).toMatch(expected)
  })
})
