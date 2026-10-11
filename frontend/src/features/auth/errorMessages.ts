import { ApiError } from '../../api/client'
import type { FieldErrors } from './validation'

export interface FormErrors<F extends string> {
  /** Shown above the form, for problems not tied to one field. */
  formError: string | null
  fieldErrors: FieldErrors<F>
}

const GENERIC_ERROR = 'เกิดข้อผิดพลาด กรุณาลองใหม่อีกครั้ง'

// Server-side (422) validation messages are in English; replace them with Thai
// text per field rather than mixing languages in the form.
const SERVER_FIELD_MESSAGES: Record<string, string> = {
  email: 'รูปแบบอีเมลไม่ถูกต้อง',
  password: 'รหัสผ่านไม่ตรงตามเงื่อนไข',
  full_name: 'ชื่อ-นามสกุลไม่ถูกต้อง',
}

export function describeAuthError<F extends string>(
  error: unknown,
  fields: readonly F[],
): FormErrors<F> {
  const result: FormErrors<F> = { formError: null, fieldErrors: {} }
  const isField = (name: string): name is F => (fields as readonly string[]).includes(name)

  if (!(error instanceof ApiError)) {
    result.formError = GENERIC_ERROR
    return result
  }

  switch (error.code) {
    case 'user_already_exists': {
      const field = 'email'
      if (isField(field)) {
        result.fieldErrors[field] = 'อีเมลนี้ถูกใช้แล้ว'
      } else {
        result.formError = 'อีเมลนี้ถูกใช้แล้ว'
      }
      break
    }
    case 'invalid_credentials':
      // Never say which of the two was wrong (mirrors the backend's rule).
      result.formError = 'อีเมลหรือรหัสผ่านไม่ถูกต้อง'
      break
    case 'inactive_user':
      result.formError = 'บัญชีนี้ถูกปิดใช้งาน กรุณาติดต่อผู้ดูแลระบบ'
      break
    case 'validation_error':
      for (const name of Object.keys(error.fieldErrors)) {
        if (isField(name)) {
          result.fieldErrors[name] = SERVER_FIELD_MESSAGES[name] ?? 'ข้อมูลไม่ถูกต้อง'
        }
      }
      if (Object.keys(result.fieldErrors).length === 0) {
        result.formError = 'ข้อมูลไม่ถูกต้อง กรุณาตรวจสอบอีกครั้ง'
      }
      break
    case 'network_error':
      result.formError = 'ไม่สามารถเชื่อมต่อเซิร์ฟเวอร์ได้ กรุณาลองใหม่อีกครั้ง'
      break
    default:
      result.formError = GENERIC_ERROR
  }
  return result
}
