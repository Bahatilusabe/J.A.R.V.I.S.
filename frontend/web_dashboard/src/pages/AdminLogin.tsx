import { useState, useEffect, useRef, startTransition } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useDispatch } from 'react-redux'
import authService from '../services/auth.service'

export default function AdminLogin() {
  const navigate = useNavigate()
  const location = useLocation()
  const dispatch = useDispatch()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [remember, setRemember] = useState(false)
  const [passwordStrength, setPasswordStrength] = useState<{ score: number; label: string }>({ score: 0, label: 'Too weak' })
  const errorRef = useRef<HTMLDivElement | null>(null)

  const from = ((location.state as { from?: { pathname?: string } })?.from?.pathname) || '/admin'

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      // Development backdoor: allow a local dev admin without backend when using credentials bahati / 1234
      // Only enable when VITE_DEV_ADMIN_BACKDOOR is set to '1' or 'true' in the Vite env.
      // Note: Also supports backend authentication via authService.login() for the same credentials
      const devBackdoorFlag = (import.meta as unknown as { env?: Record<string, string> }).env?.VITE_DEV_ADMIN_BACKDOOR
      const devBackdoorEnabled = devBackdoorFlag === '1' || devBackdoorFlag === 'true'

      if (devBackdoorEnabled && username.toLowerCase() === 'bahati' && password === '1234') {
        try {
          // Create a small JWT-like token with a near-future expiry so client-side checks pass
          const payload = { exp: Math.floor(Date.now() / 1000) + 60 * 60, role: 'admin', sub: username }
          const b64 = typeof window !== 'undefined' ? window.btoa(JSON.stringify(payload)).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '') : ''
          const fakeToken = `dev.${b64}.sig`
          localStorage.setItem('jarvis_access_token', fakeToken)
          localStorage.setItem('jarvis_refresh_token', `${fakeToken}-refresh`)
          const userObj = { username: 'bahati', role: 'admin', name: 'bahati' }
          localStorage.setItem('jarvis_user', JSON.stringify(userObj))
          // Also initialize Redux auth state so AdminRoute doesn't attempt a network profile fetch
          dispatch({ type: 'auth/loginSuccess', payload: { token: { accessToken: fakeToken, refreshToken: `${fakeToken}-refresh` }, user: userObj } })

          console.info('[AdminLogin] Dev backdoor used — environment flag enabled')
          startTransition(() => navigate(from, { replace: true }))
          return
        } catch (dErr) {
          console.error('Dev backdoor failed', dErr)
          setError('Dev login failed')
          return
        }
      }
      // Perform login. We'll navigate to the admin console immediately after
      // successful authentication and perform profile verification in the
      // background. This prevents the UI from appearing to do nothing when
      // profile verification is slow or blocked by CORS issues.
      await authService.login(username, password);

      // Navigate to the admin console immediately. AdminRoute will show a
      // loading spinner while it fetches/validates the profile. If the
      // subsequent profile check shows the user is not an admin, we'll
      // clear the session and redirect away.
      startTransition(() => navigate(from, { replace: true }));

      // Background profile verification
      (async () => {
        try {
          const profile = await authService.getProfile()
          if (!profile || profile.role !== 'admin') {
            // Not an admin — clear session and surface an error after redirect
            authService.logout()
            setError('Account is not authorized to access the admin console')
            // Ensure we don't stay on /admin
            startTransition(() => navigate('/dashboard', { replace: true }));
          }
        } catch (pfErr) {
          // If profile fetch fails, log and leave the user on the admin page
          // where AdminRoute will continue to handle retries or show a spinner.
          console.warn('Background profile verification failed', pfErr)
        }
      })()
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Login failed'
      setError(msg)
      // move focus to error for screen readers
      if (errorRef.current) errorRef.current.focus()
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    // Password strength estimation (simple heuristic)
    let score = 0
    if (password.length >= 8) score += 1
    if (/[A-Z]/.test(password)) score += 1
    if (/[0-9]/.test(password)) score += 1
    if (/[^A-Za-z0-9]/.test(password)) score += 1
    const label = score <= 1 ? 'Too weak' : score === 2 ? 'Weak' : score === 3 ? 'Good' : 'Strong'
    setPasswordStrength({ score, label })
  }, [password])

  const strengthWidthClass = ['w-0', 'w-1/4', 'w-1/2', 'w-3/4', 'w-full'][passwordStrength.score]

  useEffect(() => {
    // Restore remembered username
    try {
      const saved = localStorage.getItem('admin_remember_username')
      if (saved) {
        setUsername(saved)
        setRemember(true)
      }
    } catch (e) {
      // ignore
    }
  }, [])

  useEffect(() => {
    // Persist remembered username
    try {
      if (remember && username) localStorage.setItem('admin_remember_username', username)
      else localStorage.removeItem('admin_remember_username')
    } catch (e) {
      // ignore
    }
  }, [remember, username])

  const validateForm = () => {
    const devBackdoorFlag = (import.meta as unknown as { env?: Record<string, string> }).env?.VITE_DEV_ADMIN_BACKDOOR
    const devBackdoorEnabled = devBackdoorFlag === '1' || devBackdoorFlag === 'true'
    // allow the dev backdoor shortcut bahati/1234 even though password length is small
    if (devBackdoorEnabled && username.toLowerCase() === 'bahati' && password === '1234') return true
    return username.trim().length > 0 && password.length >= 8
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-slate-900 via-slate-800 to-slate-900 p-6">
      <div className="w-full max-w-4xl grid grid-cols-1 md:grid-cols-2 gap-6 items-center">
        {/* Left: Illustration / branding */}
        <div className="hidden md:flex flex-col items-start justify-center gap-6 bg-gradient-to-br from-cyan-700/20 to-blue-700/10 rounded-lg p-8 shadow-lg border border-cyan-500/10">
          <div className="px-2 py-1 rounded bg-cyan-500/10 text-cyan-300 text-xs font-semibold">Administrator</div>
          <h1 className="text-3xl font-extrabold text-cyan-300">Admin Console</h1>
          <p className="text-sm text-slate-200/70">Access: Control center for system-wide configuration and diagnostics. Actions here are audited.</p>
          <svg className="w-48 h-48 opacity-80" viewBox="0 0 128 128" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden>
            <rect x="16" y="32" width="96" height="64" rx="8" fill="url(#g)" />
            <path d="M32 48h64" stroke="#0891b2" strokeWidth="2" strokeLinecap="round" />
            <defs>
              <linearGradient id="g" x1="0" x2="1">
                <stop offset="0" stopColor="#0891b2" stopOpacity="0.12" />
                <stop offset="1" stopColor="#7c3aed" stopOpacity="0.08" />
              </linearGradient>
            </defs>
          </svg>
        </div>

        {/* Right: Form */}
        <div className="bg-slate-800/60 rounded-lg border border-cyan-400/20 p-6 shadow-xl backdrop-blur-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-2xl font-bold text-cyan-300">Sign in</h2>
              <p className="text-sm text-gray-400">Secure admin access to the console (SPA-only).</p>
            </div>
            <div className="text-xs text-gray-400">v2.8.5</div>
          </div>

          {error && (
            <div tabIndex={-1} ref={errorRef} aria-live="assertive" className="mb-3 text-sm text-red-400">⚠ {error}</div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="admin-username" className="block text-xs text-gray-300 mb-1">Username</label>
              <input id="admin-username" aria-label="Admin username" aria-invalid={username.trim() === '' ? 'true' : 'false'} value={username} onChange={(e) => setUsername(e.target.value)} disabled={loading}
                className="w-full px-3 py-2 rounded bg-slate-900/50 border border-cyan-400/20 text-white focus:outline-none focus:ring-2 focus:ring-cyan-400" placeholder="admin" />
            </div>

            <div>
              <label htmlFor="admin-password" className="block text-xs text-gray-300 mb-1">Password</label>
              <div className="relative">
                <input id="admin-password" aria-label="Admin password" aria-invalid={password.length < 8 ? 'true' : 'false'} type={showPassword ? 'text' : 'password'} value={password} onChange={(e) => setPassword(e.target.value)} disabled={loading}
                  className="w-full px-3 py-2 rounded bg-slate-900/50 border border-cyan-400/20 text-white focus:outline-none focus:ring-2 focus:ring-cyan-400" placeholder="••••••••" />
                <button type="button" onClick={() => setShowPassword((s) => !s)} aria-label={showPassword ? 'Hide password' : 'Show password'}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-300 hover:text-cyan-300">
                  {showPassword ? '🙈' : '👁️'}
                </button>
              </div>

              <div className="mt-2 flex items-center gap-2">
                <div className={`h-1 ${strengthWidthClass} rounded ${passwordStrength.score >= 1 ? 'bg-rose-500' : 'bg-slate-700'}`} />
                <div className="text-xs text-gray-400 w-24 text-right">{passwordStrength.label}</div>
              </div>
              {password && password.length < 8 && <div className="text-xs text-amber-300 mt-1">Use a longer password (8+ chars) for stronger security.</div>}
            </div>

            <div className="flex items-center justify-between">
              <label className="flex items-center gap-2 text-sm text-gray-300">
                <input type="checkbox" checked={remember} onChange={(e) => setRemember(e.target.checked)} className="form-checkbox h-4 w-4 text-cyan-400" />
                <span>Remember username</span>
              </label>

              <a className="text-sm text-cyan-300 hover:underline" href="#" data-no-spa>Forgot?</a>
            </div>

            <div>
              <button type="submit" disabled={loading || !validateForm()}
                className="w-full py-3 bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-600 hover:to-blue-600 disabled:opacity-50 text-slate-950 font-semibold rounded shadow">{loading ? 'Authenticating…' : 'Sign in as Admin'}</button>
            </div>
          </form>

          <div className="mt-4 text-xs text-gray-500">This admin login gates SPA access — actions here are audited. Use the dev backdoor only in local development.</div>
        </div>
      </div>
    </div>
  )
}
