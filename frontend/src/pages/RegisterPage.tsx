import { type ChangeEvent, type FormEvent, useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'

import { useAuth } from '../features/auth'
import { FormAlert } from '../features/auth/components/FormAlert'
import { TextField } from '../features/auth/components/TextField'
import { describeAuthError } from '../features/auth/errorMessages'
import { focusFirstInvalid } from '../features/auth/focus'
import {
  type FieldErrors,
  hasErrors,
  PASSWORD_MIN_LENGTH,
  REGISTER_FIELDS,
  type RegisterField,
  type RegisterValues,
  validateRegister,
} from '../features/auth/validation'

const EMPTY: RegisterValues = { full_name: '', email: '', password: '', confirmPassword: '' }

export function RegisterPage() {
  const { status, register } = useAuth()
  const navigate = useNavigate()

  const [values, setValues] = useState<RegisterValues>(EMPTY)
  const [fieldErrors, setFieldErrors] = useState<FieldErrors<RegisterField>>({})
  const [formError, setFormError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [attempted, setAttempted] = useState(false)

  if (status === 'authenticated') {
    return <Navigate to="/" replace />
  }

  function handleChange(event: ChangeEvent<HTMLInputElement>) {
    const next = { ...values, [event.target.name]: event.target.value }
    setValues(next)
    if (attempted) setFieldErrors(validateRegister(next))
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (submitting) return

    const form = event.currentTarget
    const errors = validateRegister(values)
    setAttempted(true)
    setFieldErrors(errors)
    setFormError(null)
    if (hasErrors(errors)) {
      focusFirstInvalid(form, REGISTER_FIELDS, errors)
      return
    }

    setSubmitting(true)
    try {
      // confirmPassword is a client-side check only; the API never receives it.
      await register({
        email: values.email.trim(),
        password: values.password,
        full_name: values.full_name.trim(),
      })
      navigate('/', { replace: true })
    } catch (error) {
      const described = describeAuthError(error, REGISTER_FIELDS)
      setFieldErrors(described.fieldErrors)
      setFormError(described.formError)
      setSubmitting(false)
      focusFirstInvalid(form, REGISTER_FIELDS, described.fieldErrors)
    }
  }

  return (
    <section className="card">
      <h1>สมัครสมาชิก</h1>
      <FormAlert message={formError} />
      <form onSubmit={handleSubmit} noValidate aria-busy={submitting}>
        <TextField
          name="full_name"
          label="ชื่อ-นามสกุล"
          autoComplete="name"
          value={values.full_name}
          onChange={handleChange}
          error={fieldErrors.full_name}
          required
        />
        <TextField
          name="email"
          label="อีเมล"
          type="email"
          autoComplete="email"
          inputMode="email"
          value={values.email}
          onChange={handleChange}
          error={fieldErrors.email}
          required
        />
        <TextField
          name="password"
          label="รหัสผ่าน"
          type="password"
          autoComplete="new-password"
          hint={`อย่างน้อย ${PASSWORD_MIN_LENGTH} ตัวอักษร`}
          value={values.password}
          onChange={handleChange}
          error={fieldErrors.password}
          required
        />
        <TextField
          name="confirmPassword"
          label="ยืนยันรหัสผ่าน"
          type="password"
          autoComplete="new-password"
          value={values.confirmPassword}
          onChange={handleChange}
          error={fieldErrors.confirmPassword}
          required
        />
        <button type="submit" className="button-primary" disabled={submitting}>
          {submitting ? 'กำลังสมัครสมาชิก…' : 'สมัครสมาชิก'}
        </button>
      </form>
      <p className="muted form-footer">
        มีบัญชีอยู่แล้ว? <Link to="/login">เข้าสู่ระบบ</Link>
      </p>
    </section>
  )
}
