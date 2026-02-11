import { useState, useEffect, startTransition } from 'react'
import { useNavigate } from 'react-router-dom'
// styles removed; page simplified

export default function Home() {
  const navigate = useNavigate()
  const [isLoggedIn, setIsLoggedIn] = useState(false)

  useEffect(() => {
    // Check if user is logged in
    const token = localStorage.getItem('access_token')
    setIsLoggedIn(!!token)
  }, [])

  const handleGetStarted = () => {
    if (isLoggedIn) {
      startTransition(() => navigate('/dashboard'))
    } else {
      startTransition(() => navigate('/login'))
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-purple-950 to-slate-900 overflow-hidden relative">
      {/* Simplified homepage - marketing content removed per request */}
      <div className="absolute inset-0 opacity-10">
        <svg width="100%" height="100%">
          <defs>
            <pattern id="grid" width="50" height="50" patternUnits="userSpaceOnUse">
              <path d="M 50 0 L 0 0 0 50" fill="none" stroke="#a78bfa" strokeWidth="0.5" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#grid)" />
        </svg>
      </div>

      <div className="relative z-10 flex items-center justify-center px-6 py-24">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-white mb-4">Welcome</h1>
          <p className="text-gray-300 max-w-xl mx-auto">The marketing section has been removed. Use the navigation to access the dashboard or login.</p>
          <div className="mt-8 flex items-center justify-center gap-4">
            <button onClick={handleGetStarted} className="px-6 py-3 bg-purple-600 text-white rounded-full">{isLoggedIn ? 'Go to Dashboard' : 'Get Started'}</button>
          </div>
        </div>
      </div>
    </div>
  )
}

// FutureSphere removed to eliminate marketing visuals per user's request
