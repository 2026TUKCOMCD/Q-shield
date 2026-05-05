import { useEffect, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { Loader2, ShieldAlert } from 'lucide-react'
import { useAuth } from '../auth/AuthContext'

export const AuthCallback = () => {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const { completeOAuthLogin } = useAuth()
  const providerError = searchParams.get('error')
  const accessToken = searchParams.get('accessToken')
  const [loginError, setLoginError] = useState<string | null>(null)
  const error = providerError ?? loginError ?? (accessToken ? null : 'Missing OAuth access token')

  useEffect(() => {
    if (providerError || !accessToken) {
      return
    }

    completeOAuthLogin(accessToken)
      .then(() => navigate('/scans/new', { replace: true }))
      .catch(() => setLoginError('OAuth login failed'))
  }, [accessToken, completeOAuthLogin, navigate, providerError])

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#020617] p-4 text-white">
      <div className="fixed inset-0 bg-gradient-to-br from-slate-900 via-purple-900/20 to-slate-900 pointer-events-none" />
      <div className="relative z-10 w-full max-w-md rounded-xl border border-white/10 bg-white/5 p-8 text-center backdrop-blur-md">
        {error ? (
          <>
            <ShieldAlert className="mx-auto mb-4 h-10 w-10 text-red-400" />
            <h1 className="mb-2 text-xl font-semibold">Login failed</h1>
            <p className="mb-6 text-sm text-slate-400">{error}</p>
            <Link
              to="/auth/login"
              className="inline-flex rounded-lg bg-gradient-to-r from-indigo-500 to-purple-600 px-4 py-2 text-sm font-semibold text-white transition hover:from-indigo-600 hover:to-purple-700"
            >
              Back to login
            </Link>
          </>
        ) : (
          <>
            <Loader2 className="mx-auto mb-4 h-10 w-10 animate-spin text-indigo-400" />
            <h1 className="mb-2 text-xl font-semibold">Completing login</h1>
            <p className="text-sm text-slate-400">Please wait while your account is verified.</p>
          </>
        )}
      </div>
    </div>
  )
}
