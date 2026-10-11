// The only module that reads build-time environment variables, so the rest of
// the app depends on typed values instead of import.meta.env.

function requireEnv(name: keyof ImportMetaEnv): string {
  const value = import.meta.env[name]
  if (!value) {
    // Fail at startup with a clear message rather than with a confusing network error later.
    throw new Error(`${name} is not set. Copy frontend/.env.example to frontend/.env.`)
  }
  return value
}

export const config = {
  apiBaseUrl: requireEnv('VITE_API_BASE_URL').replace(/\/+$/, ''),
} as const
