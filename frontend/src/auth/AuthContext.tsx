import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { authService, type AuthUser } from '../services/authService'
import { tokenStore } from './tokenStore'

interface AuthContextValue {
  user: AuthUser | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  signup: (email: string, password: string, displayName?: string) => Promise<void>
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

  const login = async (email: string, password: string) => {
    const result = await authService.login({ email, password })
    tokenStore.setAccessToken(result.accessToken)
    setUser(result.user)
  }

  const signup = async (email: string, password: string, displayName?: string) => {
    const result = await authService.signup({ email, password, displayName })
    tokenStore.setAccessToken(result.accessToken)
    setUser(result.user)
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
