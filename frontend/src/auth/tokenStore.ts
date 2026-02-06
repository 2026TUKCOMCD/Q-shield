const ACCESS_TOKEN_KEY = 'pqc-access-token'

export const tokenStore = {
  getAccessToken(): string | null {
    try {
      return localStorage.getItem(ACCESS_TOKEN_KEY)
    } catch {
      return null
    }
  },

  setAccessToken(token: string): void {
    try {
      localStorage.setItem(ACCESS_TOKEN_KEY, token)
    } catch {
      // ignore storage errors
    }
  },

  clear(): void {
    try {
      localStorage.removeItem(ACCESS_TOKEN_KEY)
    } catch {
      // ignore storage errors
    }
  },
}
