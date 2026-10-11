/// <reference types="vitest/config" />
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    // Fixed value so tests never depend on a developer's local .env.
    env: { VITE_API_BASE_URL: 'http://api.test' },
    restoreMocks: true,
    unstubGlobals: true,
  },
})
