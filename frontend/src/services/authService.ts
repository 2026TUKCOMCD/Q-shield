import { apiClient } from '../api'
import { config } from '../config'

export interface AuthUser {
  uuid: string
  email?: string | null
  displayName?: string | null
  avatarUrl?: string | null
  status: string
  provider?: string | null
}

export interface AuthTokenResponse {
  accessToken: string
  tokenType: string
  user: AuthUser
}

export interface SignupPayload {
  email: string
  password: string
  displayName?: string
}

export interface LoginPayload {
  email: string
  password: string
}

export const authService = {
  getOAuthLoginUrl(provider: 'google' | 'github'): string {
    return `${config.apiBaseURL}/auth/${provider}/login`
  },

  async signup(payload: SignupPayload): Promise<AuthTokenResponse> {
    const response = await apiClient.post<AuthTokenResponse>('/auth/signup', payload)
    return response.data
  },

  async login(payload: LoginPayload): Promise<AuthTokenResponse> {
    const response = await apiClient.post<AuthTokenResponse>('/auth/login', payload)
    return response.data
  },

  async me(): Promise<AuthUser> {
    const response = await apiClient.get<AuthUser>('/auth/me')
    return response.data
  },
}
