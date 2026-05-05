import { apiClient } from '../api'
import { type AuthTokenResponse } from './authService'

export interface UpdateProfilePayload {
  username?: string
  displayName?: string
}

export interface ChangePasswordPayload {
  currentPassword: string
  newPassword: string
}

export interface DeleteAccountPayload {
  currentPassword?: string
  confirmation: string
}

export const settingsService = {
  async updateProfile(payload: UpdateProfilePayload): Promise<AuthTokenResponse> {
    const response = await apiClient.patch<AuthTokenResponse>('/auth/profile', payload)
    return response.data
  },

  async changePassword(payload: ChangePasswordPayload): Promise<void> {
    await apiClient.patch('/auth/password', payload)
  },

  async deleteAccount(payload: DeleteAccountPayload): Promise<void> {
    await apiClient.delete('/auth/account', { data: payload })
  },
}
