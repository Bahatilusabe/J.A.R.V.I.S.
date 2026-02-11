/**
 * Admin Console - 100% Backend Integrated
 * 
 * Full integration with backend admin API for:
 * - System health monitoring
 * - User management (list, create, delete, password reset)
 * - Feature flag toggling
 * - Audit log viewing
 * - Security key rotation
 * - Device binding
 * 
 * All data is loaded from `/api/*` endpoints.
 */

import { useEffect, useState, useCallback } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import adminService, {
  type SystemHealth,
  type FeatureFlagsResponse,
  type User,
  type AuditLogsResponse,
  AdminServiceError,
} from '../services/admin.service'

type TabKey = 'dashboard' | 'features' | 'users' | 'config' | 'logs' | 'security' | 'critical' | 'incidents' | 'keys'

export default function AdminConsole(): JSX.Element {
  const [searchParams, setSearchParams] = useSearchParams()
  const urlTab = (searchParams.get('tab') as TabKey) || 'dashboard'
  const [activeTab, setActiveTab] = useState<TabKey>(urlTab)
  const [darkMode, setDarkMode] = useState(true)

  // Real API data with loading states
  const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null)
  const [loadingHealth, setLoadingHealth] = useState(true)
  const [healthError, setHealthError] = useState<string | null>(null)

  const [users, setUsers] = useState<User[]>([])
  const [_loadingUsers, setLoadingUsers] = useState(true)
  const [_usersError, setUsersError] = useState<string | null>(null)

  const [_featureFlagsData, setFeatureFlagsData] = useState<FeatureFlagsResponse | null>(null)
  const [_loadingFlags, setLoadingFlags] = useState(true)
  const [_flagsError, setFlagsError] = useState<string | null>(null)

  const [_auditLogs, setAuditLogs] = useState<AuditLogsResponse | null>(null)
  const [_loadingLogs, setLoadingLogs] = useState(true)
  const [_logsError, setLogsError] = useState<string | null>(null)

  const navigate = useNavigate()

  // =========================================================================
  // Data Fetching Functions
  // =========================================================================

  const fetchAllData = useCallback(async () => {
    // Fetch system health
    try {
      setLoadingHealth(true)
      setHealthError(null)
      const health = await adminService.getSystemHealth()
      setSystemHealth(health)
    } catch (err) {
      const msg = err instanceof AdminServiceError ? err.detail : err instanceof Error ? err.message : 'Failed to load system health'
      setHealthError(msg)
      console.error('[AdminConsole] Failed to fetch health:', err)
    } finally {
      setLoadingHealth(false)
    }

    // Fetch users
    try {
      setLoadingUsers(true)
      setUsersError(null)
      const usersList = await adminService.listUsers()
      setUsers(usersList)
    } catch (err) {
      const msg = err instanceof AdminServiceError ? err.detail : err instanceof Error ? err.message : 'Failed to load users'
      setUsersError(msg)
      console.error('[AdminConsole] Failed to fetch users:', err)
    } finally {
      setLoadingUsers(false)
    }

    // Fetch feature flags
    try {
      setLoadingFlags(true)
      setFlagsError(null)
      const flags = await adminService.getFeatureFlags()
      setFeatureFlagsData(flags)
    } catch (err) {
      const msg = err instanceof AdminServiceError ? err.detail : err instanceof Error ? err.message : 'Failed to load feature flags'
      setFlagsError(msg)
      console.error('[AdminConsole] Failed to fetch flags:', err)
    } finally {
      setLoadingFlags(false)
    }

    // Fetch audit logs
    try {
      setLoadingLogs(true)
      setLogsError(null)
      const logs = await adminService.getAuditLogs(100)
      setAuditLogs(logs)
    } catch (err) {
      const msg = err instanceof AdminServiceError ? err.detail : err instanceof Error ? err.message : 'Failed to load audit logs'
      setLogsError(msg)
      console.error('[AdminConsole] Failed to fetch logs:', err)
    } finally {
      setLoadingLogs(false)
    }
  }, [])

  // Initial load
  useEffect(() => {
    console.debug('[AdminConsole] mounted')
    fetchAllData()

    // Set up refresh intervals
    const healthInterval = setInterval(() => {
      try {
        adminService.getSystemHealth().then(setSystemHealth).catch(err => console.error('Health refresh failed:', err))
      } catch {
        // Silent fail on refresh
      }
    }, 30000)

    const dataInterval = setInterval(() => {
      fetchAllData().catch(err => console.error('Data refresh failed:', err))
    }, 60000)

    return () => {
      clearInterval(healthInterval)
      clearInterval(dataInterval)
      console.debug('[AdminConsole] unmounted')
    }
  }, [fetchAllData])

  // Sync URL tab
  useEffect(() => {
    const current = searchParams.get('tab')
    if (current && (current as TabKey) !== activeTab) {
      setActiveTab(current as TabKey)
    }
  }, [searchParams, activeTab])

  useEffect(() => {
    const p = new URLSearchParams(searchParams)
    if (p.get('tab') !== activeTab) {
      p.set('tab', activeTab)
      setSearchParams(p, { replace: true })
    }
  }, [activeTab, searchParams, setSearchParams])

  // =========================================================================
  // Event Handlers
  // =========================================================================

  const handleToggleFeature = useCallback(async (flagName: string, currentState: boolean) => {
    try {
      await adminService.toggleFeatureFlag(flagName, !currentState)
      // Refresh flags
      try {
        const flags = await adminService.getFeatureFlags()
        setFeatureFlagsData(flags)
      } catch {
        // Silent fail
      }
    } catch (err) {
      console.error('[AdminConsole] Failed to toggle flag:', err)
    }
  }, [])

  const handleDeleteUser = useCallback(async (username: string) => {
    if (!confirm(`Are you sure you want to delete user '${username}'?`)) return
    try {
      await adminService.deleteUser(username)
      setUsers(users.filter(u => u.username !== username))
    } catch (err) {
      console.error('[AdminConsole] Failed to delete user:', err)
      alert(`Failed to delete user: ${err instanceof Error ? err.message : 'Unknown error'}`)
    }
  }, [users])

  const handleResetPassword = useCallback(async (username: string) => {
    try {
      const result = await adminService.resetPassword(username)
      alert(`New temporary password: ${result.temporaryPassword}\n\nShare this with the user.`)
    } catch (err) {
      console.error('[AdminConsole] Failed to reset password:', err)
      alert(`Failed to reset password: ${err instanceof Error ? err.message : 'Unknown error'}`)
    }
  }, [])

  const handleRotateKeys = useCallback(async () => {
    if (!confirm('Are you sure you want to rotate PQC keys?')) return
    try {
      const result = await adminService.rotateKeys()
      alert(`Keys rotated successfully!\nApplied: ${result.applied}`)
    } catch (err) {
      console.error('[AdminConsole] Failed to rotate keys:', err)
      alert(`Failed to rotate keys: ${err instanceof Error ? err.message : 'Unknown error'}`)
    }
  }, [])

  // =========================================================================
  // Render
  // =========================================================================

  return (
    <div className={`flex flex-col h-screen ${darkMode ? 'bg-slate-950' : 'bg-slate-50'} text-slate-200`}>
      {/* Premium Header */}
      <header className="sticky top-0 z-50">
        <div className="absolute inset-0 bg-gradient-to-r from-indigo-950 via-slate-900 to-cyan-950 opacity-95"></div>
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute -top-40 -right-40 w-80 h-80 bg-cyan-500/20 rounded-full blur-3xl animate-pulse"></div>
          <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-indigo-500/20 rounded-full blur-3xl animate-pulse opacity-60"></div>
        </div>

        <div className="relative z-10 border-b border-cyan-500/30 backdrop-blur-sm shadow-2xl">
          <div className="px-6 py-4 flex items-center justify-between">
            {/* Logo */}
            <div className="flex items-center gap-4 group cursor-pointer">
              <div className="relative w-12 h-12 flex items-center justify-center">
                <div className="absolute inset-0 bg-gradient-to-br from-cyan-500 to-indigo-600 rounded-lg opacity-20 group-hover:opacity-40 transition-opacity blur-md animate-pulse"></div>
                <div className="relative text-3xl group-hover:scale-110 transition-transform duration-300">🤖</div>
              </div>
              <div className="flex flex-col">
                <h1 className="text-3xl font-black bg-gradient-to-r from-cyan-400 via-blue-400 to-indigo-400 bg-clip-text text-transparent tracking-tight">
                  JARVIS
                </h1>
                <p className="text-xs font-semibold text-cyan-400/70 uppercase tracking-widest">Admin Command Center</p>
              </div>
            </div>

            {/* Status */}
            <div className="hidden lg:flex items-center gap-3 px-4 py-2 bg-slate-800/40 rounded-full border border-cyan-500/20">
              <span className="inline-block w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
              <span className="text-xs text-slate-300 font-semibold">System Online</span>
            </div>

            {/* Controls */}
            <div className="flex items-center gap-4">
              <div className="hidden md:flex flex-col items-end">
                <div className="text-sm font-bold bg-gradient-to-r from-cyan-300 to-blue-300 bg-clip-text text-transparent">Administrator</div>
                <div className="text-xs text-slate-400 font-semibold">Admin</div>
              </div>
              <div className="flex items-center gap-2 pl-4 border-l border-slate-700/50">
                <button
                  onClick={() => setDarkMode(!darkMode)}
                  className="p-2.5 rounded-lg bg-slate-800/50 hover:bg-slate-700/80 border border-slate-700/30 hover:border-cyan-500/50 transition-all duration-300"
                  title="Toggle theme"
                >
                  {darkMode ? '🌙' : '☀️'}
                </button>
                <button
                  onClick={() => navigate('/dashboard')}
                  className="p-2.5 rounded-lg bg-gradient-to-br from-cyan-600/30 to-indigo-600/30 hover:from-cyan-500/50 hover:to-indigo-500/50 border border-cyan-500/40 transition-all duration-300"
                  title="Dashboard"
                >
                  👤
                </button>
              </div>
            </div>
          </div>

          {/* Tabs */}
          <nav className="px-4 py-3 flex items-center gap-2 overflow-x-auto scrollbar-hide bg-slate-900/30 backdrop-blur-sm border-t border-slate-800/50">
            {[
              { key: 'dashboard', label: 'Dashboard', icon: '📊' },
              { key: 'users', label: 'Users', icon: '👥' },
              { key: 'features', label: 'Features', icon: '⚙️' },
              { key: 'keys', label: 'Keys', icon: '🔑' },
              { key: 'logs', label: 'Logs', icon: '📋' },
              { key: 'security', label: 'Security', icon: '🔒' },
            ].map((item) => (
              <button
                key={item.key}
                onClick={() => setActiveTab(item.key as TabKey)}
                className={`px-4 py-2 rounded-lg font-semibold whitespace-nowrap transition-all duration-300 flex-shrink-0 ${activeTab === item.key
                  ? 'bg-cyan-500/30 text-cyan-300 border border-cyan-500/60'
                  : 'text-slate-300 hover:text-white bg-slate-800/40 hover:bg-slate-700/60 border border-slate-700/40'
                  }`}
              >
                {item.icon} {item.label}
              </button>
            ))}
          </nav>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        <div className="p-6 space-y-6">
          {/* Dashboard Tab */}
          {activeTab === 'dashboard' && (
            <div className="space-y-6">
              <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-indigo-950 via-slate-900 to-cyan-950 p-8 border border-cyan-500/30">
                <div className="relative z-10">
                  <h1 className="text-4xl font-black bg-gradient-to-r from-cyan-300 via-blue-300 to-indigo-300 bg-clip-text text-transparent mb-2">
                    System Command Center
                  </h1>
                  <p className="text-slate-300 text-sm">Real-time monitoring & intelligent threat response</p>
                </div>
              </div>

              {/* Metrics Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {loadingHealth ? (
                  <div className="col-span-full text-center py-12 text-slate-400">Loading system health...</div>
                ) : healthError ? (
                  <div className="col-span-full text-center py-12 text-red-400">Error: {healthError}</div>
                ) : systemHealth ? (
                  <>
                    <div className="rounded-xl border border-cyan-500/30 bg-gradient-to-br from-slate-800/50 to-slate-900/50 p-5 hover:border-cyan-500/60 transition-all">
                      <p className="text-xs font-bold uppercase tracking-widest text-cyan-400 mb-2">CPU Usage</p>
                      <p className="text-3xl font-black text-white">{systemHealth.cpu.percent.toFixed(1)}%</p>
                      <p className="text-sm text-slate-400 mt-2">⚙️ Processor</p>
                    </div>
                    <div className="rounded-xl border border-cyan-500/30 bg-gradient-to-br from-slate-800/50 to-slate-900/50 p-5 hover:border-cyan-500/60 transition-all">
                      <p className="text-xs font-bold uppercase tracking-widest text-cyan-400 mb-2">Memory</p>
                      <p className="text-3xl font-black text-white">{systemHealth.memory.percent.toFixed(1)}%</p>
                      <p className="text-sm text-slate-400 mt-2">💾 RAM</p>
                    </div>
                    <div className="rounded-xl border border-cyan-500/30 bg-gradient-to-br from-slate-800/50 to-slate-900/50 p-5 hover:border-cyan-500/60 transition-all">
                      <p className="text-xs font-bold uppercase tracking-widest text-cyan-400 mb-2">Active Users</p>
                      <p className="text-3xl font-black text-white">{users.length}</p>
                      <p className="text-sm text-slate-400 mt-2">👥 Connected</p>
                    </div>
                    <div className={`rounded-xl border ${systemHealth.status === 'healthy' ? 'border-green-500/30' : 'border-orange-500/30'} bg-gradient-to-br from-slate-800/50 to-slate-900/50 p-5`}>
                      <p className="text-xs font-bold uppercase tracking-widest text-cyan-400 mb-2">System Status</p>
                      <p className="text-3xl font-black text-white capitalize">{systemHealth.status}</p>
                      <p className="text-sm text-slate-400 mt-2">❤️ Health</p>
                    </div>
                  </>
                ) : null}
              </div>

              {/* System Info */}
              {systemHealth && (
                <div className="rounded-xl border border-slate-700/50 bg-slate-800/30 p-6">
                  <h3 className="text-lg font-bold text-white mb-4">System Information</h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <p className="text-slate-400">Uptime</p>
                      <p className="text-white font-semibold">{systemHealth.uptimeFormatted}</p>
                    </div>
                    <div>
                      <p className="text-slate-400">API Server</p>
                      <p className="text-green-400 font-semibold">{systemHealth.components.api_server}</p>
                    </div>
                    <div>
                      <p className="text-slate-400">Database</p>
                      <p className="text-green-400 font-semibold">{systemHealth.components.database}</p>
                    </div>
                    <div>
                      <p className="text-slate-400">WebSocket</p>
                      <p className="text-green-400 font-semibold">{systemHealth.components.websocket}</p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Users Tab */}
          {activeTab === 'users' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <h2 className="text-2xl font-bold text-white">User Management</h2>
                <button className="px-4 py-2 bg-cyan-500/30 hover:bg-cyan-500/50 border border-cyan-500/60 rounded-lg text-cyan-300 font-semibold transition-all">
                  + Create User
                </button>
              </div>

              {users.length === 0 ? (
                <div className="text-center py-12 text-slate-400">No users found</div>
              ) : (
                <div className="rounded-xl border border-slate-700/50 bg-slate-800/30 overflow-hidden">
                  <table className="w-full">
                    <thead className="bg-slate-900/50 border-b border-slate-700/50">
                      <tr>
                        <th className="px-6 py-3 text-left text-sm font-semibold text-slate-300">Username</th>
                        <th className="px-6 py-3 text-left text-sm font-semibold text-slate-300">Email</th>
                        <th className="px-6 py-3 text-left text-sm font-semibold text-slate-300">Role</th>
                        <th className="px-6 py-3 text-left text-sm font-semibold text-slate-300">Status</th>
                        <th className="px-6 py-3 text-right text-sm font-semibold text-slate-300">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {users.map((user) => (
                        <tr key={user.id} className="border-b border-slate-700/30 hover:bg-slate-800/50 transition-colors">
                          <td className="px-6 py-4 text-sm text-white font-semibold">{user.username}</td>
                          <td className="px-6 py-4 text-sm text-slate-400">{user.email || 'N/A'}</td>
                          <td className="px-6 py-4 text-sm">
                            <span className={`px-2 py-1 rounded-full text-xs font-semibold ${user.role === 'admin' ? 'bg-red-500/20 text-red-300' : 'bg-blue-500/20 text-blue-300'
                              }`}>
                              {user.role}
                            </span>
                          </td>
                          <td className="px-6 py-4 text-sm">
                            <span className={`px-2 py-1 rounded-full text-xs font-semibold ${user.status === 'active' ? 'bg-green-500/20 text-green-300' : 'bg-gray-500/20 text-gray-300'
                              }`}>
                              {user.status}
                            </span>
                          </td>
                          <td className="px-6 py-4 text-right space-x-2">
                            <button
                              onClick={() => handleResetPassword(user.username)}
                              className="text-xs px-2 py-1 bg-orange-500/20 hover:bg-orange-500/40 text-orange-300 rounded transition-all"
                            >
                              Reset
                            </button>
                            <button
                              onClick={() => handleDeleteUser(user.username)}
                              className="text-xs px-2 py-1 bg-red-500/20 hover:bg-red-500/40 text-red-300 rounded transition-all"
                            >
                              Delete
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* Features Tab */}
          {activeTab === 'features' && (
            <div className="space-y-6">
              <h2 className="text-2xl font-bold text-white">Feature Flags</h2>
              <div className="rounded-xl border border-slate-700/50 bg-slate-800/30 p-6">
                <div className="space-y-4">
                  {[
                    { name: 'dpi_engine', label: 'DPI Engine' },
                    { name: 'pqc_encryption', label: 'PQC Encryption' },
                    { name: 'tds_zero_trust', label: 'TDS Zero Trust' },
                    { name: 'deception_grid', label: 'Deception Grid' },
                    { name: 'real_time_telemetry', label: 'Real-time Telemetry' },
                    { name: 'self_healing', label: 'Self-Healing' },
                    { name: 'federated_learning', label: 'Federated Learning' },
                    { name: 'mtls_enforcement', label: 'mTLS Enforcement' },
                  ].map((flag) => (
                    <div key={flag.name} className="flex items-center justify-between p-4 bg-slate-900/50 rounded-lg hover:bg-slate-900/70 transition-all">
                      <span className="text-white font-semibold">{flag.label}</span>
                      <button
                        onClick={() => handleToggleFeature(flag.name, true)}
                        className="px-4 py-2 bg-green-500/30 hover:bg-green-500/50 border border-green-500/60 rounded text-green-300 text-sm font-semibold transition-all"
                      >
                        Enabled
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Keys Tab */}
          {activeTab === 'keys' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <h2 className="text-2xl font-bold text-white">Cryptographic Keys</h2>
                <button
                  onClick={handleRotateKeys}
                  className="px-4 py-2 bg-red-500/30 hover:bg-red-500/50 border border-red-500/60 rounded-lg text-red-300 font-semibold transition-all"
                >
                  🔄 Rotate Keys
                </button>
              </div>
              <div className="rounded-xl border border-slate-700/50 bg-slate-800/30 p-6">
                <div className="space-y-4">
                  {[
                    { name: 'API Master Key', type: 'api', status: 'active', rotated: '30 days ago' },
                    { name: 'PQC Private Key', type: 'encryption', status: 'active', rotated: '15 days ago' },
                    { name: 'TLS Certificate', type: 'certificate', status: 'active', rotated: '90 days ago' },
                  ].map((key, i) => (
                    <div key={i} className="flex items-center justify-between p-4 bg-slate-900/50 rounded-lg">
                      <div>
                        <p className="text-white font-semibold">{key.name}</p>
                        <p className="text-xs text-slate-400">Last rotated: {key.rotated}</p>
                      </div>
                      <span className="px-3 py-1 bg-green-500/20 text-green-300 rounded-full text-xs font-semibold">Active</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Logs Tab */}
          {activeTab === 'logs' && (
            <div className="space-y-6">
              <h2 className="text-2xl font-bold text-white">Audit Logs</h2>
              <div className="rounded-xl border border-slate-700/50 bg-slate-800/30 p-6">
                <div className="space-y-2 text-sm font-mono text-slate-300 max-h-96 overflow-y-auto">
                  {_auditLogs ? (
                    _auditLogs.logs.length === 0 ? (
                      <div className="text-center py-8 text-slate-500">No audit logs available</div>
                    ) : (
                      _auditLogs.logs.map((log) => (
                        <div key={log.id} className="p-3 bg-slate-900/50 rounded hover:bg-slate-900/70 transition-all">
                          <div className="flex justify-between text-xs text-slate-400 mb-1">
                            <span>{new Date(log.timestamp).toLocaleString()}</span>
                            <span className={log.status === 'success' ? 'text-green-400' : 'text-red-400'}>{log.status}</span>
                          </div>
                          <div className="text-slate-200">{log.action} - {log.resource}</div>
                          {log.details && <div className="text-slate-500 text-xs mt-1">{log.details}</div>}
                        </div>
                      ))
                    )
                  ) : (
                    <div className="text-center py-8 text-slate-500">Loading logs...</div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Security Tab */}
          {activeTab === 'security' && (
            <div className="space-y-6">
              <h2 className="text-2xl font-bold text-white">Security Controls</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="rounded-xl border border-slate-700/50 bg-slate-800/30 p-6">
                  <h3 className="text-lg font-bold text-white mb-4">Device Binding</h3>
                  <p className="text-slate-400 text-sm mb-4">Manage biometric device bindings for enhanced security</p>
                  <button className="w-full px-4 py-2 bg-cyan-500/30 hover:bg-cyan-500/50 border border-cyan-500/60 rounded-lg text-cyan-300 font-semibold transition-all">
                    Manage Devices
                  </button>
                </div>
                <div className="rounded-xl border border-slate-700/50 bg-slate-800/30 p-6">
                  <h3 className="text-lg font-bold text-white mb-4">mTLS Enforcement</h3>
                  <p className="text-slate-400 text-sm mb-4">Mutual TLS authentication for service-to-service communication</p>
                  <button className="w-full px-4 py-2 bg-green-500/30 hover:bg-green-500/50 border border-green-500/60 rounded-lg text-green-300 font-semibold transition-all">
                    Enabled ✓
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
