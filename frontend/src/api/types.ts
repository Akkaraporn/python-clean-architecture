// Mirrors the backend's Pydantic schemas (src/interface/handlers/fastapi/schemas.py).
// Field names stay in snake_case so they match the JSON on the wire one-to-one.

export interface User {
  id: string
  email: string
  full_name: string
  is_active: boolean
  /** ISO 8601 timestamp with timezone. */
  created_at: string
}

export interface TokenResponse {
  access_token: string
  token_type: 'bearer'
}

export interface RegisterPayload {
  email: string
  password: string
  full_name: string
}

export interface LoginPayload {
  email: string
  password: string
}

/** `code` values the backend sends, plus the ones the client produces itself. */
export const API_ERROR_CODES = [
  'user_already_exists',
  'invalid_credentials',
  'invalid_token',
  'token_expired',
  'user_not_found',
  'inactive_user',
  'domain_error',
  'validation_error',
  'network_error',
  'unknown_error',
] as const

export type ApiErrorCode = (typeof API_ERROR_CODES)[number]
