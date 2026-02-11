import { ReactNode, useState, useEffect, useRef, startTransition } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import SidePanel from './SidePanel'
import authService from '../services/auth.service'
import { MicRing } from './MicRing'
import { useVocalSOC } from '../hooks/useVocalSOC'

interface LayoutProps {
  children: ReactNode
}

export default function Layout({ children }: LayoutProps) {
  const navigate = useNavigate()
  const location = useLocation()
  const [collapsed, setCollapsed] = useState(false)
  const [userName, setUserName] = useState('User')
  const [unreadNotifications, setUnreadNotifications] = useState(3)
  const [showNotifications, setShowNotifications] = useState(false)
  const [darkMode, setDarkMode] = useState(true)
  const [currentTime, setCurrentTime] = useState(new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }))
  const [showMicPopover, setShowMicPopover] = useState(false)
  const micButtonRef = useRef<HTMLButtonElement | null>(null)
  const vocal = useVocalSOC()

  // Hide the compact "System" status panel on overview pages (dashboard/military/root)
  const hideSystemPanel = ['/', '/dashboard', '/military'].includes(location.pathname)

  useEffect(() => {
    // Fetch username from auth service or localStorage
    const user = localStorage.getItem('user_name') || 'Administrator'
    setUserName(user)

    // Update time every second
    const timer = setInterval(() => {
      setCurrentTime(new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }))
    }, 1000)

    return () => clearInterval(timer)
  }, [])

  useEffect(() => {
    const onLogout = () => {
      // Ensure auth storage cleaned up and navigate to login via router (SPA navigation)
      try {
        authService.logout()
      } catch (e) {
        // ignore
      }
      navigate('/login')
    }

    window.addEventListener('jarvis:logout', onLogout as EventListener)
    return () => {
      window.removeEventListener('jarvis:logout', onLogout as EventListener)
    }
  }, [navigate])

  const handleLogout = () => {
    try {
      // Use central authService to logout and navigate
      authService.logout()
      startTransition(() => navigate('/login'))
    } catch (error) {
      console.error('Logout error:', error)
    }
  }

  const handleNotificationClick = (_id: number) => {
    setUnreadNotifications(Math.max(0, unreadNotifications - 1))
  }

  return (
    <div className="flex h-screen bg-slate-900">
      <SidePanel collapsed={collapsed} onToggleCollapse={() => setCollapsed((s) => !s)} />

      <main className="flex-1 overflow-auto bg-slate-900">
        {/* Premium Top Navigation Bar */}
        <header className="relative bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 border-b border-cyan-500/20 px-8 py-4 shadow-2xl backdrop-blur-sm">
          {/* Animated background orbs */}
          <div className="absolute inset-0 overflow-hidden pointer-events-none">
            <div className="absolute -top-20 -left-20 w-64 h-64 bg-cyan-500/5 rounded-full blur-3xl animate-pulse"></div>
            <div className="absolute -top-20 -right-32 w-80 h-80 bg-indigo-500/5 rounded-full blur-3xl animate-pulse opacity-50"></div>
          </div>

          {/* Top accent line with gradient */}
          <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-cyan-500 to-transparent"></div>

          <div className="relative flex justify-between items-center">
            {/* Left Section: Logo & Status */}
            <div className="flex items-center gap-6">
              {/* Premium Logo */}
              <div className="flex items-center gap-3 group cursor-pointer hover:scale-105 transition-transform duration-300">
                <div className="relative w-10 h-10">
                  {/* Logo Circle with gradient */}
                  <div className="absolute inset-0 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-full blur opacity-75 group-hover:opacity-100 transition-opacity"></div>
                  <div className="relative flex items-center justify-center w-10 h-10 bg-slate-900 rounded-full border border-cyan-400/50 group-hover:border-cyan-400 transition-colors">
                    <span className="text-xs font-black bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">J</span>
                  </div>
                </div>
                <div className="hidden sm:flex flex-col gap-0 leading-tight">
                  <span className="text-sm font-bold bg-gradient-to-r from-cyan-400 via-blue-400 to-indigo-500 bg-clip-text text-transparent">J.A.R.V.I.S</span>
                  <span className="text-xs text-cyan-400/60 font-medium">v2.8.5</span>
                </div>
              </div>

              {/* System Status Indicator (hidden on overview/dashboard/military per user request) */}
              {!hideSystemPanel && (
                <div className="hidden md:flex items-center gap-2 px-4 py-2 bg-slate-800/50 border border-green-500/20 rounded-lg group hover:border-green-500/40 transition-all duration-300">
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                  <div className="flex flex-col gap-0 leading-tight">
                    <span className="text-xs text-gray-400">System</span>
                    <span className="text-sm font-semibold text-green-400">{currentTime}</span>
                  </div>
                </div>
              )}
            </div>

            {/* Center Section: Live Status (Hidden on mobile) */}
            <div className="hidden lg:flex items-center gap-3 px-4 py-2 bg-gradient-to-r from-cyan-500/10 to-blue-500/10 border border-cyan-500/20 rounded-lg backdrop-blur-sm">
              <div className="flex items-center gap-2">
                <div className="w-1.5 h-1.5 bg-cyan-400 rounded-full animate-bounce"></div>
                <span className="text-xs font-medium text-cyan-300">All Systems Operational</span>
              </div>
              <span className="text-cyan-400/40">•</span>
              <span className="text-xs text-cyan-300/60">Network Active</span>
            </div>

            {/* Right Section: User Controls */}
            <div className="flex items-center gap-3">
              {/* Notifications Bell */}
              <div className="relative group">
                <button
                  onClick={() => setShowNotifications(!showNotifications)}
                  className="relative p-2.5 text-gray-300 hover:text-cyan-400 transition-colors duration-300 rounded-lg hover:bg-slate-800/50 border border-transparent hover:border-cyan-500/20"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                  </svg>
                  {unreadNotifications > 0 && (
                    <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full animate-pulse"></span>
                  )}
                </button>

                {/* Notifications Dropdown */}
                {showNotifications && (
                  <div className="absolute right-0 mt-2 w-72 bg-gradient-to-b from-slate-800 to-slate-900 border border-cyan-500/30 rounded-xl shadow-2xl z-50 backdrop-blur-sm">
                    <div className="p-4 border-b border-cyan-500/20">
                      <h3 className="text-sm font-semibold text-white">Notifications</h3>
                    </div>
                    <div className="max-h-64 overflow-y-auto">
                      <div className="p-3 hover:bg-slate-700/50 border-b border-slate-700/30 cursor-pointer transition-colors group" onClick={() => handleNotificationClick(1)}>
                        <div className="flex items-start gap-2">
                          <div className="w-2 h-2 bg-cyan-400 rounded-full mt-1.5 flex-shrink-0"></div>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm text-cyan-300 font-medium">System Update Available</p>
                            <p className="text-xs text-gray-400">New security patches ready for deployment</p>
                            <span className="text-xs text-gray-500">2 mins ago</span>
                          </div>
                        </div>
                      </div>
                      <div className="p-3 hover:bg-slate-700/50 border-b border-slate-700/30 cursor-pointer transition-colors group" onClick={() => handleNotificationClick(2)}>
                        <div className="flex items-start gap-2">
                          <div className="w-2 h-2 bg-green-400 rounded-full mt-1.5 flex-shrink-0"></div>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm text-green-300 font-medium">Backup Completed</p>
                            <p className="text-xs text-gray-400">Weekly backup finished successfully</p>
                            <span className="text-xs text-gray-500">1 hour ago</span>
                          </div>
                        </div>
                      </div>
                      <div className="p-3 hover:bg-slate-700/50 cursor-pointer transition-colors group" onClick={() => handleNotificationClick(3)}>
                        <div className="flex items-start gap-2">
                          <div className="w-2 h-2 bg-orange-400 rounded-full mt-1.5 flex-shrink-0"></div>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm text-orange-300 font-medium">High Memory Usage</p>
                            <p className="text-xs text-gray-400">Memory utilization at 85%</p>
                            <span className="text-xs text-gray-500">5 mins ago</span>
                          </div>
                        </div>
                      </div>
                    </div>
                    <div className="p-3 border-t border-cyan-500/20 text-center">
                      <button className="text-xs text-cyan-400 hover:text-cyan-300 font-medium transition-colors">View All Notifications</button>
                    </div>
                  </div>
                )}
              </div>

              {/* Theme Toggle */}
              <button
                onClick={() => setDarkMode(!darkMode)}
                className="p-2.5 text-gray-300 hover:text-cyan-400 transition-colors duration-300 rounded-lg hover:bg-slate-800/50 border border-transparent hover:border-cyan-500/20"
              >
                {darkMode ? (
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z"></path>
                  </svg>
                ) : (
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.536l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.707.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.464 5.05l-.707-.707a1 1 0 00-1.414 1.414l.707.707zm5.414 5.414a1 1 0 01.707.293l.707-.707a1 1 0 01-1.414-1.414l-.707.707a1 1 0 01.707 1.121zM5 8a1 1 0 100-2H4a1 1 0 000 2h1z" clipRule="evenodd"></path>
                  </svg>
                )}
              </button>

              {/* Make the displayed user name the admin entry point */}
              <div className="hidden sm:flex items-center">
                <button
                  onClick={() => {
                    console.debug('[Layout] Administrator label clicked, navigating to /admin/login')
                    startTransition(() => navigate('/admin/login'))
                  }}
                  className="flex flex-col items-end gap-0 leading-tight px-3 py-1.5 rounded-lg hover:bg-slate-800/50 transition-colors"
                  title="Administrator Console"
                  aria-label="Open Administrator Console"
                >
                  <span className="text-sm font-semibold text-cyan-300">{userName}</span>
                  <span className="text-xs text-gray-400">Administrator</span>
                </button>
              </div>

              <div className="h-8 w-px bg-slate-600/30 mx-2" />

              <div className="flex items-center gap-3">
                <div className="relative">
                  <button
                    ref={micButtonRef}
                    onClick={() => setShowMicPopover((s) => !s)}
                    className={`relative p-2 rounded-full transition-all ${vocal.isRecording
                      ? 'bg-red-500/30 border border-red-500 text-red-400 animate-pulse'
                      : 'bg-slate-800/50 border border-slate-700/50 text-slate-400 hover:bg-slate-700/50'
                      }`}
                    title="Voice Command (Open microphone)"
                    aria-haspopup="true"
                  >
                    <span className="text-lg">{vocal.isRecording ? '🎙️' : '🎤'}</span>
                    {vocal.isRecording && <span className="absolute inset-0 rounded-full border-2 border-red-400 animate-pulse" />}
                  </button>

                  {showMicPopover && (
                    <div className="absolute right-0 mt-2 w-80 z-50">
                      <div className="bg-slate-800 border border-slate-700 rounded-lg shadow-lg p-3">
                        <div className="flex items-center justify-between mb-2">
                          <div className="text-sm font-semibold text-slate-200">Microphone</div>
                          <button onClick={() => setShowMicPopover(false)} className="text-slate-400 hover:text-slate-200" title="Close microphone panel">✕</button>
                        </div>
                        <MicRing
                          isRecording={vocal.isRecording}
                          audioLevel={vocal.audioLevel}
                          onStartRecording={async () => await vocal.startRecording()}
                          onStopRecording={() => vocal.stopRecording()}
                          waveformData={vocal.waveformData}
                        />
                      </div>
                    </div>
                  )}
                </div>

                <div className="relative group cursor-pointer">
                  <div className="absolute inset-0 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-full blur opacity-50 group-hover:opacity-75 transition-opacity"></div>
                  <div className="relative flex items-center justify-center w-9 h-9 bg-gradient-to-br from-cyan-400 to-blue-500 rounded-full border border-cyan-300/50 group-hover:border-cyan-300 transition-colors text-sm font-bold text-slate-900">
                    {userName.charAt(0).toUpperCase()}
                  </div>
                </div>

                <button onClick={handleLogout} className="ml-2 px-4 py-2 text-sm font-medium text-gray-200 hover:text-white bg-gradient-to-r from-red-500/10 to-rose-500/10 hover:from-red-500/20 hover:to-rose-500/20 border border-red-500/20 hover:border-red-500/40 rounded-lg transition-all duration-300 hover:shadow-lg hover:shadow-red-500/20">Logout</button>
              </div>
            </div>
          </div>
        </header>

        {children}
      </main>
    </div>
  )
}
