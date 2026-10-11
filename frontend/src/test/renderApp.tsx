import { render } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { createMemoryRouter, RouterProvider } from 'react-router-dom'

import type { User } from '../api/types'
import { AuthProvider } from '../features/auth'
import { routes } from '../routes/router'

export const JANE: User = {
  id: '6f1c2c8e-0000-4000-8000-000000000001',
  email: 'jane@example.com',
  full_name: 'Jane Doe',
  is_active: true,
  created_at: '2030-01-01T00:00:00Z',
}

/** Mounts the real route tree at `path`, inside the real AuthProvider. */
export function renderApp(path: string) {
  const router = createMemoryRouter(routes, { initialEntries: [path] })
  const user = userEvent.setup()
  render(
    <AuthProvider>
      <RouterProvider router={router} />
    </AuthProvider>,
  )
  return { router, user }
}

export function deferred<T>() {
  let resolve!: (value: T) => void
  const promise = new Promise<T>((r) => {
    resolve = r
  })
  return { promise, resolve }
}
