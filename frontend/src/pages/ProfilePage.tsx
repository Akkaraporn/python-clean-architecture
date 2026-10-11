import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { getMe } from '../api/auth'
import { ApiError, isAbortError } from '../api/client'
import type { User } from '../api/types'
import { useAuth } from '../features/auth'
import { FormAlert } from '../features/auth/components/FormAlert'

type ProfileState =
  | { kind: 'loading' }
  | { kind: 'loaded'; user: User }
  | { kind: 'error'; message: string }

const dateFormatter = new Intl.DateTimeFormat('th-TH', { dateStyle: 'long', timeStyle: 'short' })

export function ProfilePage() {
  const { logout } = useAuth()
  const navigate = useNavigate()
  const [state, setState] = useState<ProfileState>({ kind: 'loading' })

  // Fetched fresh rather than read from context, so the page always reflects the
  // server and proves the token is still accepted. A 401 here is handled by the
  // API client: the session ends and ProtectedRoute sends the user to login.
  const fetchProfile = useCallback((signal?: AbortSignal) => {
    getMe(signal)
      .then((user) => setState({ kind: 'loaded', user }))
      .catch((error: unknown) => {
        if (isAbortError(error)) return
        const message =
          error instanceof ApiError && error.code === 'network_error'
            ? 'ไม่สามารถเชื่อมต่อเซิร์ฟเวอร์ได้'
            : 'โหลดข้อมูลโปรไฟล์ไม่สำเร็จ'
        setState({ kind: 'error', message })
      })
  }, [])

  // The initial state is already 'loading', so the effect only starts the request.
  useEffect(() => {
    const controller = new AbortController()
    fetchProfile(controller.signal)
    return () => controller.abort()
  }, [fetchProfile])

  function retry() {
    setState({ kind: 'loading' })
    fetchProfile()
  }

  function handleLogout() {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <section className="card">
      <h1>โปรไฟล์</h1>

      {state.kind === 'loading' && (
        <p role="status" className="muted">
          กำลังโหลดข้อมูล…
        </p>
      )}

      {state.kind === 'error' && (
        <>
          <FormAlert message={state.message} />
          <button type="button" className="button-secondary" onClick={retry}>
            ลองใหม่
          </button>
        </>
      )}

      {state.kind === 'loaded' && (
        <dl className="profile">
          <dt>ชื่อ-นามสกุล</dt>
          <dd>{state.user.full_name}</dd>
          <dt>อีเมล</dt>
          <dd>{state.user.email}</dd>
          <dt>สถานะบัญชี</dt>
          <dd>{state.user.is_active ? 'ใช้งานอยู่' : 'ถูกปิดใช้งาน'}</dd>
          <dt>สมัครเมื่อ</dt>
          <dd>
            <time dateTime={state.user.created_at}>
              {dateFormatter.format(new Date(state.user.created_at))}
            </time>
          </dd>
        </dl>
      )}

      <button type="button" className="button-primary" onClick={handleLogout}>
        ออกจากระบบ
      </button>
    </section>
  )
}
