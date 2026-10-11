import { Link } from 'react-router-dom'

export function NotFoundPage() {
  return (
    <section className="card">
      <h1>ไม่พบหน้านี้</h1>
      <p>
        <Link to="/">กลับหน้าแรก</Link>
      </p>
    </section>
  )
}
