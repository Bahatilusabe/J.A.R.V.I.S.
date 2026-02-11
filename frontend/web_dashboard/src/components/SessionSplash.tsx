import React from 'react'
import styles from './SessionSplash.module.css'

interface SessionSplashProps {
  sessionMessage: string
  sessionError: string | null
  onRetry: () => void
}

// (Removed DataStream/particle visualizations — replaced by shield concentric ring lanes)

// (Removed GlobalMapSphere — focus is on the shield visual)

export const SessionSplash: React.FC<SessionSplashProps> = ({ sessionMessage, sessionError, onRetry }) => {
  // Normalize certain backend error messages for UI clarity
  const displayError = React.useMemo(() => {
    if (!sessionError) return null
    // Map known backend phrases to UI-friendly labels
    const lowered = sessionError.toLowerCase()
    if (lowered.includes('backend services offline') || lowered.includes('backend offline')) {
      return 'Base Station Off_Grid'
    }
    return sessionError
  }, [sessionError])

  const displayMessage = React.useMemo(() => {
    if (!sessionMessage) return sessionMessage
    const lowered = sessionMessage.toLowerCase()
    if (lowered.includes('backend services offline') || lowered.includes('backend offline')) {
      return 'Base Station Off_Grid'
    }
    return sessionMessage
  }, [sessionMessage])

  // Local UI state for briefly showing Access Granted animation
  const [showAccessGranted, setShowAccessGranted] = React.useState(false)

  React.useEffect(() => {
    const msg = (displayMessage || '').toLowerCase()
    if (msg.includes('secure session established') || msg.includes('access granted') || msg.includes('✓')) {
      setShowAccessGranted(true)
      const t = setTimeout(() => setShowAccessGranted(false), 900)
      return () => clearTimeout(t)
    }
    return undefined
  }, [displayMessage])

  // When a session error occurs, automatically attempt re-initialization every few seconds
  React.useEffect(() => {
    if (!sessionError) return
    const retryInterval = setInterval(() => {
      try {
        onRetry()
      } catch (e) {
        // swallow errors from caller; Login.initSession will log
      }
    }, 5000)
    return () => clearInterval(retryInterval)
  }, [sessionError, onRetry])

  return (
    <div className={`min-h-screen bg-gradient-to-br from-slate-950 via-blue-950 to-slate-900 flex items-center justify-center p-4 relative overflow-hidden ${styles['splash-container']}`}>
      {/* Background grid */}
      <div className="absolute inset-0 opacity-12 pointer-events-none flex items-center justify-center">
        {/* Replace the full-bleed rect with a centered cyber-security shield graphic */}
        <div className={styles['security-shield']} aria-hidden>
          <div className={styles['shield-glow']} />
          <svg className={styles['shield-svg']} viewBox="0 0 200 220" xmlns="http://www.w3.org/2000/svg" role="img">
            <defs>
              <linearGradient id="shieldGrad" x1="0%" x2="0%" y1="0%" y2="100%">
                <stop offset="0%" stopColor="#08f1ea" stopOpacity="0.08"/>
                <stop offset="100%" stopColor="#00121a" stopOpacity="0.12"/>
              </linearGradient>
            </defs>
            {/* Shield core */}
            <path className={styles['shield-core']} d="M100 8 L170 40 V100 C170 150 140 190 100 210 C60 190 30 150 30 100 V40 Z" fill="url(#shieldGrad)" />
            {/* Shield outline */}
            <path className={styles['shield-outline']} d="M100 12 L165 42 V100 C165 148 136 186 100 204 C64 186 35 148 35 100 V42 Z" />
            {/* Accent scan stroke */}
            <path className={styles['shield-accent']} d="M100 22 L150 48 V100 C150 140 130 170 100 186 C70 170 50 140 50 100 V48 Z" />
            {/* subtle star emblem centered inside shield */}
            <g transform="translate(100,110) scale(0.85)" aria-hidden>
              {/* 5-point star polygon (centered to shield inner circle) */}
              <polygon points="0,-12 3.6,-3.7 12,-3.7 5.2,2.2 7.7,11 0,6.5 -7.7,11 -5.2,2.2 -12,-3.7 -3.6,-3.7" className={styles['shield-emblem']} />
            </g>
          </svg>
        </div>
      </div>

      {/* Concentric ring lanes around shield (SVG rings) */}
      <div className={styles['shield-rings']} aria-hidden>
        <svg viewBox="0 0 300 300" className={styles['shield-svg']}>
          <circle className={`${styles['shield-ring']} ${styles['shield-ring-3']}`} cx="150" cy="150" r="110" />
          <circle className={`${styles['shield-ring']} ${styles['shield-ring-2']}`} cx="150" cy="150" r="80" />
          <circle className={`${styles['shield-ring']} ${styles['shield-ring-1']}`} cx="150" cy="150" r="50" />
        </svg>
      </div>

      <div className="w-full max-w-5xl relative z-10">
        <div className="mb-8 text-center">
          <div className="bg-gradient-to-r from-red-900/40 to-red-800/20 border-t-2 border-b-2 border-red-600/60 px-8 py-3 text-center backdrop-blur-sm inline-block rounded-md shadow-sm">
            <p className="text-red-500 text-sm md:text-base font-mono font-semibold tracking-widest uppercase">⚠ CLASSIFIED INITIALIZATION PROTOCOL ⚠</p>
          </div>
        </div>

  <div className={`bg-gradient-to-br from-slate-800/50 to-slate-900/50 backdrop-blur-3xl rounded-2xl border border-cyan-400/60 shadow-2xl shadow-cyan-400/20 p-16 md:p-20 ${styles['panel-translucent']}`}>
          <div className="text-center mb-8">
            <div className="relative inline-block">
              <div className={`absolute inset-0 ${styles['logo-glow']}`}></div>
              <h1 className="text-6xl md:text-7xl lg:text-8xl font-black text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-blue-400 to-cyan-300 mb-2 tracking-wide leading-tight relative z-10">J.A.R.V.I.S</h1>
              <p className="text-cyan-300/70 font-mono text-xs tracking-widest">SECURE SESSION INITIALIZATION</p>
            </div>
          </div>

          <div className="h-20 md:h-24 flex items-center justify-center mb-8">
              <p className={`text-xl md:text-2xl font-mono text-center font-semibold ${styles['typewriter-text']}`}>
              <span className="text-cyan-300">{displayMessage}</span>
              <span className={styles['typing-cursor']}>▌</span>
            </p>
          </div>

          

          <div className="grid grid-cols-3 gap-8 mb-8 text-center">
            {[
              { label: 'NETWORK', color: sessionError ? 'red' : 'green' },
              { label: 'AUTH', color: sessionError ? 'red' : 'green' },
              { label: 'SECURE', color: sessionError ? 'red' : 'green' },
            ].map((status) => (
              <div key={status.label} className="space-y-3">
                <div className="flex justify-center">
                  <div
                    className={`w-4 h-4 rounded-full animate-pulse shadow-lg ${
                      status.color === 'green' ? 'bg-green-400 shadow-green-400/50' : 'bg-red-500 shadow-red-500/50'
                    }`}
                  ></div>
                </div>
                <p className={`text-xs font-mono font-semibold ${status.color === 'green' ? 'text-green-400' : 'text-red-400'}`}>{status.label}</p>
              </div>
            ))}
          </div>

          <div className="mb-4 text-center">
            {sessionError ? (
              <div className="space-y-4">
                <div className={`rounded-lg px-6 py-5 text-center ${styles['failure-position']}`}>
                  {/* Boot in progress / start attempted */}
                  {(displayMessage || '').toLowerCase().includes('boot') || (displayMessage || '').toLowerCase().includes('bootstrap') || (displayMessage || '').toLowerCase().includes('initiated') ? (
                    <div className={`bg-red-900/30 border border-red-500/50 backdrop-blur-sm`}> 
                      <p className="text-red-400 text-sm font-mono mb-2 font-semibold">⚠ SESSION INITIALIZATION FAILED ⚠</p>
                      <div className={`boot-indicator ${styles['boot-indicator'] || ''} mb-2`}>
                        <div className={`boot-spinner ${styles['boot-spinner'] || ''}`}></div>
                        <div className="text-left">
                          <p className="text-red-300 text-sm font-mono mb-1">Boot sequence initiated — attempting remote recovery</p>
                          <p className={`boot-caption ${styles['boot-caption'] || ''}`}>Remote start triggered • polling command center</p>
                        </div>
                      </div>
                      <p className="text-red-300 text-xs font-mono/80">Automatic reinitialization in progress — please stand by</p>
                    </div>
                  ) : showAccessGranted ? (
                    <div className={`${styles['access-granted']} access-granted`}> 
                      <div className={styles['check']}> 
                        <span>✓</span>
                      </div>
                      <div>
                        <p className="text-sm font-mono font-bold text-cyan-900">ACCESS GRANTED</p>
                        <p className="text-xs boot-caption">Secure session established — redirecting</p>
                      </div>
                    </div>
                  ) : (
                    <div className={`bg-red-900/30 border border-red-500/50 rounded-lg px-6 py-5 text-center backdrop-blur-sm`}>
                      <p className="text-red-400 text-sm font-mono mb-2 font-semibold">⚠ SESSION INITIALIZATION FAILED ⚠</p>
                      <p className="text-red-300 text-sm font-mono mb-1">{displayError}</p>
                      <p className="text-red-300 text-xs font-mono/80">Attempting automatic reinitialization — standing by...</p>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <p className="text-center text-xs text-cyan-300/60 font-mono">Encrypting channel • PQC authentication active • Quantum-safe protocols enabled</p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default SessionSplash

