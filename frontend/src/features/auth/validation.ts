// Client-side checks exist for fast feedback only. The backend (Pydantic + use
// cases) remains the authority: anyone can call the API without this form.
// The limits mirror backend/src/interface/handlers/fastapi/schemas.py.

export type FieldErrors<F extends string> = Partial<Record<F, string>>

export const PASSWORD_MIN_LENGTH = 8
/** bcrypt only uses 72 bytes; Thai characters take 3 bytes each in UTF-8. */
export const PASSWORD_MAX_BYTES = 72
export const FULL_NAME_MAX_LENGTH = 255

// Deliberately loose: the server's email validator has the final say.
const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

export interface LoginValues {
  email: string
  password: string
}
export type LoginField = keyof LoginValues
export const LOGIN_FIELDS: readonly LoginField[] = ['email', 'password']

export interface RegisterValues {
  full_name: string
  email: string
  password: string
  confirmPassword: string
}
export type RegisterField = keyof RegisterValues
export const REGISTER_FIELDS: readonly RegisterField[] = [
  'full_name',
  'email',
  'password',
  'confirmPassword',
]

function utf8Length(value: string): number {
  return new TextEncoder().encode(value).length
}

function emailError(email: string): string | undefined {
  if (!email.trim()) return 'กรุณากรอกอีเมล'
  if (!EMAIL_PATTERN.test(email.trim())) return 'รูปแบบอีเมลไม่ถูกต้อง'
  return undefined
}

export function validateLogin(values: LoginValues): FieldErrors<LoginField> {
  const errors: FieldErrors<LoginField> = {}
  const email = emailError(values.email)
  if (email) errors.email = email
  // No strength rules at login: they belong to registration.
  if (!values.password) errors.password = 'กรุณากรอกรหัสผ่าน'
  return errors
}

export function validateRegister(values: RegisterValues): FieldErrors<RegisterField> {
  const errors: FieldErrors<RegisterField> = {}

  if (!values.full_name.trim()) {
    errors.full_name = 'กรุณากรอกชื่อ-นามสกุล'
  } else if (values.full_name.length > FULL_NAME_MAX_LENGTH) {
    errors.full_name = `ชื่อยาวได้ไม่เกิน ${FULL_NAME_MAX_LENGTH} ตัวอักษร`
  }

  const email = emailError(values.email)
  if (email) errors.email = email

  if (values.password.length < PASSWORD_MIN_LENGTH) {
    errors.password = `รหัสผ่านต้องมีอย่างน้อย ${PASSWORD_MIN_LENGTH} ตัวอักษร`
  } else if (utf8Length(values.password) > PASSWORD_MAX_BYTES) {
    errors.password = 'รหัสผ่านยาวเกินไป (ไม่เกิน 72 ตัวอักษรภาษาอังกฤษ หรือ 24 ตัวอักษรภาษาไทย)'
  }

  if (!values.confirmPassword) {
    errors.confirmPassword = 'กรุณายืนยันรหัสผ่าน'
  } else if (values.confirmPassword !== values.password) {
    errors.confirmPassword = 'รหัสผ่านไม่ตรงกัน'
  }

  return errors
}

export function hasErrors<F extends string>(errors: FieldErrors<F>): boolean {
  return Object.values(errors).some(Boolean)
}
