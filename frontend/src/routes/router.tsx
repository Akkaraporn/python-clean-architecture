import { createBrowserRouter } from 'react-router-dom'

import { AppLayout } from '../components/AppLayout'
import { HomePage } from '../pages/HomePage'
import { NotFoundPage } from '../pages/NotFoundPage'

// All routes in one place: pages stay unaware of URLs other than through <Link>.
export const router = createBrowserRouter([
  {
    element: <AppLayout />,
    children: [
      { index: true, element: <HomePage /> },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
])
