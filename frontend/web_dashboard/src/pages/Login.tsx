import { useState, useEffect, useRef, startTransition } from 'react'
import { useNavigate } from 'react-router-dom'
import authService from '../services/auth.service'
import SessionSplash from '../components/SessionSplash'

export default function Login() {
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [sessionLoading, setSessionLoading] = useState(true)
  const [sessionError, setSessionError] = useState('')
  const [sessionMessage, setSessionMessage] = useState('Initializing secure session...')
  const startAttemptedRef = useRef(false)

  // Initialize a secure session before showing login UI
  const initSession = async () => {
    // Resolve API base early so it's available in both try and catch blocks
    const apiBase = (import.meta as unknown as { env: Record<string, string> }).env.VITE_API_URL || 'http://127.0.0.1:8000'

    // Helper for environments where AbortSignal.timeout may not be available (older browsers)
    const makeTimeoutSignal = (ms: number): AbortSignal => {
      const maybe = (AbortSignal as unknown as { timeout?: (m: number) => AbortSignal }).timeout
      if (typeof maybe === 'function') return maybe(ms)
      const ac = new AbortController()
      setTimeout(() => ac.abort(), ms)
      return ac.signal
    }

    try {
      setSessionError('')
      setSessionMessage('Initializing secure session...')

      // Fast backend connectivity check (no artificial delays)
      const resp = await fetch(`${apiBase}/api/system/status`, {
        method: 'GET',
        credentials: 'include',
        signal: makeTimeoutSignal(5000),
      })

      if (!resp.ok) {
        throw new Error('Backend unavailable')
      }

      setSessionMessage('✓ Secure session established')
      // Skip long delay - show login immediately
      setSessionLoading(false)
    } catch (e) {
      console.error('Session init error:', e)
      setSessionError('Unable to reach command center')

      // Map to friendly message used by splash; attempt to start backend services
      setSessionMessage('Backend services offline')

      // Try to trigger backend self-healing/start only once per page load to avoid repeated jobs
      try {
        if (!startAttemptedRef.current) {
          startAttemptedRef.current = true
          setSessionMessage('Attempting to bootstrap command services...')

          const startResp = await fetch(`${apiBase}/api/self_healing/start`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ mode: 'recovery' }),
            signal: makeTimeoutSignal(8000),
          })

          if (startResp.ok) {
            const startJson = await startResp.json().catch(() => ({}))
            console.info('Self-healing start triggered:', startJson)
            setSessionMessage('Services initializing...')

            // Poll system status for up to 30 seconds (reduced from 60)
            const deadline = Date.now() + 30000
            while (Date.now() < deadline) {
              try {
                const p = await fetch(`${apiBase}/api/system/status`, { method: 'GET', credentials: 'include', signal: makeTimeoutSignal(5000) })
                if (p.ok) {
                  setSessionMessage('✓ Secure session established')
                  // Skip long delay - show login immediately
                  setSessionError('')
                  setSessionLoading(false)
                  return
                }
              } catch (pollErr) {
                // swallow and retry
              }
              // Wait 1s between polls (reduced from 2s)
              // eslint-disable-next-line no-await-in-loop
              await new Promise((r) => setTimeout(r, 1000))
            }

            // If we get here, polling timed out
            setSessionError('Unable to reach command center')
            setSessionMessage('Base Station Off_Grid')
            return
          } else {
            console.warn('Self-healing start returned non-ok', startResp.status)
            // fall through to set error below
          }
        }
      } catch (startErr) {
        console.error('Failed to trigger self-healing start:', startErr)
      }

      // Default fallback when start not performed or failed
      setSessionMessage('Base Station Off_Grid')
    }
  }

  // Call initSession once on mount. Disable exhaustive-deps because initSession is fine to run once
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => {
    initSession()
  }, [])


  const validateInputs = (): boolean => {
    if (!username || !password) {
      setError('Username and password are required')
      return false
    }
    return true
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    if (!validateInputs()) {
      setLoading(false)
      return
    }

    try {
      await authService.login(username, password)
      console.info('[Login] login successful, navigating to /dashboard')
      startTransition(() => navigate('/dashboard'))
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Login failed. Please try again.'
      setError(errorMessage)
      console.error('Login error:', err)
    } finally {
      setLoading(false)
    }
  }

  if (sessionLoading) {
    return <SessionSplash sessionMessage={sessionMessage} sessionError={sessionError} onRetry={initSession} />
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-800 flex items-center justify-center p-4 relative overflow-hidden">
      {/* CIA Theme - Classified Background Effect */}
      <div className="absolute inset-0 opacity-5">
        <div className="absolute top-0 left-0 text-red-600 font-mono text-xs tracking-widest transform -rotate-45">
          {Array(50).fill('⚠ CLASSIFIED ⚠').join(' ')}
        </div>
      </div>

      {/* Animated Grid Background */}
      <div className="absolute inset-0 opacity-10">
        <svg width="100%" height="100%">
          <defs>
            <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
              <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#0891b2" strokeWidth="0.5" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#grid)" />
        </svg>
      </div>

      {/* Login Container */}
      <div className="w-full max-w-lg relative z-10">
        {/* Top Secret Banner */}
        <div className="mb-6">
          <div className="bg-gradient-to-r from-red-900/20 to-red-800/10 border border-red-600/30 px-4 py-2 text-center">
            <p className="text-red-500 text-sm font-mono font-bold tracking-widest">
              ⚠ CLASSIFIED - FOR OFFICIAL USE ONLY ⚠
            </p>
            <p className="text-red-400 text-xs font-mono mt-1">
              UNAUTHORIZED ACCESS IS PROHIBITED • VIOLATIONS WILL BE PROSECUTED
            </p>
          </div>
        </div>

        {/* Main Login Panel */}
        <div className="bg-gradient-to-br from-slate-800/40 to-slate-900/40 backdrop-blur-xl rounded-lg border border-cyan-400/40 shadow-2xl overflow-hidden">
          {/* Header */}
          <div className="bg-gradient-to-r from-slate-900/60 to-slate-950/60 border-b border-cyan-400/20 px-8 py-6">
            <div className="text-center">
              <h1 className="text-4xl font-black text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-blue-400 to-cyan-300 mb-2 tracking-wider">
                J.A.R.V.I.S
              </h1>
              <p className="text-cyan-300/80 font-mono text-sm mb-1">CENTRALIZED INTELLIGENCE NETWORK</p>
              <p className="text-gray-400 text-xs">Defense & Threat Intelligence Management System</p>
            </div>
            {/* Status Indicator */}
            <div className="mt-4 flex items-center justify-center gap-2">
              <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
              <span className="text-green-400 text-xs font-mono">SYSTEM OPERATIONAL</span>
            </div>
          </div>

          {/* Form Section */}
          <div className="px-8 py-8">
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Error Message */}
              {error && (
                <div className="bg-red-900/20 border border-red-500/50 rounded px-4 py-3 text-red-400 text-sm font-mono">
                  <span className="font-bold">⚠ AUTHENTICATION FAILED:</span> {error}
                </div>
              )}

              {/* Username Field */}
              <div>
                <label className="block text-xs font-mono font-bold text-cyan-400/80 mb-2 uppercase tracking-wider">
                  👤 Agent ID / Username
                </label>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  disabled={loading}
                  className="w-full px-4 py-3 bg-slate-900/50 border border-cyan-400/30 hover:border-cyan-400/50 focus:border-cyan-400 rounded text-white placeholder-gray-500/60 focus:outline-none focus:ring-2 focus:ring-cyan-400/20 transition-all disabled:opacity-50"
                  placeholder="Enter your agent credentials"
                />
              </div>

              {/* Password Field */}
              <div>
                <label className="block text-xs font-mono font-bold text-cyan-400/80 mb-2 uppercase tracking-wider">
                  🔐 Security Clearance
                </label>
                <div className="relative">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    disabled={loading}
                    className="w-full px-4 py-3 bg-slate-900/50 border border-cyan-400/30 hover:border-cyan-400/50 focus:border-cyan-400 rounded text-white placeholder-gray-500/60 focus:outline-none focus:ring-2 focus:ring-cyan-400/20 transition-all disabled:opacity-50"
                    placeholder="Enter your security clearance code"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    disabled={loading}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-cyan-400/60 hover:text-cyan-400 transition-colors disabled:opacity-50"
                  >
                    {showPassword ? '👁️' : '👁️‍🗨️'}
                  </button>
                </div>
              </div>

              {/* Login Button */}
              <button
                type="submit"
                disabled={loading || !username || !password}
                className="w-full py-3 bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-600 hover:to-blue-600 disabled:from-gray-600 disabled:to-gray-700 text-slate-950 font-bold uppercase tracking-widest rounded transition-all transform hover:scale-105 disabled:scale-100 disabled:opacity-60 font-mono text-sm shadow-lg hover:shadow-cyan-500/50"
              >
                {loading ? (
                  <span className="flex items-center justify-center gap-2">
                    <span className="inline-block w-4 h-4 border-2 border-slate-950 border-t-transparent rounded-full animate-spin"></span>
                    AUTHENTICATING...
                  </span>
                ) : (
                  '🔓 AUTHENTICATE ACCESS'
                )}
              </button>

              {/* Status Lights */}
              <div className="flex gap-4 pt-2">
                <div className="flex-1 flex items-center gap-2 text-xs text-gray-400 font-mono">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span>Database: CONNECTED</span>
                </div>
                <div className="flex-1 flex items-center gap-2 text-xs text-gray-400 font-mono">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span>Security: ACTIVE</span>
                </div>
              </div>
            </form>
          </div>

          {/* Footer */}
          <div className="border-t border-cyan-400/20 bg-slate-950/30 px-8 py-4">
            <p className="text-center text-xs text-gray-500 font-mono mb-2">
              🔐 Post-Quantum Cryptography (Dilithium/Kyber) Enabled
            </p>
            <p className="text-center text-xs text-gray-600 font-mono">
              © 2025 JARVIS Intelligence Systems • All rights reserved
            </p>
            <p className="text-center text-xs text-red-600/60 font-mono mt-3">
              VIOLATION OF FEDERAL LAW • UNAUTHORIZED ACCESS TO THIS SYSTEM IS PROHIBITED
            </p>
          </div>
        </div>

        {/* Bottom Secret Banner */}
        <div className="mt-6">
          <div className="bg-gradient-to-r from-red-900/20 to-red-800/10 border border-red-600/30 px-4 py-2 text-center">
            <p className="text-red-400 text-xs font-mono">
              SESSION MONITORING ACTIVE • ALL ACTIVITIES LOGGED AND MONITORED
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
