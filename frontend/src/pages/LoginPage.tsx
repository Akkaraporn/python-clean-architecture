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
  LOGIN_FIELDS,
  type LoginField,
  type LoginValues,
  validateLogin,
} from '../features/auth/validation'

const EMPTY: LoginValues = { email: '', password: '' }

export function LoginPage() {
  const { status, login } = useAuth()
  const navigate = useNavigate()

  const [values, setValues] = useState<LoginValues>(EMPTY)
  const [fieldErrors, setFieldErrors] = useState<FieldErrors<LoginField>>({})
  const [formError, setFormError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [attempted, setAttempted] = useState(false)

  if (status === 'authenticated') {
    return <Navigate to="/" replace />
  }

  function handleChange(event: ChangeEvent<HTMLInputElement>) {
    const next = { ...values, [event.target.name]: event.target.value }
    setValues(next)
    // Live feedback only after the first submit, so users are not scolded mid-typing.
    if (attempted) setFieldErrors(validateLogin(next))
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (submitting) return

    const form = event.currentTarget
    const errors = validateLogin(values)
    setAttempted(true)
    setFieldErrors(errors)
    setFormError(null)
    if (hasErrors(errors)) {
      focusFirstInvalid(form, LOGIN_FIELDS, errors)
      return
    }

    setSubmitting(true)
    try {
      await login({ email: values.email.trim(), password: values.password })
      navigate('/', { replace: true })
    } catch (error) {
      const described = describeAuthError(error, LOGIN_FIELDS)
      setFieldErrors(described.fieldErrors)
      setFormError(described.formError)
      setSubmitting(false)
    }
  }

  return (
    <section className="card">
      <h1>เข้าสู่ระบบ</h1>
      <FormAlert message={formError} />
      <form onSubmit={handleSubmit} noValidate aria-busy={submitting}>
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
          autoComplete="current-password"
          value={values.password}
          onChange={handleChange}
          error={fieldErrors.password}
          required
        />
        <button type="submit" className="button-primary" disabled={submitting}>
          {submitting ? 'กำลังเข้าสู่ระบบ…' : 'เข้าสู่ระบบ'}
        </button>
      </form>
      <p className="muted form-footer">
        ยังไม่มีบัญชี? <Link to="/register">สมัครสมาชิก</Link>
      </p>
    </section>
  )
}
