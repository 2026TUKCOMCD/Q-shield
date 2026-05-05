import { useEffect, useMemo, useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { Eye, EyeOff, KeyRound, Settings, Trash2, UserRound } from 'lucide-react'
import { useAuth } from '../auth/AuthContext'
import { settingsService } from '../services/settingsService'

const USERNAME_PATTERN = /^[a-z0-9_][a-z0-9_.-]{2,49}$/

const getProviderLabel = (provider?: string | null) => {
  switch (provider) {
    case 'google':
      return 'Google'
    case 'github':
      return 'GitHub'
    case 'local':
      return 'General User'
    default:
      return 'Unknown'
  }
}

const getPasswordProviderLabel = (provider?: string | null) => {
  switch (provider) {
    case 'google':
      return 'Google'
    case 'github':
      return 'GitHub'
    default:
      return 'your sign-in provider'
  }
}

const toErrorMessage = (error: unknown, fallback: string) => {
  const maybeError = error as { message?: string }
  return maybeError?.message || fallback
}

const toPasswordErrorMessage = (error: unknown) => {
  const message = toErrorMessage(error, 'Failed to update password.')
  if (message === 'Current password is incorrect') {
    return 'Current password is incorrect. Please check your current password and try again.'
  }
  return message
}

interface PasswordInputProps {
  value: string
  onChange: (value: string) => void
  autoComplete: string
}

const PasswordInput = ({ value, onChange, autoComplete }: PasswordInputProps) => {
  const [visible, setVisible] = useState(false)

  return (
    <div className="relative">
      <input
        value={value}
        onChange={(event) => onChange(event.target.value)}
        type={visible ? 'text' : 'password'}
        autoComplete={autoComplete}
        className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 pr-10 text-white placeholder:text-slate-500 focus:outline-none focus:border-indigo-500/50"
      />
      <button
        type="button"
        onClick={() => setVisible((current) => !current)}
        aria-label={visible ? 'Hide password' : 'Show password'}
        title={visible ? 'Hide password' : 'Show password'}
        className="absolute inset-y-0 right-0 flex items-center px-3 text-slate-400 transition hover:text-white"
      >
        {visible ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
      </button>
    </div>
  )
}

export const SettingsPage = () => {
  const navigate = useNavigate()
  const { user, updateSession, logout } = useAuth()
  const [username, setUsername] = useState('')
  const [profileMessage, setProfileMessage] = useState<string | null>(null)
  const [profileError, setProfileError] = useState<string | null>(null)
  const [isSavingProfile, setIsSavingProfile] = useState(false)

  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [passwordMessage, setPasswordMessage] = useState<string | null>(null)
  const [passwordError, setPasswordError] = useState<string | null>(null)
  const [isChangingPassword, setIsChangingPassword] = useState(false)

  const [deletePassword, setDeletePassword] = useState('')
  const [deleteConfirmation, setDeleteConfirmation] = useState('')
  const [deleteError, setDeleteError] = useState<string | null>(null)
  const [deleteSuccessMessage, setDeleteSuccessMessage] = useState<string | null>(null)
  const [isDeleting, setIsDeleting] = useState(false)

  const providerLabel = useMemo(() => getProviderLabel(user?.provider), [user?.provider])
  const passwordProviderLabel = useMemo(
    () => getPasswordProviderLabel(user?.provider),
    [user?.provider],
  )
  const canChangePassword = Boolean(user?.canChangePassword)

  useEffect(() => {
    setUsername(user?.username || user?.displayName || '')
  }, [user])

  useEffect(() => {
    if (!deleteSuccessMessage) {
      return
    }

    const timeoutId = window.setTimeout(() => {
      logout()
      navigate('/auth/login', { replace: true })
    }, 1800)

    return () => window.clearTimeout(timeoutId)
  }, [deleteSuccessMessage, logout, navigate])

  const handleProfileSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setProfileError(null)
    setProfileMessage(null)

    const normalizedUsername = username.trim().toLowerCase()
    if (canChangePassword && !USERNAME_PATTERN.test(normalizedUsername)) {
      setProfileError(
        'Username must be 3-50 characters and use letters, numbers, dot, dash, or underscore.',
      )
      return
    }

    setIsSavingProfile(true)
    try {
      const result = await settingsService.updateProfile({
        username: canChangePassword ? normalizedUsername : undefined,
      })
      updateSession(result)
      setProfileMessage('Profile updated.')
    } catch (error) {
      setProfileError(toErrorMessage(error, 'Failed to update profile.'))
    } finally {
      setIsSavingProfile(false)
    }
  }

  const handlePasswordSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setPasswordError(null)
    setPasswordMessage(null)

    if (currentPassword.length < 8) {
      setPasswordError('Current password must be at least 8 characters.')
      return
    }

    if (newPassword.length < 8) {
      setPasswordError('New password must be at least 8 characters.')
      return
    }

    setIsChangingPassword(true)
    try {
      await settingsService.changePassword({ currentPassword, newPassword })
      setCurrentPassword('')
      setNewPassword('')
      setPasswordMessage('Password updated.')
    } catch (error) {
      setPasswordError(toPasswordErrorMessage(error))
    } finally {
      setIsChangingPassword(false)
    }
  }

  const handleDeleteSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setDeleteError(null)

    if (canChangePassword && deletePassword.length < 8) {
      setDeleteError('Current password must be at least 8 characters.')
      return
    }

    if (deleteConfirmation.trim().toUpperCase() !== 'DELETE') {
      setDeleteError('Type DELETE to confirm account deletion.')
      return
    }

    setIsDeleting(true)
    try {
      await settingsService.deleteAccount({
        currentPassword: canChangePassword ? deletePassword : undefined,
        confirmation: deleteConfirmation,
      })
      setDeleteSuccessMessage('Your account has been deleted successfully.')
    } catch (error) {
      setDeleteError(toErrorMessage(error, 'Failed to delete account.'))
      setIsDeleting(false)
    }
  }

  return (
    <div className="min-h-screen bg-[#020617] text-white">
      {deleteSuccessMessage && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm">
          <div className="w-full max-w-sm rounded-xl border border-emerald-500/30 bg-slate-900 p-6 text-center shadow-2xl">
            <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full border border-emerald-500/30 bg-emerald-500/10">
              <Trash2 className="h-5 w-5 text-emerald-300" />
            </div>
            <h2 className="text-xl font-semibold text-white">Account Deleted</h2>
            <p className="mt-2 text-sm text-slate-300">{deleteSuccessMessage}</p>
            <p className="mt-1 text-xs text-slate-500">Returning to login...</p>
          </div>
        </div>
      )}
      <div className="fixed inset-0 bg-gradient-to-br from-slate-900 via-purple-900/20 to-slate-900 pointer-events-none" />
      <div className="fixed inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(99,102,241,0.1),transparent_50%)] pointer-events-none" />

      <div className="relative z-10 ml-0 md:ml-64 p-4 md:p-8">
        <div className="mx-auto max-w-5xl space-y-8">
          <div className="flex items-center gap-4">
            <div className="rounded-xl border border-indigo-500/30 bg-gradient-to-br from-indigo-500/20 to-purple-600/20 p-3">
              <Settings className="h-6 w-6 text-indigo-300" />
            </div>
            <div>
              <h1 className="text-4xl font-bold bg-gradient-to-r from-indigo-400 via-purple-400 to-indigo-400 bg-clip-text text-transparent">
                Settings
              </h1>
              <p className="mt-1 text-sm text-slate-400">Manage your Q-shield account.</p>
            </div>
          </div>

          <section className="rounded-xl border border-white/10 bg-white/5 p-6 backdrop-blur-md">
            <div className="mb-6 flex items-center gap-3">
              <div className="rounded-lg border border-indigo-500/30 bg-indigo-500/10 p-2">
                <UserRound className="h-5 w-5 text-indigo-300" />
              </div>
              <div>
                <h2 className="text-xl font-semibold">Account Profile</h2>
              </div>
            </div>

            <form onSubmit={handleProfileSubmit} className="grid gap-4 md:grid-cols-2">
              <label className="block space-y-2">
                <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                  Username
                </span>
                <input
                  value={username}
                  onChange={(event) => setUsername(event.target.value)}
                  disabled={!canChangePassword}
                  className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-white disabled:cursor-not-allowed disabled:opacity-50 focus:outline-none focus:border-indigo-500/50"
                />
                {!canChangePassword && (
                  <span className="block text-xs text-slate-500">
                    Username is synced from your {providerLabel} profile.
                  </span>
                )}
              </label>

              <div>
                <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                  Email
                </p>
                <p className="mt-2 truncate rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-300">
                  {user?.email || 'Not provided'}
                </p>
              </div>

              <div>
                <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                  Account Status
                </p>
                <p className="mt-2 rounded-lg border border-emerald-500/20 bg-emerald-500/10 px-3 py-2 text-sm text-emerald-300">
                  {providerLabel}
                </p>
              </div>

              <div className="md:col-span-2 flex flex-col gap-3 sm:flex-row sm:items-center">
                <button
                  type="submit"
                  disabled={isSavingProfile}
                  className="rounded-lg bg-gradient-to-r from-indigo-500 to-purple-600 px-4 py-2 text-sm font-medium text-white hover:from-indigo-600 hover:to-purple-700 disabled:opacity-50"
                >
                  {isSavingProfile ? 'Saving...' : 'Save Profile'}
                </button>
                {profileMessage && <p className="text-sm text-emerald-400">{profileMessage}</p>}
                {profileError && <p className="text-sm text-red-400">{profileError}</p>}
              </div>
            </form>
          </section>

          <section className="rounded-xl border border-white/10 bg-white/5 p-6 backdrop-blur-md">
            <div className="mb-6 flex items-center gap-3">
              <div className="rounded-lg border border-indigo-500/30 bg-indigo-500/10 p-2">
                <KeyRound className="h-5 w-5 text-indigo-300" />
              </div>
              <div>
                <h2 className="text-xl font-semibold">Password</h2>
                <p className="text-sm text-slate-400">
                  {canChangePassword
                    ? 'Update the password used for this account.'
                    : `Password is managed by ${passwordProviderLabel}.`}
                </p>
              </div>
            </div>

            <form onSubmit={handlePasswordSubmit} className="grid gap-4 md:grid-cols-2">
              <label className="block space-y-2">
                <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                  Current Password
                </span>
                <PasswordInput
                  value={currentPassword}
                  onChange={setCurrentPassword}
                  autoComplete="current-password"
                />
              </label>
              <label className="block space-y-2">
                <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                  New Password
                </span>
                <PasswordInput
                  value={newPassword}
                  onChange={setNewPassword}
                  autoComplete="new-password"
                />
                <span className="block text-xs text-slate-500">At least 8 characters.</span>
              </label>
              <div className="md:col-span-2 flex flex-col gap-3 sm:flex-row sm:items-center">
                <button
                  type="submit"
                  disabled={!canChangePassword || isChangingPassword}
                  className="rounded-lg bg-white/10 px-4 py-2 text-sm font-medium text-white hover:bg-white/15 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {isChangingPassword ? 'Updating...' : 'Update Password'}
                </button>
                {passwordMessage && <p className="text-sm text-emerald-400">{passwordMessage}</p>}
                {passwordError && <p className="text-sm text-red-400">{passwordError}</p>}
              </div>
            </form>
          </section>

          <section className="rounded-xl border border-red-500/20 bg-red-500/5 p-6 backdrop-blur-md">
            <div className="mb-6 flex items-center gap-3">
              <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-2">
                <Trash2 className="h-5 w-5 text-red-300" />
              </div>
              <div>
                <h2 className="text-xl font-semibold">Delete Account</h2>
                <p className="text-sm text-slate-400">This will disable your account and sign you out.</p>
              </div>
            </div>

            <form onSubmit={handleDeleteSubmit} className="grid gap-4 md:grid-cols-2">
              {canChangePassword && (
                <label className="block space-y-2">
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                    Current Password
                  </span>
                  <PasswordInput
                    value={deletePassword}
                    onChange={setDeletePassword}
                    autoComplete="current-password"
                  />
                </label>
              )}
              <label className="block space-y-2">
                <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                  Confirmation
                </span>
                <input
                  value={deleteConfirmation}
                  onChange={(event) => setDeleteConfirmation(event.target.value)}
                  placeholder="DELETE"
                  className="w-full rounded-lg border border-red-500/20 bg-white/5 px-3 py-2 text-white placeholder:text-slate-500 focus:outline-none focus:border-red-500/50"
                />
              </label>
              <div className="md:col-span-2 flex flex-col gap-3 sm:flex-row sm:items-center">
                <button
                  type="submit"
                  disabled={isDeleting}
                  className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-2 text-sm font-medium text-red-200 hover:bg-red-500/20 disabled:opacity-50"
                >
                  {isDeleting ? 'Deleting...' : 'Delete Account'}
                </button>
                {deleteError && <p className="text-sm text-red-400">{deleteError}</p>}
              </div>
            </form>
          </section>
        </div>
      </div>
    </div>
  )
}
