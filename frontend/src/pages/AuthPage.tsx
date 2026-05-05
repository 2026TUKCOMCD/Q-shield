import { useEffect, useState } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { Github, Shield } from 'lucide-react'
import { useAuth } from '../auth/AuthContext'
import { authService } from '../services/authService'

type Mode = 'login' | 'signup'

const GoogleIcon = () => (
  <svg className="h-4 w-4" viewBox="0 0 24 24" aria-hidden="true" focusable="false">
    <path
      fill="currentColor"
      d="M21.6 12.23c0-.74-.07-1.45-.19-2.13H12v4.03h5.38a4.6 4.6 0 0 1-2 3.02v2.52h3.24c1.9-1.74 2.98-4.31 2.98-7.44Z"
    />
    <path
      fill="currentColor"
      d="M12 22c2.7 0 4.97-.9 6.62-2.43l-3.24-2.52c-.9.6-2.05.96-3.38.96-2.6 0-4.8-1.76-5.59-4.12H3.06v2.6A10 10 0 0 0 12 22Z"
    />
    <path
      fill="currentColor"
      d="M6.41 13.89A6.02 6.02 0 0 1 6.1 12c0-.66.11-1.29.31-1.89v-2.6H3.06A10 10 0 0 0 2 12c0 1.61.39 3.14 1.06 4.49l3.35-2.6Z"
    />
    <path
      fill="currentColor"
      d="M12 5.99c1.47 0 2.79.5 3.82 1.49l2.87-2.87C16.96 3 14.7 2 12 2a10 10 0 0 0-8.94 5.51l3.35 2.6C7.2 7.75 9.4 5.99 12 5.99Z"
    />
  </svg>
)

export const AuthPage = () => {
  const location = useLocation()
  const navigate = useNavigate()
  const { isAuthenticated, login, signup } = useAuth()
  const initialMode: Mode = location.pathname.includes('/signup') ? 'signup' : 'login'
  const [mode, setMode] = useState<Mode>(initialMode)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setMode(location.pathname.includes('/signup') ? 'signup' : 'login')
  }, [location.pathname])

  if (isAuthenticated) {
    return <Navigate to="/scans/new" replace />
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)
    setError(null)
    try {
      if (mode === 'login') {
        await login(email, password)
      } else {
        await signup(email, password, displayName || undefined)
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Authentication failed')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleSocialLogin = (provider: 'google' | 'github') => {
    window.location.assign(authService.getOAuthLoginUrl(provider))
  }

  return (
    <div className="min-h-screen bg-[#020617] text-white flex items-center justify-center p-4">
      <div className="fixed inset-0 bg-gradient-to-br from-slate-900 via-purple-900/20 to-slate-900 pointer-events-none" />
      <div className="w-full max-w-md relative z-10 bg-white/5 backdrop-blur-md border border-white/10 rounded-xl p-8">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg">
            <Shield className="w-5 h-5 text-white" />
          </div>
          <h1 className="text-2xl font-bold">{mode === 'login' ? 'Login' : 'Create Account'}</h1>
        </div>

        <div className="flex gap-2 mb-6">
          <button
            onClick={() => {
              setMode('login')
              navigate('/auth/login')
            }}
            className={`flex-1 py-2 rounded-lg border ${
              mode === 'login'
                ? 'bg-indigo-500/20 border-indigo-500/40 text-white'
                : 'bg-white/5 border-white/10 text-slate-300'
            }`}
          >
            Login
          </button>
          <button
            onClick={() => {
              setMode('signup')
              navigate('/auth/signup')
            }}
            className={`flex-1 py-2 rounded-lg border ${
              mode === 'signup'
                ? 'bg-indigo-500/20 border-indigo-500/40 text-white'
                : 'bg-white/5 border-white/10 text-slate-300'
            }`}
          >
            Signup
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {mode === 'signup' && (
            <input
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              placeholder="Display name (optional)"
              className="w-full px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-white placeholder:text-slate-500 focus:outline-none"
            />
          )}
          <input
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            type="email"
            required
            placeholder="Email"
            className="w-full px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-white placeholder:text-slate-500 focus:outline-none"
          />
          <input
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            type="password"
            required
            placeholder="Password"
            className="w-full px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-white placeholder:text-slate-500 focus:outline-none"
          />

          {error && <p className="text-sm text-red-400">{error}</p>}

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full py-2 rounded-lg bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 disabled:opacity-50"
          >
            {isSubmitting ? 'Processing...' : mode === 'login' ? 'Login' : 'Create Account'}
          </button>
        </form>

        <div className="my-6 flex items-center gap-3">
          <div className="h-px flex-1 bg-white/10" />
          <span className="text-xs uppercase tracking-wider text-slate-500">or</span>
          <div className="h-px flex-1 bg-white/10" />
        </div>

        <div className="grid gap-3">
          <button
            type="button"
            onClick={() => handleSocialLogin('google')}
            className="flex w-full items-center justify-center gap-2 rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-200 transition hover:bg-white/10"
          >
            <GoogleIcon />
            <span>Continue with Google</span>
          </button>
          <button
            type="button"
            onClick={() => handleSocialLogin('github')}
            className="flex w-full items-center justify-center gap-2 rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-200 transition hover:bg-white/10"
          >
            <Github className="h-4 w-4" />
            <span>Continue with GitHub</span>
          </button>
        </div>
      </div>
    </div>
  )
}
