import { Link } from 'react-router-dom'

import { useAuth } from '../features/auth'

export function HomePage() {
  const { status, user } = useAuth()

  return (
    <section className="card">
      {status === 'authenticated' && user ? (
        <>
          <h1>สวัสดี, {user.full_name}</h1>
          <p>คุณเข้าสู่ระบบแล้วด้วย {user.email}</p>
          <p>
            <Link to="/profile">ดูโปรไฟล์</Link>
          </p>
        </>
      ) : (
        <>
          <h1>ยินดีต้อนรับ</h1>
          <p>ระบบสมัครสมาชิกและเข้าสู่ระบบด้วย FastAPI + React</p>
          <p>
            <Link to="/login">เข้าสู่ระบบ</Link> หรือ <Link to="/register">สมัครสมาชิก</Link>
          </p>
        </>
      )}
    </section>
  )
}
