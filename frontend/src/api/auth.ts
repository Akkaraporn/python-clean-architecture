import { apiRequest } from './client'
import type { LoginPayload, RegisterPayload, TokenResponse, User } from './types'

export function register(payload: RegisterPayload): Promise<User> {
  return apiRequest<User>('/api/auth/register', { method: 'POST', body: payload })
}

export function login(payload: LoginPayload): Promise<TokenResponse> {
  return apiRequest<TokenResponse>('/api/auth/login', { method: 'POST', body: payload })
}

export function getMe(signal?: AbortSignal): Promise<User> {
  return apiRequest<User>('/api/users/me', { auth: true, signal })
}
