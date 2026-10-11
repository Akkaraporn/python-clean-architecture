import { config } from '../config'
import { tokenStorage } from './tokenStorage'
import { API_ERROR_CODES, type ApiErrorCode } from './types'

/** The single error type every API call rejects with. */
export class ApiError extends Error {
  readonly status: number
  readonly code: ApiErrorCode
  /** Per-field messages from a 422 response, keyed by field name. */
  readonly fieldErrors: Readonly<Record<string, string>>

  constructor(
    status: number,
    code: ApiErrorCode,
    message: string,
    fieldErrors: Record<string, string> = {},
  ) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.fieldErrors = fieldErrors
  }
}

type UnauthorizedListener = () => void
const unauthorizedListeners = new Set<UnauthorizedListener>()

/**
 * Called whenever an authenticated request is rejected with 401 (expired, forged
 * or revoked token). Returns an unsubscribe function.
 */
export function onUnauthorized(listener: UnauthorizedListener): () => void {
  unauthorizedListeners.add(listener)
  return () => {
    unauthorizedListeners.delete(listener)
  }
}

export interface RequestOptions {
  method?: 'GET' | 'POST'
  body?: unknown
  /** Attach the stored bearer token. */
  auth?: boolean
  signal?: AbortSignal
}

export async function apiRequest<T>(
  path: string,
  { method = 'GET', body, auth = false, signal }: RequestOptions = {},
): Promise<T> {
  const headers: Record<string, string> = { Accept: 'application/json' }
  if (body !== undefined) {
    headers['Content-Type'] = 'application/json'
  }
  if (auth) {
    const token = tokenStorage.get()
    if (token) {
      headers.Authorization = `Bearer ${token}`
    }
  }

  let response: Response
  try {
    response = await fetch(`${config.apiBaseUrl}${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
      signal,
    })
  } catch (error) {
    if (isAbortError(error)) {
      throw error
    }
    throw new ApiError(0, 'network_error', 'Cannot reach the server')
  }

  const data = await readJson(response)

  if (!response.ok) {
    // Only a request that carried our token can prove the session is over. A 401
    // from the login form just means a wrong password.
    if (response.status === 401 && auth) {
      tokenStorage.clear()
      unauthorizedListeners.forEach((listener) => listener())
    }
    throw toApiError(response.status, data)
  }

  // A type assertion, not a runtime check: it trusts the backend contract that the
  // interfaces in ./types mirror.
  return data as T
}

export function isAbortError(error: unknown): boolean {
  return error instanceof DOMException && error.name === 'AbortError'
}

async function readJson(response: Response): Promise<unknown> {
  const text = await response.text()
  if (!text) {
    return null
  }
  try {
    return JSON.parse(text) as unknown
  } catch {
    // e.g. an HTML error page from a proxy in front of the API.
    return null
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function isApiErrorCode(value: unknown): value is ApiErrorCode {
  return (API_ERROR_CODES as readonly unknown[]).includes(value)
}

function toApiError(status: number, data: unknown): ApiError {
  const detail = isRecord(data) ? data.detail : undefined

  // FastAPI validation errors: {"detail": [{"loc": ["body", "email"], "msg": "..."}]}
  if (status === 422 && Array.isArray(detail)) {
    const fieldErrors: Record<string, string> = {}
    for (const item of detail) {
      if (!isRecord(item) || !Array.isArray(item.loc) || typeof item.msg !== 'string') {
        continue
      }
      const field = item.loc[item.loc.length - 1]
      if (typeof field === 'string' && !(field in fieldErrors)) {
        fieldErrors[field] = item.msg
      }
    }
    return new ApiError(status, 'validation_error', 'Invalid input', fieldErrors)
  }

  // Domain errors: {"detail": "...", "code": "..."}
  if (typeof detail === 'string') {
    const code = isRecord(data) && isApiErrorCode(data.code) ? data.code : 'unknown_error'
    return new ApiError(status, code, detail)
  }

  return new ApiError(status, 'unknown_error', `Request failed with status ${status}`)
}
