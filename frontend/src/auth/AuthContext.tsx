/* eslint-disable react-refresh/only-export-components */
import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { authService, type AuthTokenResponse, type AuthUser } from '../services/authService'
import { tokenStore } from './tokenStore'

interface AuthContextValue {
  user: AuthUser | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (username: string, password: string) => Promise<void>
  signup: (username: string, password: string, email: string, displayName?: string) => Promise<void>
  completeOAuthLogin: (accessToken: string) => Promise<void>
  updateSession: (result: AuthTokenResponse) => void
  refreshUser: () => Promise<AuthUser>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const bootstrap = async () => {
      const token = tokenStore.getAccessToken()
      if (!token) {
        setIsLoading(false)
        return
      }

      try {
        const me = await authService.me()
        setUser(me)
      } catch {
        tokenStore.clear()
        setUser(null)
      } finally {
        setIsLoading(false)
      }
    }

    bootstrap()
  }, [])

  useEffect(() => {
    const onUnauthorized = () => {
      tokenStore.clear()
      setUser(null)
    }

    window.addEventListener('auth:unauthorized', onUnauthorized)
    return () => window.removeEventListener('auth:unauthorized', onUnauthorized)
  }, [])

  const login = async (username: string, password: string) => {
    const result = await authService.login({ username, password })
    tokenStore.setAccessToken(result.accessToken)
    setUser(result.user)
  }

  const signup = async (username: string, password: string, email: string, displayName?: string) => {
    const result = await authService.signup({ username, email, password, displayName })
    tokenStore.setAccessToken(result.accessToken)
    setUser(result.user)
  }

  const completeOAuthLogin = async (accessToken: string) => {
    // TODO: Prefer a secure httpOnly cookie in production. This follows the
    // existing localStorage Bearer-token flow used by the current frontend.
    tokenStore.setAccessToken(accessToken)
    const me = await authService.me()
    setUser(me)
  }

  const updateSession = (result: AuthTokenResponse) => {
    tokenStore.setAccessToken(result.accessToken)
    setUser(result.user)
  }

  const refreshUser = async () => {
    const me = await authService.me()
    setUser(me)
    return me
  }

  const logout = () => {
    tokenStore.clear()
    setUser(null)
  }

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isAuthenticated: !!user,
      isLoading,
      login,
      signup,
      completeOAuthLogin,
      updateSession,
      refreshUser,
      logout,
    }),
    [user, isLoading],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export const useAuth = (): AuthContextValue => {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return ctx
}
