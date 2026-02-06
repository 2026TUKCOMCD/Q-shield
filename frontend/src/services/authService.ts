import { apiClient } from '../api'

export interface AuthUser {
  uuid: string
  email: string
  displayName?: string | null
  status: string
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
