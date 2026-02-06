import { useEffect, useState } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { Shield } from 'lucide-react'
import { useAuth } from '../auth/AuthContext'

type Mode = 'login' | 'signup'

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
    } catch (err: any) {
      setError(err?.message || 'Authentication failed')
    } finally {
      setIsSubmitting(false)
    }
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
      </div>
    </div>
  )
}
