import { config } from '../config'

export function HomePage() {
  return (
    <section className="card">
      <h1>ยินดีต้อนรับ</h1>
      <p>ระบบสมัครสมาชิกและเข้าสู่ระบบด้วย FastAPI + React</p>
      <p className="muted">
        API: <code>{config.apiBaseUrl}</code>
      </p>
    </section>
  )
}
