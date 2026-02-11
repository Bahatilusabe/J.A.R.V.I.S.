import { useState, useEffect, startTransition } from 'react'
import { useNavigate } from 'react-router-dom'
import useSystemStatus from '../hooks/useSystemStatus'
import { StatusChip } from './StatusChip'

/**
 * System Topbar Component
 * Displays: system time, node health, voice activation, user identity, federated sync
 * Advanced real-time monitoring with visual indicators
 */
export function SystemBar() {
  // Hide the entire system bar on overview/dashboard/military pages as requested
  const { systemStatus, error } = useSystemStatus()
  const navigate = useNavigate()
  const [currentTime, setCurrentTime] = useState(new Date())
  const [showUserMenu, setShowUserMenu] = useState(false)

  // Update clock
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentTime(new Date())
    }, 1000)

    return () => clearInterval(interval)
  }, [])

  const timeString = currentTime.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: true,
  })

  const dateString = currentTime.toLocaleDateString('en-US', {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
  })

  // Previously the system bar was hidden on overview pages. Render it on all pages to keep the top bar consistent.

  // The center status panel has been removed entirely.

  // Voice activation is handled either via the topbar mic popover (uses useVocalSOC)
  // or via dedicated VocalSOC page. Keep this handler removed to avoid duplication.

  const handleLogout = async () => {
    try {
      // Clear auth token and session from localStorage
      localStorage.removeItem('authToken')
      localStorage.removeItem('userSession')
      localStorage.removeItem('user')

      // Close user menu dropdown
      setShowUserMenu(false)

      // Navigate to login page
      startTransition(() => navigate('/login'))
    } catch (error) {
      console.error('Logout error:', error)
    }
  }

  // Pulse animation for critical states
  const isPulsing = systemStatus?.threatLevel === 'critical' || systemStatus?.mode === 'under_attack'

  return (
    <div className={`system-bar sticky top-0 z-40 flex items-center justify-between px-4 py-3 bg-gradient-to-b from-slate-900/70 to-transparent border-b border-slate-800/30 backdrop-blur-sm ${isPulsing ? 'animate-pulse' : ''}`}>
      {/* Left: System Status and Time */}
      <div className="flex items-center gap-4">
        {/* Status Chip */}
        {systemStatus && (
          <StatusChip
            mode={systemStatus.mode}
            threatLevel={systemStatus.threatLevel}
            animated={true}
          />
        )}

        {/* Time and Date */}
        <div className="text-xs text-slate-400 font-mono tracking-wider">
          <div className="text-slate-300">{timeString}</div>
          <div className="text-slate-500">{dateString}</div>
        </div>
      </div>

      {/* Center status removed */}
      <div className="flex-1" />

      {/* Right: Voice and User Controls */}
      <div className="flex items-center gap-3">
        {/* Error Indicator */}
        {error && (
          <div className="px-2 py-1 rounded text-xs bg-red-500/20 text-red-400 border border-red-500/50 max-w-xs truncate">
            {error}
          </div>
        )}

        {/* Admin access has been moved to the main topbar (Layout) to avoid duplication */}

        {/* User Menu Button */}
        <div className="relative flex items-center gap-2">
          {/* Small caret/button to open the user menu for settings/logout */}
          <div className="relative">
            <button
              onClick={() => setShowUserMenu(!showUserMenu)}
              className="px-2 py-1 rounded bg-slate-800/50 border border-slate-700/50 hover:bg-slate-700/50 transition-colors"
              title="User Menu"
            >
              ▾
            </button>

            {/* User Menu Dropdown (settings/logout) */}
            {showUserMenu && (
              <div className="absolute right-0 top-full mt-2 w-48 bg-slate-800 border border-slate-700 rounded-lg shadow-lg z-50 overflow-hidden">
                <div className="px-4 py-3 border-b border-slate-700">
                  <div className="font-medium text-slate-200 text-sm">System Administrator</div>
                  <div className="text-xs text-slate-500 mt-1">NODE-01 • CONSCIOUS MODE</div>
                </div>
                <div className="p-2 space-y-1">
                  <button className="w-full text-left px-3 py-2 rounded text-xs text-slate-300 hover:bg-slate-700/50 transition-colors" onClick={() => startTransition(() => navigate('/settings'))}>
                    ⚙️ Settings
                  </button>
                  <button className="w-full text-left px-3 py-2 rounded text-xs text-slate-300 hover:bg-slate-700/50 transition-colors">
                    📊 Profile
                  </button>
                  <button className="w-full text-left px-3 py-2 rounded text-xs text-slate-300 hover:bg-slate-700/50 transition-colors">
                    🔐 Security
                  </button>
                  <div className="border-t border-slate-700 my-1" />
                  <button className="w-full text-left px-3 py-2 rounded text-xs text-red-400 hover:bg-red-500/10 transition-colors" onClick={handleLogout}>
                    🚪 Logout
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default SystemBar
