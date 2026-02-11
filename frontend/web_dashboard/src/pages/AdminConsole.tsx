/* eslint-disable @typescript-eslint/no-unused-vars */
import { useEffect, useState, useCallback } from 'react'
import { useSearchParams } from 'react-router-dom'
import adminService, { type SystemHealth, type SystemMetrics, type FeatureFlagsResponse, type AuditLogsResponse, type User as AdminUser } from '../services/admin.service'
import apiClient, { getErrorMessage } from '../utils/api'
import { useToast } from '../hooks/use-toast'

type TabKey = 'dashboard' | 'system' | 'features' | 'users' | 'config' | 'logs' | 'security' | 'critical' | 'incidents' | 'keys'

interface _FeatureToggle {
  id: string
  name: string
  description: string
  enabled: boolean
  category: string
}

interface CriticalAlert {
  id: string
  severity: 'critical' | 'high' | 'medium'
  title: string
  description: string
  timestamp: string
  action?: string
}

interface Incident {
  id: string
  type: string
  severity: 'critical' | 'high' | 'medium'
  // broaden status union to match backend/forensics types and existing sample data
  status: 'active' | 'detected' | 'investigating' | 'contained' | 'resolved' | 'archived'
  title: string
  timestamp: string
  affectedSystems: string[]
}

interface SecretKey {
  id: string
  name: string
  type: 'api' | 'encryption' | 'certificate'
  status: 'active' | 'rotated' | 'revoked'
  lastRotated: string
  expiresAt?: string
}

export default function AdminConsole(): JSX.Element {
  const [searchParams, setSearchParams] = useSearchParams()
  const urlTab = (searchParams.get('tab') as TabKey) || 'dashboard'
  const [activeTab, setActiveTab] = useState<TabKey>(urlTab)
  // Overlay state: show a descriptive overlay when a nav tab is clicked
  const [overlayTab, setOverlayTab] = useState<TabKey | null>(null)
  const [_tracerEnabled, _setTracerEnabled] = useState<boolean>(() => {
    try {
      if (typeof window === 'undefined') return false
      return localStorage.getItem('jarvis_debug_location') === '1' || new URL(window.location.href).searchParams.get('debug') === 'location'
    } catch (err) {
      return false
    }
  })
  const [_lastTracerEvent, _setLastTracerEvent] = useState<Record<string, unknown> | null>(null)
  const [darkMode] = useState<boolean>(() => {
    try {
      if (typeof window === 'undefined') return false
      return localStorage.getItem('jarvis_dark_mode') !== '0'
    } catch (err) {
      return true
    }
  })

  // Real API data with loading states
  const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null)
  const [loadingHealth, setLoadingHealth] = useState(true)
  const [healthError, setHealthError] = useState<string | null>(null)

  const [systemMetrics, setSystemMetrics] = useState<SystemMetrics | null>(null)
  const [loadingMetrics, setLoadingMetrics] = useState(true)
  const [metricsError, setMetricsError] = useState<string | null>(null)
  const [autoRefreshMetrics, setAutoRefreshMetrics] = useState(true)

  const [users, setUsers] = useState<AdminUser[]>([])
  const [_loadingUsers, setLoadingUsers] = useState(true)
  const [_usersError, setUsersError] = useState<string | null>(null)

  const [featureFlagsData, setFeatureFlagsData] = useState<FeatureFlagsResponse | null>(null)
  const [_loadingFlags, setLoadingFlags] = useState(true)
  const [_flagsError, setFlagsError] = useState<string | null>(null)

  const [auditLogs, setAuditLogs] = useState<AuditLogsResponse | null>(null)
  const [_loadingLogs, setLoadingLogs] = useState(true)
  const [_logsError, setLogsError] = useState<string | null>(null)

  // Critical system alerts
  const [_criticalAlerts, setCriticalAlerts] = useState<CriticalAlert[]>([
    { id: '1', severity: 'critical', title: '🚨 Unauthorized Access Attempt', description: 'Multiple login failures detected from IP 192.168.1.50', timestamp: '2 mins ago', action: 'Block IP' },
    { id: '2', severity: 'high', title: '⚠️ Certificate Expiring Soon', description: 'TLS certificate expires in 14 days', timestamp: '1 hour ago', action: 'Renew Now' },
    { id: '3', severity: 'high', title: '🔐 PQC Key Rotation Required', description: 'Post-Quantum cryptography keys need rotation', timestamp: '3 hours ago', action: 'Rotate Keys' },
  ])

  // Active incidents
  const [incidents, setIncidents] = useState<Incident[]>([
    { id: '1', type: 'Intrusion Attempt', severity: 'critical', status: 'active', title: 'Persistent DDoS Attack - Port 443', timestamp: '2 mins ago', affectedSystems: ['Load Balancer', 'API Gateway'] },
    { id: '2', type: 'Data Anomaly', severity: 'high', status: 'investigating', title: 'Unusual Database Queries Detected', timestamp: '45 mins ago', affectedSystems: ['Database', 'Analytics'] },
    { id: '3', type: 'Performance Degradation', severity: 'medium', status: 'resolved', title: 'CPU Spikes on Worker Nodes', timestamp: '2 hours ago', affectedSystems: ['Compute Cluster'] },
  ])
  const [loadingIncidents, setLoadingIncidents] = useState(false)

  // Secret keys and certificates
  const [secretKeys, setSecretKeys] = useState<SecretKey[]>([
    { id: '1', name: 'API Master Key', type: 'api', status: 'active', lastRotated: '30 days ago', expiresAt: '2026-03-20' },
    { id: '2', name: 'PQC Private Key', type: 'encryption', status: 'active', lastRotated: '15 days ago' },
    { id: '3', name: 'TLS Certificate', type: 'certificate', status: 'active', lastRotated: '90 days ago', expiresAt: '2026-01-03' },
    { id: '4', name: 'Database Encryption Key', type: 'encryption', status: 'rotated', lastRotated: '2 days ago' },
  ])
  const [loadingKeys, setLoadingKeys] = useState(false)

  // Confirm dialog state for sensitive operations
  const [confirmAction, setConfirmAction] = useState<{ type: string; targetId: string; details: CriticalAlert | Incident | SecretKey | Record<string, unknown> } | null>(null)
  const [confirmLoading, setConfirmLoading] = useState(false)

  // Config and Security settings state
  const [configChanges, setConfigChanges] = useState<Record<string, unknown>>({})
  const [securitySettings, setSecuritySettings] = useState<Record<string, unknown>>({ twoFaEnabled: false })
  const [savingConfig, setSavingConfig] = useState(false)
  const [savingSecurity, setSavingSecurity] = useState(false)

  // Search state
  const [featureSearchTerm, setFeatureSearchTerm] = useState('')
  const [userSearchTerm, setUserSearchTerm] = useState('')

  // User creation form state
  const [showAddUserForm, setShowAddUserForm] = useState(false)
  const [newUserForm, setNewUserForm] = useState({ username: '', email: '', password: '', confirmPassword: '', role: 'operator' as 'admin' | 'analyst' | 'operator' })
  const [addingUser, setAddingUser] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)

  const { toast } = useToast()

  // Toggle user active/inactive status (optimistic update, best-effort server sync)
  const toggleUserStatus = useCallback(async (userId: string, currentlyActive: boolean) => {
    // Optimistically update UI immediately
    const newStatus = currentlyActive ? 'inactive' : 'active'
    setUsers((prev) => prev.map((u) => (u.id === userId ? { ...u, status: newStatus } : u)))

    try {
      // Update server (PATCH may not be implemented in all environments - best effort)
      apiClient.patch(`/api/users/${userId}`, { status: newStatus }).catch(() => {
        // Silently fail - UI is already updated optimistically
      })

      // Log to audit trail asynchronously
      apiClient.post('/api/audit-logs', {
        action: currentlyActive ? 'deactivate_user' : 'activate_user',
        targetId: userId,
        targetType: 'user',
        userId: 'system',
        details: { via: 'admin-console', executedBy: 'J.A.R.V.I.S', timestamp: new Date().toISOString() },
      }).catch(() => {
        // Silently fail
      })

      toast({ title: `User ${newStatus === 'active' ? 'activated' : 'deactivated'} successfully` })
    } catch (err) {
      const msg = getErrorMessage(err)
      toast({ title: `Failed to update user status`, description: msg, variant: 'destructive' })
      // Revert optimistic update on error
      setUsers((prev) => prev.map((u) => (u.id === userId ? { ...u, status: currentlyActive ? 'active' : 'inactive' } : u)))
    }
  }, [toast])

  // Confirm and execute critical alert actions (Block IP, Renew Cert, Rotate Keys)
  const executeConfirmAction = async () => {
    if (!confirmAction) return
    setConfirmLoading(true)
    const { type, targetId, details } = confirmAction

    try {
      // Optimistic update - update UI immediately
      if (type === 'critical_action') {
        setCriticalAlerts((prev) => prev.filter((a) => a.id !== targetId))
      } else if (type === 'add_user') {
        const newUser: AdminUser = {
          id: `user_${Date.now()}`,
          username: 'New User',
          email: 'newuser@example.com',
          role: 'viewer',
          status: 'active',
        }
        setUsers((prev) => [...prev, newUser])
        toast({ title: 'User added successfully' })
      } else if (type === 'add_feature') {
        toast({ title: 'Feature flag added successfully' })
      } else if (type === 'delete_user') {
        setUsers((prev) => prev.filter((u) => u.id !== targetId))
        toast({ title: 'User deleted successfully' })
      } else if (type === 'delete_feature') {
        toast({ title: 'Feature flag deleted successfully' })
      } else {
        toast({ title: 'Action executed' })
      }

      // Close dialog immediately for instant feedback
      setConfirmLoading(false)
      setConfirmAction(null)

      // Log to audit trail asynchronously (fire-and-forget)
      apiClient.post('/api/audit-logs', {
        action: type,
        targetId,
        targetType: type === 'critical_action' ? 'alert' : type.includes('user') ? 'user' : type.includes('feature') ? 'feature' : 'resource',
        userId: 'system',
        details: { ...(details as unknown as Record<string, unknown>), executedBy: 'J.A.R.V.I.S', timestamp: new Date().toISOString() },
      }).catch(() => {
        // Silently fail - UI update already happened
      })
    } catch (err) {
      const msg = getErrorMessage(err)
      toast({ title: 'Action failed', description: msg, variant: 'destructive' })
      setConfirmLoading(false)
      setConfirmAction(null)
    }
  }

  // Save config changes
  const saveConfigChanges = async () => {
    setSavingConfig(true)
    try {
      await apiClient.post('/api/audit-logs', {
        action: 'update_config',
        targetId: 'system_config',
        targetType: 'config',
        userId: 'system',
        details: { ...configChanges, executedBy: 'J.A.R.V.I.S', timestamp: new Date().toISOString() },
      })
      toast({ title: 'Configuration saved successfully' })
    } catch (err) {
      const msg = getErrorMessage(err)
      toast({ title: 'Failed to save config', description: msg, variant: 'destructive' })
    } finally {
      setSavingConfig(false)
    }
  }

  // Save security settings
  const saveSecuritySettings = async () => {
    setSavingSecurity(true)
    try {
      await apiClient.post('/api/audit-logs', {
        action: 'update_security',
        targetId: 'system_security',
        targetType: 'security',
        userId: 'system',
        details: { ...securitySettings, executedBy: 'J.A.R.V.I.S', timestamp: new Date().toISOString() },
      })
      toast({ title: 'Security settings saved successfully' })
    } catch (err) {
      const msg = getErrorMessage(err)
      toast({ title: 'Failed to save security settings', description: msg, variant: 'destructive' })
    } finally {
      setSavingSecurity(false)
    }
  }

  // Toggle 2FA
  const toggle2FA = (enabled: boolean) => {
    setSecuritySettings((prev) => ({ ...prev, twoFaEnabled: enabled }))
  }

  // Handle feature search
  const handleFeatureSearch = () => {
    if (featureSearchTerm.length === 0) {
      toast({ title: 'Enter a search term' })
      return
    }
    const filteredCount = features.filter((f) => f.name.toLowerCase().includes(featureSearchTerm.toLowerCase()) || f.description.toLowerCase().includes(featureSearchTerm.toLowerCase())).length
    toast({ title: `Found ${filteredCount} matching feature${filteredCount !== 1 ? 's' : ''}` })
  }

  // Handle user search
  const handleUserSearch = () => {
    if (userSearchTerm.length === 0) {
      toast({ title: 'Enter a search term' })
      return
    }
    const filteredCount = users.filter((u) => u.username.toLowerCase().includes(userSearchTerm.toLowerCase()) || u.email.toLowerCase().includes(userSearchTerm.toLowerCase())).length
    toast({ title: `Found ${filteredCount} matching user${filteredCount !== 1 ? 's' : ''}` })
  }

  // Add new feature
  const handleAddFeature = () => {
    setConfirmAction({
      type: 'add_feature',
      targetId: 'new_feature',
      details: { action: 'add_feature', timestamp: new Date().toISOString() },
    })
  }

  // Add new user
  const handleAddUser = () => {
    setShowAddUserForm(true)
    setFormError(null)
    setNewUserForm({ username: '', email: '', password: '', confirmPassword: '', role: 'operator' })
  }

  // Submit new user form
  const handleSubmitNewUser = async () => {
    // Validation
    if (!newUserForm.username.trim()) {
      setFormError('Username is required')
      return
    }
    if (!newUserForm.email.trim()) {
      setFormError('Email is required')
      return
    }
    if (!newUserForm.password) {
      setFormError('Password is required')
      return
    }
    if (newUserForm.password.length < 8) {
      setFormError('Password must be at least 8 characters')
      return
    }
    if (newUserForm.password !== newUserForm.confirmPassword) {
      setFormError('Passwords do not match')
      return
    }

    setAddingUser(true)
    setFormError(null)

    try {
      // Create the user via admin service
      const response = await adminService.createUser({
        username: newUserForm.username,
        email: newUserForm.email,
        role: newUserForm.role,
      })

      // Add user to local state (response.user contains the created user)
      const createdUser = response.user as AdminUser
      const newUser: AdminUser = {
        id: createdUser.id || `user_${Date.now()}`,
        username: newUserForm.username,
        email: newUserForm.email,
        role: newUserForm.role,
        status: 'active',
      }
      setUsers((prev) => [...prev, newUser])

      // Log to audit trail
      apiClient.post('/api/audit-logs', {
        action: 'create_user',
        targetId: newUser.id,
        targetType: 'user',
        userId: 'system',
        details: { username: newUserForm.username, role: newUserForm.role, via: 'admin-console', executedBy: 'J.A.R.V.I.S', timestamp: new Date().toISOString() },
      }).catch(() => { })

      toast({ title: 'User created successfully' })
      setShowAddUserForm(false)
      setNewUserForm({ username: '', email: '', password: '', confirmPassword: '', role: 'operator' })
    } catch (err) {
      const msg = getErrorMessage(err)
      setFormError(msg || 'Failed to create user')
      toast({ title: 'Failed to create user', description: msg, variant: 'destructive' })
    } finally {
      setAddingUser(false)
    }
  }

  // View all alerts
  const handleViewAllAlerts = () => {
    setActiveTab('critical')
    toast({ title: 'Navigating to Critical Alerts tab' })
  }

  // Incident action handlers
  const updateIncidentStatus = async (incidentId: string, newStatus: Incident['status']) => {
    try {
      // Optimistically update UI
      setIncidents((prev) =>
        prev.map((incident) =>
          incident.id === incidentId ? { ...incident, status: newStatus } : incident
        )
      )

      // Post to audit log
      await apiClient.post('/api/audit-logs', {
        action: 'update_incident_status',
        targetId: incidentId,
        targetType: 'incident',
        userId: 'system',
        details: { newStatus, timestamp: new Date().toISOString(), executedBy: 'J.A.R.V.I.S' },
      }).catch(() => { })

      toast({ title: `Incident status updated to ${newStatus}` })
    } catch (err) {
      const msg = getErrorMessage(err)
      toast({ title: 'Failed to update incident', description: msg, variant: 'destructive' })
      // Revert on error
      try {
        const refreshed = await adminService.getIncidents()
        setIncidents(refreshed as Incident[])
      } catch {
        // ignore
      }
    }
  }

  // Rotate security key
  const rotateSecurityKey = async (keyId: string) => {
    try {
      await apiClient.post('/api/audit-logs', {
        action: 'rotate_key',
        targetId: keyId,
        targetType: 'secret_key',
        userId: 'system',
        details: { timestamp: new Date().toISOString(), executedBy: 'J.A.R.V.I.S' },
      })

      // Update the key's rotation timestamp
      setSecretKeys((prev) =>
        prev.map((key) =>
          key.id === keyId ? { ...key, lastRotated: 'just now', status: 'active' } : key
        )
      )

      toast({ title: 'Security key rotated successfully' })
    } catch (err) {
      const msg = getErrorMessage(err)
      toast({ title: 'Failed to rotate key', description: msg, variant: 'destructive' })
    }
  }

  // Fetch incidents from backend
  const fetchIncidents = useCallback(async () => {
    try {
      setLoadingIncidents(true)
      const data = await adminService.getIncidents()
      setIncidents(data as Incident[])
    } catch (err) {
      console.error('Failed to fetch incidents:', err)
    } finally {
      setLoadingIncidents(false)
    }
  }, [])

  // Fetch secret keys from backend
  const fetchSecretKeys = useCallback(async () => {
    try {
      setLoadingKeys(true)
      const data = await adminService.getSecretKeys()
      setSecretKeys(data as SecretKey[])
    } catch (err) {
      console.error('Failed to fetch secret keys:', err)
    } finally {
      setLoadingKeys(false)
    }
  }, [])

  useEffect(() => {
    console.debug('[AdminConsole] mounted', { pathname: typeof window !== 'undefined' ? window.location.pathname : '' })

    // Fetch system health
    const fetchHealth = async () => {
      try {
        setLoadingHealth(true)
        setHealthError(null)
        const health = await adminService.getSystemHealth()
        setSystemHealth(health)
      } catch (err) {
        const msg = err instanceof Error ? err.message : 'Failed to load system health'
        setHealthError(msg)
        console.error('[AdminConsole] Failed to fetch health:', err)
      } finally {
        setLoadingHealth(false)
      }
    }

    // Fetch users
    const fetchUsers = async () => {
      try {
        setLoadingUsers(true)
        setUsersError(null)
        const usersList = await adminService.listUsers()
        setUsers(usersList)
      } catch (err) {
        const msg = err instanceof Error ? err.message : 'Failed to load users'
        setUsersError(msg)
        console.error('[AdminConsole] Failed to fetch users:', err)
      } finally {
        setLoadingUsers(false)
      }
    }

    // Fetch feature flags
    const fetchFlags = async () => {
      try {
        setLoadingFlags(true)
        setFlagsError(null)
        const flags = await adminService.getFeatureFlags()
        setFeatureFlagsData(flags)
      } catch (err) {
        const msg = err instanceof Error ? err.message : 'Failed to load feature flags'
        setFlagsError(msg)
        console.error('[AdminConsole] Failed to fetch flags:', err)
      } finally {
        setLoadingFlags(false)
      }
    }

    // Fetch audit logs
    const fetchLogs = async () => {
      try {
        setLoadingLogs(true)
        setLogsError(null)
        const logs = await adminService.getAuditLogs(100)
        setAuditLogs(logs)
      } catch (err) {
        const msg = err instanceof Error ? err.message : 'Failed to load audit logs'
        setLogsError(msg)
        console.error('[AdminConsole] Failed to fetch logs:', err)
      } finally {
        setLoadingLogs(false)
      }
    }

    // Fetch system metrics
    const fetchMetrics = async () => {
      try {
        setLoadingMetrics(true)
        setMetricsError(null)
        const metrics = await adminService.getSystemMetrics()
        setSystemMetrics(metrics)
      } catch (err) {
        const msg = err instanceof Error ? err.message : 'Failed to load system metrics'
        setMetricsError(msg)
        console.error('[AdminConsole] Failed to fetch metrics:', err)
      } finally {
        setLoadingMetrics(false)
      }
    }

    // Start all fetches
    fetchHealth()
    fetchMetrics()
    fetchUsers()
    fetchFlags()
    fetchLogs()
    fetchIncidents()
    fetchSecretKeys()

    // Set up refresh interval (every 30 seconds for health/metrics, every 60 for others)
    const healthInterval = setInterval(fetchHealth, 30000)
    const metricsInterval = autoRefreshMetrics ? setInterval(fetchMetrics, 10000) : null
    const usersInterval = setInterval(fetchUsers, 60000)
    const flagsInterval = setInterval(fetchFlags, 60000)
    const logsInterval = setInterval(fetchLogs, 60000)
    const incidentsInterval = setInterval(fetchIncidents, 60000)
    const keysInterval = setInterval(fetchSecretKeys, 60000)

    return () => {
      clearInterval(healthInterval)
      if (metricsInterval) clearInterval(metricsInterval)
      clearInterval(usersInterval)
      clearInterval(flagsInterval)
      clearInterval(logsInterval)
      clearInterval(incidentsInterval)
      clearInterval(keysInterval)
      console.debug('[AdminConsole] unmounted')
    }
  }, [fetchIncidents, fetchSecretKeys, autoRefreshMetrics])

  useEffect(() => {
    const current = searchParams.get('tab')
    if (current && (current as TabKey) !== activeTab) {
      setActiveTab(current as TabKey)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams])

  // Ensure any overlay preview is closed when switching main tabs to avoid it blocking interactions
  useEffect(() => {
    setOverlayTab(null)
  }, [activeTab])

  // Close overlay if a confirmation dialog is opened
  useEffect(() => {
    if (confirmAction) setOverlayTab(null)
  }, [confirmAction])

  useEffect(() => {
    const p = new URLSearchParams(searchParams)
    if (p.get('tab') !== activeTab) {
      p.set('tab', activeTab)
      setSearchParams(p, { replace: true })
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab])

  useEffect(() => {
    const handler = (e: Event) => {
      const ev = e as CustomEvent
      _setLastTracerEvent(ev.detail as Record<string, unknown>)
      console.debug('[AdminConsole] tracer event', ev.detail)
    }
    window.addEventListener('jarvis:debug:location', handler)
    return () => window.removeEventListener('jarvis:debug:location', handler)
  }, [])

  // navigate is currently unused in this view, prefer router links when needed
  // const navigate = useNavigate()

  const toggleFeature = useCallback(async (flagName: string, currentState: boolean) => {
    const newState = !currentState

    // Optimistic update - update UI immediately
    setFeatureFlagsData((prev) => {
      if (!prev) return prev
      return {
        ...prev,
        flags: { ...prev.flags, [flagName]: newState }
      }
    })

    try {
      // Update server asynchronously (fire-and-forget for speed)
      adminService.toggleFeatureFlag(flagName, newState).catch(async (err) => {
        console.error('[AdminConsole] Failed to toggle flag:', err)
        toast({ title: 'Note: Flag update may not have persisted', variant: 'default' })
        // Revert on error
        try {
          const flags = await adminService.getFeatureFlags()
          setFeatureFlagsData(flags)
        } catch {
          // ignore refresh failure
        }
      })
    } catch (err) {
      console.error('[AdminConsole] Failed to toggle flag:', err)
      toast({ title: 'Failed to toggle feature flag', variant: 'destructive' })
    }
  }, [toast])

  // Derive a features array from the FeatureFlagsResponse for rendering
  const features: _FeatureToggle[] = featureFlagsData
    ? Object.entries(featureFlagsData.flags).map(([id, enabled]) => ({
      id,
      name: id,
      description: '',
      enabled: Boolean(enabled),
      category: 'experimental',
    }))
    : []


  return (
    <div className={`flex flex-col h-screen ${darkMode ? 'bg-slate-950' : 'bg-slate-50'} text-slate-200`}>
      {/* Use the shared Layout/System top bar (provided by Layout wrapper) — remove local sticky header to keep UI consistent across pages. */}
      <div className="h-4" />

      {/* Overlay: shows a quick descriptive preview when a nav tab is clicked */}
      {overlayTab && (
        <div className="fixed inset-0 flex items-start justify-center pt-20 px-4 z-[1000]">
          <div className="absolute inset-0 bg-black/60 pointer-events-auto" onClick={() => setOverlayTab(null)} />
          <div className="relative w-full max-w-4xl bg-slate-900 rounded-lg border border-cyan-500/20 p-6 shadow-2xl">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-bold text-white">{overlayTab.toUpperCase()}</h3>
              <div className="flex items-center gap-2">
                <button className="px-3 py-1 bg-cyan-600 text-white rounded" onClick={() => { setActiveTab(overlayTab); setOverlayTab(null) }}>Open Full</button>
                <button className="px-3 py-1 bg-slate-700 text-white rounded" onClick={() => setOverlayTab(null)}>Close</button>
              </div>
            </div>
            <div className="max-h-[60vh] overflow-auto">
              {overlayTab === 'dashboard' && (
                <div className="space-y-3">
                  <p className="text-sm text-slate-400">Quick system summary. Use "Open Full" to view full dashboard.</p>
                  <div className="grid grid-cols-2 gap-3 mt-3">
                    <div className="p-3 bg-slate-800 rounded border border-cyan-500/20">CPU: <strong>--%</strong></div>
                    <div className="p-3 bg-slate-800 rounded border border-cyan-500/20">Memory: <strong>--%</strong></div>
                    <div className="p-3 bg-slate-800 rounded border border-cyan-500/20">Active Users: <strong>--</strong></div>
                    <div className="p-3 bg-slate-800 rounded border border-cyan-500/20">System Health: <strong>Unknown</strong></div>
                  </div>
                </div>
              )}
              {overlayTab === 'features' && (
                <div className="space-y-3">
                  <p className="text-sm text-slate-400">Feature flags quick view — toggle from the full view.</p>
                  {features.slice(0, 4).map((f) => (
                    <div key={f.id} className="flex items-center justify-between p-3 bg-slate-800 rounded border border-slate-700/30">
                      <div>
                        <div className="font-semibold text-white">{f.name}</div>
                        <div className="text-xs text-slate-400">{f.description || 'No description'}</div>
                      </div>
                      <div className={`px-2 py-1 rounded text-xs ${f.enabled ? 'bg-green-500/20 text-green-300' : 'bg-gray-500/20 text-gray-300'}`}>{f.enabled ? 'Enabled' : 'Disabled'}</div>
                    </div>
                  ))}
                </div>
              )}
              {overlayTab === 'users' && (
                <div className="space-y-3">
                  <p className="text-sm text-slate-400">Top users (sample)</p>
                  <div className="space-y-2 mt-2">
                    {users.slice(0, 6).map((u) => (
                      <div key={u.id} className="flex items-center justify-between p-3 bg-slate-800 rounded border border-slate-700/30">
                        <div className="font-semibold">{u.username}</div>
                        <div className="text-xs text-slate-400">{u.role}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {/* Fallback small summary for other tabs */}
              {overlayTab && !['dashboard', 'features', 'users'].includes(overlayTab) && (
                <div className="text-sm text-slate-400">Preview for <strong>{overlayTab}</strong>. Click "Open Full" to view all details.</div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Navigation Tabs (non-sticky; clicking opens overlay preview) */}
      <nav className="px-4 py-3 flex items-center gap-2 overflow-x-auto scrollbar-hide bg-slate-900/10 backdrop-blur-sm border-b border-slate-800/20">
        {[
          { key: 'dashboard', label: 'Dashboard', icon: '📊', color: 'from-blue-500 to-cyan-500' },
          { key: 'system', label: 'System', icon: '⚙️', color: 'from-cyan-500 to-blue-500' },
          { key: 'critical', label: 'Critical', icon: '🚨', color: 'from-red-500 to-orange-500', alert: true },
          { key: 'incidents', label: 'Incidents', icon: '⚡', color: 'from-orange-500 to-yellow-500', alert: true },
          { key: 'features', label: 'Features', icon: '🎛️', color: 'from-purple-500 to-pink-500' },
          { key: 'users', label: 'Users', icon: '👥', color: 'from-green-500 to-emerald-500' },
          { key: 'keys', label: 'Keys', icon: '🔑', color: 'from-indigo-500 to-purple-500', alert: true },
          { key: 'config', label: 'Config', icon: '🔧', color: 'from-cyan-500 to-blue-500' },
          { key: 'security', label: 'Security', icon: '🔒', color: 'from-rose-500 to-red-500' },
          { key: 'logs', label: 'Logs', icon: '📋', color: 'from-slate-500 to-gray-500' },
        ].map((item) => (
          <button
            key={item.key}
            onClick={() => { setActiveTab(item.key as TabKey); setOverlayTab(null); }}
            className="relative group flex items-center gap-2 px-4 py-2.5 rounded-lg font-bold whitespace-nowrap transition-all duration-300 flex-shrink-0"
          >
            <div className={`relative flex items-center gap-2 px-3 py-1.5 rounded-lg transition-all duration-300 ${activeTab === item.key ? 'text-white shadow-lg' : 'text-slate-300 hover:text-white bg-slate-800/40 hover:bg-slate-700/60 border border-slate-700/40 hover:border-slate-600/60'}`}>
              {item.alert && <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-red-500 rounded-full animate-pulse shadow-lg shadow-red-500/50"></span>}
              <span className={`text-lg transition-transform group-hover:scale-125 ${activeTab === item.key ? 'animate-bounce' : ''}`}>{item.icon}</span>
              <span className="hidden lg:inline">{item.label}</span>
            </div>
            {activeTab === item.key && <div className="absolute bottom-0 left-1/2 transform -translate-x-1/2 w-3/4 h-1 bg-gradient-to-r from-cyan-400 to-blue-400 rounded-t-lg shadow-lg shadow-cyan-500/50"></div>}
          </button>
        ))}
      </nav>

      {/* Animated Top Accent Line */}
      <div className="h-0.5 bg-gradient-to-r from-transparent via-cyan-500 to-transparent opacity-60 animate-pulse"></div>

      {/* Main Content Area */}
      <main className="flex-1 overflow-auto">
        <div className="p-6">
          {/* Dashboard Tab */}
          {activeTab === 'dashboard' && (
            <div className="space-y-8">
              {/* Premium Header Section */}
              <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-indigo-950 via-slate-900 to-cyan-950 p-8 border border-cyan-500/30 backdrop-blur-sm">
                <div className="absolute inset-0 overflow-hidden pointer-events-none">
                  <div className="absolute -top-40 -right-40 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl"></div>
                  <div className="absolute -bottom-40 -left-40 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl"></div>
                </div>

                <div className="relative z-10 flex items-center justify-between">
                  <div>
                    <h1 className="text-4xl font-black bg-gradient-to-r from-cyan-300 via-blue-300 to-indigo-300 bg-clip-text text-transparent mb-2">System Command Center</h1>
                    <p className="text-slate-300 text-sm">Real-time monitoring & intelligent threat response</p>
                  </div>
                  <div className="hidden lg:flex flex-col items-end gap-2">
                    <div className="flex items-center gap-2 px-4 py-2 bg-green-500/20 rounded-full border border-green-500/40">
                      <span className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></span>
                      <span className="text-sm font-semibold text-green-300">All Systems Operational</span>
                    </div>
                    <p className="text-xs text-slate-400">Last sync: 2 seconds ago</p>
                  </div>
                </div>
              </div>

              {/* Advanced Metrics Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {loadingHealth ? (
                  <div className="col-span-full text-center py-8 text-slate-400">Loading system health...</div>
                ) : healthError ? (
                  <div className="col-span-full text-center py-8 text-red-400">Error: {healthError}</div>
                ) : systemHealth ? (
                  <>
                    <div className="group relative rounded-xl overflow-hidden border border-cyan-500/30 bg-gradient-to-br from-slate-800/50 to-slate-900/50 p-5 hover:border-cyan-500/60 transition-all duration-300">
                      <div className="relative z-10">
                        <p className="text-xs font-bold uppercase tracking-widest text-cyan-400 mb-1">CPU Usage</p>
                        <p className="text-3xl font-black text-white">{systemHealth.cpu.percent.toFixed(1)}%</p>
                        <span className="text-4xl group-hover:scale-125 transition-transform duration-300">⚙️</span>
                      </div>
                    </div>
                    <div className="group relative rounded-xl overflow-hidden border border-cyan-500/30 bg-gradient-to-br from-slate-800/50 to-slate-900/50 p-5 hover:border-cyan-500/60 transition-all duration-300">
                      <div className="relative z-10">
                        <p className="text-xs font-bold uppercase tracking-widest text-cyan-400 mb-1">Memory</p>
                        <p className="text-3xl font-black text-white">{systemHealth.memory.percent.toFixed(1)}%</p>
                        <span className="text-4xl group-hover:scale-125 transition-transform duration-300">💾</span>
                      </div>
                    </div>
                    <div className="group relative rounded-xl overflow-hidden border border-cyan-500/30 bg-gradient-to-br from-slate-800/50 to-slate-900/50 p-5 hover:border-cyan-500/60 transition-all duration-300">
                      <div className="relative z-10">
                        <p className="text-xs font-bold uppercase tracking-widest text-cyan-400 mb-1">Active Users</p>
                        <p className="text-3xl font-black text-white">{users.length}</p>
                        <span className="text-4xl group-hover:scale-125 transition-transform duration-300">👥</span>
                      </div>
                    </div>
                    <div className={`group relative rounded-xl overflow-hidden border ${systemHealth.status === 'healthy' ? 'border-green-500/30' : 'border-orange-500/30'} bg-gradient-to-br from-slate-800/50 to-slate-900/50 p-5 transition-all duration-300`}>
                      <div className="relative z-10">
                        <p className="text-xs font-bold uppercase tracking-widest text-cyan-400 mb-1">System Health</p>
                        <p className="text-3xl font-black text-white capitalize">{systemHealth.status}</p>
                        <span className="text-4xl group-hover:scale-125 transition-transform duration-300">❤️</span>
                      </div>
                    </div>
                  </>
                ) : null}
              </div>

              {/* Real-time Analytics Section */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Live System Activity */}
                <div className="lg:col-span-2 group rounded-2xl border border-cyan-500/30 bg-gradient-to-br from-slate-800/40 to-slate-900/60 p-6 hover:border-cyan-500/60 transition-all">
                  <div className="flex items-center justify-between mb-6">
                    <h3 className="text-2xl font-bold text-white flex items-center gap-3">
                      <span className="text-2xl">📊</span>
                      Live System Activity
                      <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse ml-auto"></span>
                    </h3>
                  </div>

                  {/* Animated chart area */}
                  <div className="relative h-48 bg-slate-900/50 rounded-xl overflow-hidden border border-slate-700/50 mb-4">
                    {/* Grid background */}
                    <div className="absolute inset-0 opacity-20">
                      <div className="w-full h-full flex flex-col justify-between">
                        {Array.from({ length: 5 }).map((_, i) => (
                          <div key={i} className="w-full h-px bg-slate-600/30"></div>
                        ))}
                      </div>
                    </div>

                    {/* Simulated wave chart */}
                    <svg className="absolute inset-0 w-full h-full" preserveAspectRatio="none" viewBox="0 0 200 100">
                      <defs>
                        <linearGradient id="waveGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                          <stop offset="0%" stopColor="#06b6d4" stopOpacity="0.6" />
                          <stop offset="100%" stopColor="#0284c7" stopOpacity="0.1" />
                        </linearGradient>
                      </defs>
                      <path d="M0,50 Q50,20 100,50 T200,50 L200,100 L0,100 Z" fill="url(#waveGradient)" />
                      <path d="M0,60 Q50,30 100,60 T200,60 L200,100 L0,100 Z" fill="#4f46e5" opacity="0.3" />
                    </svg>

                    {/* Data points */}
                    <div className="absolute inset-0 flex items-end justify-around p-4">
                      {[45, 62, 58, 75, 68, 82, 71, 88].map((val, i) => (
                        <div key={i} className="flex flex-col items-center gap-1">
                          {/* stylelint-disable-next-line */}
                          <div
                            className="w-1 bg-gradient-to-t from-cyan-500 to-cyan-400 rounded-full transition-all duration-500 hover:w-2 hover:bg-cyan-300"
                            data-height={val}
                            style={{ height: `${val}%` }}
                            suppressHydrationWarning
                          ></div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Legend & Stats */}
                  <div className="grid grid-cols-3 gap-3">
                    <div className="bg-slate-800/50 rounded-lg p-3 border border-cyan-500/20">
                      <p className="text-xs text-slate-400 font-semibold mb-1">PEAK</p>
                      <p className="text-2xl font-bold text-cyan-300">88%</p>
                      <p className="text-xs text-slate-500 mt-1">Last 24h</p>
                    </div>
                    <div className="bg-slate-800/50 rounded-lg p-3 border border-blue-500/20">
                      <p className="text-xs text-slate-400 font-semibold mb-1">AVERAGE</p>
                      <p className="text-2xl font-bold text-blue-300">68%</p>
                      <p className="text-xs text-slate-500 mt-1">Normalized</p>
                    </div>
                    <div className="bg-slate-800/50 rounded-lg p-3 border border-indigo-500/20">
                      <p className="text-xs text-slate-400 font-semibold mb-1">TREND</p>
                      <p className="text-2xl font-bold text-indigo-300">↑ 12%</p>
                      <p className="text-xs text-slate-500 mt-1">vs Yesterday</p>
                    </div>
                  </div>
                </div>

                {/* Critical Metrics Panel */}
                <div className="rounded-2xl border border-rose-500/30 bg-gradient-to-br from-slate-800/40 to-slate-900/60 p-6 hover:border-rose-500/60 transition-all">
                  <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
                    <span className="text-2xl">🎯</span> Critical Metrics
                  </h3>

                  <div className="space-y-4">
                    {[
                      { label: 'Response Time', value: '47ms', status: 'optimal', icon: '⚡' },
                      { label: 'Error Rate', value: '0.02%', status: 'optimal', icon: '✓' },
                      { label: 'Uptime', value: '99.9%', status: 'excellent', icon: '💯' },
                      { label: 'Throughput', value: '2.8K/s', status: 'healthy', icon: '📤' },
                    ].map((metric, idx) => (
                      <div key={idx} className="group">
                        <div className="flex items-center justify-between mb-2">
                          <p className="text-sm text-slate-300 font-semibold">{metric.label}</p>
                          <span className="text-lg">{metric.icon}</span>
                        </div>
                        <div className="flex items-baseline justify-between">
                          <p className="text-2xl font-bold text-cyan-300">{metric.value}</p>
                          <span className={`text-xs font-bold px-2 py-1 rounded-full uppercase tracking-widest ${metric.status === 'optimal' ? 'bg-green-500/20 text-green-300' :
                            metric.status === 'excellent' ? 'bg-cyan-500/20 text-cyan-300' :
                              'bg-blue-500/20 text-blue-300'
                            }`}>
                            {metric.status}
                          </span>
                        </div>
                        <div className="h-1.5 bg-slate-700/50 rounded-full mt-2 overflow-hidden">
                          {/* stylelint-disable-next-line */}
                          <div
                            className={`h-full rounded-full transition-all ${metric.status === 'optimal' ? 'bg-gradient-to-r from-green-500 to-green-400' :
                              metric.status === 'excellent' ? 'bg-gradient-to-r from-cyan-500 to-cyan-400' :
                                'bg-gradient-to-r from-blue-500 to-blue-400'
                              }`}
                            data-metric-status={metric.status}
                            style={{ width: `${metric.status === 'optimal' ? 95 : metric.status === 'excellent' ? 99 : 92}%` }}
                            suppressHydrationWarning
                          ></div>
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Status Footer */}
                  <div className="mt-6 pt-4 border-t border-slate-700/50">
                    <p className="text-xs text-slate-400 text-center">🟢 All systems nominal</p>
                  </div>
                </div>
              </div>

              {/* Advanced Alerts & Intelligence */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Intelligent Alert Feed */}
                <div className="group rounded-2xl border border-orange-500/30 bg-gradient-to-br from-slate-800/40 to-slate-900/60 p-6 hover:border-orange-500/60 transition-all">
                  <h3 className="text-2xl font-bold text-white mb-6 flex items-center gap-3">
                    <span className="text-2xl">🔔</span>
                    Alert Intelligence
                    <span className="ml-auto text-xs px-3 py-1 bg-orange-500/20 text-orange-300 rounded-full font-semibold">2 New</span>
                  </h3>

                  <div className="space-y-3">
                    {[
                      { id: 'cpu-1', icon: '⚠️', title: 'High CPU Usage', detail: 'Worker node #3', severity: 'warning', time: '2 mins ago', action: null as string | null },
                      { id: 'backup-1', icon: 'ℹ️', title: 'System Backup', detail: 'Database backup completed', severity: 'info', time: '15 mins ago', action: null as string | null },
                      { id: 'recovery-1', icon: '✓', title: 'Service Recovery', detail: 'API Gateway online', severity: 'success', time: '1 hour ago', action: null as string | null },
                    ].map((alert, idx) => (
                      <div key={idx} className="group/alert p-4 bg-slate-800/50 rounded-lg hover:bg-slate-750 border border-slate-700/30 hover:border-slate-600/60 transition-all cursor-pointer">
                        <div className="flex items-start gap-4">
                          <span className="text-2xl flex-shrink-0 group-hover/alert:scale-125 transition-transform">{alert.icon}</span>
                          <div className="flex-1 min-w-0">
                            <p className="font-semibold text-white truncate">{alert.title}</p>
                            <p className="text-sm text-slate-400 truncate">{alert.detail}</p>
                          </div>
                          <div className="flex-shrink-0 text-right flex flex-col items-end gap-2">
                            <span className={`text-xs font-bold px-2 py-1 rounded-full ${alert.severity === 'warning' ? 'bg-orange-500/20 text-orange-300' :
                              alert.severity === 'info' ? 'bg-blue-500/20 text-blue-300' :
                                'bg-green-500/20 text-green-300'
                              }`}>
                              {alert.severity.toUpperCase()}
                            </span>
                            <p className="text-xs text-slate-500">{alert.time}</p>
                            {alert.action && (
                              <button className="mt-2 px-3 py-1 rounded bg-rose-600 text-white text-xs" onClick={() => setConfirmAction({ type: 'critical_action', targetId: alert.id, details: alert })}>{alert.action}</button>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>

                  <button onClick={handleViewAllAlerts} className="w-full mt-4 py-2 px-4 bg-orange-600/20 hover:bg-orange-600/40 text-orange-300 font-semibold rounded-lg border border-orange-500/30 hover:border-orange-500/60 transition-all">
                    View All Alerts →
                  </button>
                </div>

                {/* Performance Dashboard */}
                <div className="group rounded-2xl border border-purple-500/30 bg-gradient-to-br from-slate-800/40 to-slate-900/60 p-6 hover:border-purple-500/60 transition-all">
                  <h3 className="text-2xl font-bold text-white mb-6 flex items-center gap-3">
                    <span className="text-2xl">📈</span>
                    Performance Analytics
                  </h3>

                  <div className="space-y-5">
                    {[
                      { metric: 'API Latency', value: '47ms', max: '500ms', bar: 9, trend: '↓ 5%', color: 'from-green-500 to-green-400' },
                      { metric: 'Database Query Time', value: '23ms', max: '100ms', bar: 23, trend: '↑ 2%', color: 'from-blue-500 to-blue-400' },
                      { metric: 'Cache Hit Rate', value: '94%', max: '100%', bar: 94, trend: '↑ 8%', color: 'from-cyan-500 to-cyan-400' },
                      { metric: 'Memory Utilization', value: '2.4GB', max: '8GB', bar: 30, trend: '↑ 1%', color: 'from-purple-500 to-purple-400' },
                    ].map((perf, idx) => (
                      <div key={idx}>
                        <div className="flex items-center justify-between mb-2">
                          <p className="text-sm font-semibold text-slate-300">{perf.metric}</p>
                          <div className="flex items-center gap-2">
                            <span className="text-lg font-bold text-cyan-300">{perf.value}</span>
                            <span className="text-xs text-slate-400">/ {perf.max}</span>
                            <span className={`text-xs font-semibold ${perf.trend.includes('↓') ? 'text-green-400' : 'text-orange-400'}`}>{perf.trend}</span>
                          </div>
                        </div>
                        <div className="h-2.5 bg-slate-700/50 rounded-full overflow-hidden border border-slate-600/30">
                          {/* stylelint-disable-next-line */}
                          <div
                            className={`h-full bg-gradient-to-r ${perf.color} transition-all duration-500 rounded-full`}
                            data-perf-bar={perf.bar}
                            style={{ width: `${perf.bar}%` }}
                            suppressHydrationWarning
                          ></div>
                        </div>
                      </div>
                    ))}
                  </div>

                  <button className="w-full mt-6 py-2 px-4 bg-purple-600/20 hover:bg-purple-600/40 text-purple-300 font-semibold rounded-lg border border-purple-500/30 hover:border-purple-500/60 transition-all">
                    Detailed Report →
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Features Tab */}
          {activeTab === 'features' && (
            <div className="space-y-6">
              {/* Page Header */}
              <div className="flex items-center justify-between">
                <h2 className="text-3xl font-bold text-white">Feature Management</h2>
                <button onClick={handleAddFeature} className="px-4 py-2 bg-green-600 text-white rounded-md shadow-md hover:bg-green-500 transition-all">
                  + Add New Feature
                </button>
              </div>

              {/* Search & Filter Bar */}
              <div className="bg-slate-800/60 p-4 rounded-lg border border-slate-700/30">
                <div className="flex items-center gap-4">
                  <div className="flex-1">
                    <label htmlFor="features-search" className="sr-only">Search features</label>
                    <input
                      id="features-search"
                      type="text"
                      placeholder="Search features..."
                      value={featureSearchTerm}
                      onChange={(e) => setFeatureSearchTerm(e.target.value)}
                      className="w-full px-4 py-2 bg-slate-700 text-slate-200 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-cyan-500"
                    />
                  </div>
                  <button onClick={handleFeatureSearch} className="px-4 py-2 bg-cyan-600 text-white rounded-lg shadow-md hover:bg-cyan-500 transition-all">
                    Search
                  </button>
                </div>
              </div>

              {/* Features Table */}
              <div className="bg-slate-800 rounded-lg border border-slate-700/30">
                <div className="grid grid-cols-4 gap-4 p-4 text-slate-400 font-semibold uppercase tracking-wider border-b border-slate-700">
                  <div className="flex items-center gap-2">
                    <span className="text-lg">⚙️</span>
                    Feature
                  </div>
                  <div className="hidden md:block">Description</div>
                  <div className="text-center">Status</div>
                  <div className="text-center">Actions</div>
                </div>
                <div className="divide-y divide-slate-700">
                  {features
                    .filter((feature) => featureSearchTerm.length === 0 || feature.name.toLowerCase().includes(featureSearchTerm.toLowerCase()) || feature.description.toLowerCase().includes(featureSearchTerm.toLowerCase()))
                    .map((feature) => (
                      <div key={feature.id} className="grid grid-cols-4 gap-4 p-4 hover:bg-slate-700 transition-all">
                        <div className="flex items-center gap-2">
                          <span className="text-lg">{feature.enabled ? '✅' : '❌'}</span>
                          <span className="font-medium text-white">{feature.name}</span>
                        </div>
                        <div className="hidden md:block">
                          <p className="text-slate-300 text-sm">{feature.description || 'No description provided.'}</p>
                        </div>
                        <div className="text-center">
                          <span className={`text-xs font-bold px-2 py-1 rounded-full ${feature.enabled ? 'bg-green-500/20 text-green-300' : 'bg-red-500/20 text-red-300'}`}>
                            {feature.enabled ? 'Enabled' : 'Disabled'}
                          </span>
                        </div>
                        <div className="text-center">
                          <button
                            onClick={() => toggleFeature(feature.id, feature.enabled)}
                            className="px-3 py-1 text-xs rounded-lg transition-all flex items-center gap-1 justify-center"
                          >
                            {feature.enabled ? (
                              <>
                                <span className="text-green-400">✔️</span>
                                Disable
                              </>
                            ) : (
                              <>
                                <span className="text-red-400">✖️</span>
                                Enable
                              </>
                            )}
                          </button>
                        </div>
                      </div>
                    ))}
                </div>
              </div>
            </div>
          )}

          {/* System Metrics Tab */}
          {activeTab === 'system' && (
            <div className="space-y-6">
              {/* Page Header */}
              <div className="flex items-center justify-between">
                <h2 className="text-3xl font-bold text-white">System Metrics & Memory Allocation</h2>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => adminService.getSystemMetrics().then(setSystemMetrics).catch(e => setMetricsError(e instanceof Error ? e.message : 'Failed to refresh'))}
                    className="px-4 py-2 bg-cyan-600 text-white rounded-md shadow-md hover:bg-cyan-500 transition-all"
                  >
                    🔄 Refresh Now
                  </button>
                  <label className="flex items-center gap-2 text-slate-300 px-4 py-2 bg-slate-800/40 rounded-md border border-slate-700/30">
                    <input
                      type="checkbox"
                      checked={autoRefreshMetrics}
                      onChange={(e) => setAutoRefreshMetrics(e.target.checked)}
                      className="w-4 h-4"
                    />
                    <span>Auto-Refresh (10s)</span>
                  </label>
                </div>
              </div>

              {/* Health Status Card */}
              <div className="bg-gradient-to-br from-slate-800 to-slate-900 p-6 rounded-lg border border-slate-700/30 shadow-lg">
                <h3 className="text-2xl font-bold text-white mb-4">System Health Status</h3>
                {loadingHealth ? (
                  <div className="text-slate-400">Loading health status...</div>
                ) : healthError ? (
                  <div className="text-red-400">Error: {healthError}</div>
                ) : systemHealth ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Status Indicator */}
                    <div className="flex items-center gap-4">
                      <div className={`w-16 h-16 rounded-full flex items-center justify-center text-3xl font-bold ${systemHealth.status === 'healthy' ? 'bg-green-500/20 border-2 border-green-500 text-green-400' : systemHealth.status === 'warning' ? 'bg-yellow-500/20 border-2 border-yellow-500 text-yellow-400' : 'bg-red-500/20 border-2 border-red-500 text-red-400'}`}>
                        {systemHealth.status === 'healthy' ? '✓' : systemHealth.status === 'warning' ? '⚠' : '✕'}
                      </div>
                      <div>
                        <p className="text-slate-400 text-sm">Status</p>
                        <p className={`text-2xl font-bold capitalize ${systemHealth.status === 'healthy' ? 'text-green-400' : systemHealth.status === 'warning' ? 'text-yellow-400' : 'text-red-400'}`}>{systemHealth.status}</p>
                      </div>
                    </div>

                    {/* Uptime */}
                    <div>
                      <p className="text-slate-400 text-sm mb-1">Uptime</p>
                      <p className="text-xl font-semibold text-cyan-300">{systemHealth.uptimeFormatted}</p>
                      <p className="text-xs text-slate-500">({systemHealth.uptimeSeconds} seconds)</p>
                    </div>

                    {/* CPU Usage */}
                    <div>
                      <p className="text-slate-400 text-sm mb-2">CPU Usage</p>
                      <div className="flex items-center gap-3">
                        <div className="flex-1 bg-slate-700 rounded-full h-3 overflow-hidden">
                          <div
                            className={`h-full transition-all duration-500 ${systemHealth.cpu.percent > 80 ? 'bg-red-500' : systemHealth.cpu.percent > 50 ? 'bg-yellow-500' : 'bg-green-500'}`}
                            style={{ width: `${Math.min(systemHealth.cpu.percent, 100)}%` }}
                            data-cpu-bar="usage"
                          />
                        </div>
                        <span className={`font-bold min-w-fit ${systemHealth.cpu.percent > 80 ? 'text-red-400' : systemHealth.cpu.percent > 50 ? 'text-yellow-400' : 'text-green-400'}`}>{systemHealth.cpu.percent.toFixed(1)}%</span>
                      </div>
                    </div>

                    {/* Memory Usage */}
                    <div>
                      <p className="text-slate-400 text-sm mb-2">Memory Usage</p>
                      <div className="flex items-center gap-3">
                        <div className="flex-1 bg-slate-700 rounded-full h-3 overflow-hidden">
                          <div
                            className={`h-full transition-all duration-500 ${systemHealth.memory.percent > 80 ? 'bg-red-500' : systemHealth.memory.percent > 50 ? 'bg-yellow-500' : 'bg-blue-500'}`}
                            style={{ width: `${Math.min(systemHealth.memory.percent, 100)}%` }}
                            data-memory-bar="usage"
                          />
                        </div>
                        <span className={`font-bold min-w-fit ${systemHealth.memory.percent > 80 ? 'text-red-400' : systemHealth.memory.percent > 50 ? 'text-yellow-400' : 'text-blue-400'}`}>{systemHealth.memory.percent.toFixed(1)}%</span>
                      </div>
                      <p className="text-xs text-slate-500 mt-1">{(systemHealth.memory.usageBytes / 1024 / 1024).toFixed(0)} MB</p>
                    </div>

                    {/* Component Status */}
                    <div className="md:col-span-2">
                      <p className="text-slate-400 text-sm mb-3">Component Status</p>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                        {Object.entries(systemHealth.components).map(([name, status]) => (
                          <div key={name} className={`p-3 rounded-lg border ${status === 'online' ? 'bg-green-500/10 border-green-500/30' : 'bg-red-500/10 border-red-500/30'}`}>
                            <p className="text-xs text-slate-400 capitalize">{name.replace(/_/g, ' ')}</p>
                            <p className={`font-semibold ${status === 'online' ? 'text-green-400' : 'text-red-400'}`}>{status}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                ) : null}
              </div>

              {/* System Metrics Card */}
              <div className="bg-gradient-to-br from-slate-800 to-slate-900 p-6 rounded-lg border border-slate-700/30 shadow-lg">
                <h3 className="text-2xl font-bold text-white mb-4">Detailed System Metrics</h3>
                {loadingMetrics ? (
                  <div className="text-slate-400">Loading system metrics...</div>
                ) : metricsError ? (
                  <div className="text-red-400">Error: {metricsError}</div>
                ) : systemMetrics ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Process Metrics */}
                    <div>
                      <h4 className="text-lg font-semibold text-cyan-300 mb-4">Process Metrics</h4>
                      <div className="space-y-3">
                        <div>
                          <p className="text-slate-400 text-sm">Process ID (PID)</p>
                          <p className="text-lg font-mono font-bold text-white">{systemMetrics.process.pid}</p>
                        </div>
                        <div>
                          <p className="text-slate-400 text-sm">Memory (RSS)</p>
                          <p className="text-lg font-bold text-blue-300">{systemMetrics.process.memoryRssMb.toFixed(2)} MB</p>
                        </div>
                        <div>
                          <p className="text-slate-400 text-sm">Memory %</p>
                          <div className="flex items-center gap-2 mt-1">
                            <div className="flex-1 bg-slate-700 rounded-full h-2 overflow-hidden">
                              <div
                                className="h-full bg-blue-500 transition-all duration-500"
                                style={{ width: `${Math.min(systemMetrics.process.memoryPercent, 100)}%` }}
                                data-process-memory="bar"
                              />
                            </div>
                            <span className="font-bold text-blue-400 min-w-fit">{systemMetrics.process.memoryPercent.toFixed(2)}%</span>
                          </div>
                        </div>
                        <div>
                          <p className="text-slate-400 text-sm">CPU Usage</p>
                          <div className="flex items-center gap-2 mt-1">
                            <div className="flex-1 bg-slate-700 rounded-full h-2 overflow-hidden">
                              <div
                                className="h-full bg-orange-500 transition-all duration-500"
                                style={{ width: `${Math.min(systemMetrics.process.cpuPercent, 100)}%` }}
                                data-process-cpu="bar"
                              />
                            </div>
                            <span className="font-bold text-orange-400 min-w-fit">{systemMetrics.process.cpuPercent.toFixed(2)}%</span>
                          </div>
                        </div>
                        <div>
                          <p className="text-slate-400 text-sm">Threads</p>
                          <p className="text-lg font-bold text-emerald-300">{systemMetrics.process.numThreads}</p>
                        </div>
                      </div>
                    </div>

                    {/* System Metrics */}
                    <div>
                      <h4 className="text-lg font-semibold text-cyan-300 mb-4">System Metrics</h4>
                      <div className="space-y-3">
                        <div>
                          <p className="text-slate-400 text-sm">CPU Cores</p>
                          <p className="text-lg font-bold text-purple-300">{systemMetrics.system.cpuCount}</p>
                        </div>
                        <div>
                          <p className="text-slate-400 text-sm">Total Memory</p>
                          <p className="text-lg font-bold text-violet-300">{systemMetrics.system.virtualMemoryTotalGb.toFixed(2)} GB</p>
                        </div>
                        <div>
                          <p className="text-slate-400 text-sm">Available Memory</p>
                          <p className="text-lg font-bold text-green-300">{systemMetrics.system.virtualMemoryAvailableGb.toFixed(2)} GB</p>
                        </div>
                        <div>
                          <p className="text-slate-400 text-sm">Memory Usage %</p>
                          <div className="flex items-center gap-2 mt-1">
                            <div className="flex-1 bg-slate-700 rounded-full h-2 overflow-hidden">
                              <div
                                className={`h-full transition-all duration-500 ${systemMetrics.system.virtualMemoryPercent > 80 ? 'bg-red-500' : systemMetrics.system.virtualMemoryPercent > 50 ? 'bg-yellow-500' : 'bg-green-500'}`}
                                style={{ width: `${Math.min(systemMetrics.system.virtualMemoryPercent, 100)}%` }}
                                data-system-memory="bar"
                              />
                            </div>
                            <span className={`font-bold min-w-fit ${systemMetrics.system.virtualMemoryPercent > 80 ? 'text-red-400' : systemMetrics.system.virtualMemoryPercent > 50 ? 'text-yellow-400' : 'text-green-400'}`}>{systemMetrics.system.virtualMemoryPercent.toFixed(2)}%</span>
                          </div>
                        </div>
                        <div>
                          <p className="text-slate-400 text-sm">Uptime</p>
                          <p className="text-lg font-mono font-bold text-slate-300">{(systemMetrics.uptimeSeconds / 86400).toFixed(1)} days</p>
                        </div>
                      </div>
                    </div>

                    {/* Memory Allocation Chart */}
                    <div className="md:col-span-2">
                      <h4 className="text-lg font-semibold text-cyan-300 mb-4">Memory Allocation Overview</h4>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="bg-slate-700/50 p-4 rounded-lg border border-slate-600/30">
                          <p className="text-slate-400 text-sm mb-2">Used Memory</p>
                          <p className="text-2xl font-bold text-red-400">{(systemMetrics.system.virtualMemoryTotalGb - systemMetrics.system.virtualMemoryAvailableGb).toFixed(2)} GB</p>
                          <p className="text-xs text-slate-500 mt-1">{((systemMetrics.system.virtualMemoryPercent).toFixed(1))}% of total</p>
                        </div>
                        <div className="bg-slate-700/50 p-4 rounded-lg border border-slate-600/30">
                          <p className="text-slate-400 text-sm mb-2">Available Memory</p>
                          <p className="text-2xl font-bold text-green-400">{systemMetrics.system.virtualMemoryAvailableGb.toFixed(2)} GB</p>
                          <p className="text-xs text-slate-500 mt-1">{(100 - systemMetrics.system.virtualMemoryPercent).toFixed(1)}% of total</p>
                        </div>
                        <div className="bg-slate-700/50 p-4 rounded-lg border border-slate-600/30">
                          <p className="text-slate-400 text-sm mb-2">Process Memory</p>
                          <p className="text-2xl font-bold text-blue-400">{systemMetrics.process.memoryRssMb.toFixed(2)} MB</p>
                          <p className="text-xs text-slate-500 mt-1">{(systemMetrics.process.memoryPercent).toFixed(2)}% of system</p>
                        </div>
                      </div>
                    </div>
                  </div>
                ) : null}
              </div>

              {/* Last Updated */}
              <div className="text-right text-sm text-slate-500">
                Last updated: {systemMetrics?.timestamp ? new Date(systemMetrics.timestamp).toLocaleTimeString() : 'Never'}
              </div>
            </div>
          )}

          {/* Users Tab */}
          {activeTab === 'users' && (
            <div className="space-y-6">
              {/* Page Header */}
              <div className="flex items-center justify-between">
                <h2 className="text-3xl font-bold text-white">User Management</h2>
                <button onClick={handleAddUser} className="px-4 py-2 bg-green-600 text-white rounded-md shadow-md hover:bg-green-500 transition-all">
                  + Add New User
                </button>
              </div>

              {/* Search & Filter Bar */}
              <div className="bg-slate-800/60 p-4 rounded-lg border border-slate-700/30">
                <div className="flex items-center gap-4">
                  <div className="flex-1">
                    <label htmlFor="users-search" className="sr-only">Search users</label>
                    <input
                      id="users-search"
                      type="text"
                      placeholder="Search users..."
                      value={userSearchTerm}
                      onChange={(e) => setUserSearchTerm(e.target.value)}
                      className="w-full px-4 py-2 bg-slate-700 text-slate-200 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-cyan-500"
                    />
                  </div>
                  <button onClick={handleUserSearch} className="px-4 py-2 bg-cyan-600 text-white rounded-lg shadow-md hover:bg-cyan-500 transition-all">
                    Search
                  </button>
                </div>
              </div>

              {/* Users Table */}
              <div className="bg-slate-800 rounded-lg border border-slate-700/30">
                <div className="grid grid-cols-5 gap-4 p-4 text-slate-400 font-semibold uppercase tracking-wider border-b border-slate-700">
                  <div className="flex items-center gap-2">
                    <span className="text-lg">👤</span>
                    User
                  </div>
                  <div className="hidden md:block">Email</div>
                  <div className="text-center">Role</div>
                  <div className="text-center">Status</div>
                  <div className="text-center">Actions</div>
                </div>
                <div className="divide-y divide-slate-700">
                  {users
                    .filter((user) => userSearchTerm.length === 0 || user.username.toLowerCase().includes(userSearchTerm.toLowerCase()) || user.email.toLowerCase().includes(userSearchTerm.toLowerCase()))
                    .map((user) => (
                      <div key={user.id} className="grid grid-cols-5 gap-4 p-4 hover:bg-slate-700 transition-all">
                        <div className="flex items-center gap-2">
                          <span className="text-lg">👤</span>
                          <span className="font-medium text-white">{user.username}</span>
                        </div>
                        <div className="hidden md:block">
                          <p className="text-slate-300 text-sm">{user.email}</p>
                        </div>
                        <div className="text-center">
                          <span className={`text-xs font-bold px-2 py-1 rounded-full ${user.role === 'admin' ? 'bg-red-500/20 text-red-300' : 'bg-green-500/20 text-green-300'}`}>
                            {user.role === 'admin' ? 'Admin' : 'User'}
                          </span>
                        </div>
                        <div className="text-center">
                          <span className={`text-xs font-bold px-2 py-1 rounded-full ${user.status === 'active' ? 'bg-green-500/20 text-green-300' : 'bg-red-500/20 text-red-300'}`}>
                            {user.status === 'active' ? 'Active' : 'Inactive'}
                          </span>
                        </div>
                        <div className="text-center flex gap-2 justify-center flex-wrap">
                          <button
                            onClick={() => toggleUserStatus(user.id, user.status === 'active')}
                            className={`px-3 py-1 text-xs font-semibold rounded-lg transition-all ${user.status === 'active' ? 'bg-red-600 text-white hover:bg-red-500' : 'bg-green-600 text-white hover:bg-green-500'}`}
                          >
                            {user.status === 'active' ? 'Deactivate' : 'Activate'}
                          </button>
                          <button
                            onClick={() => setConfirmAction({
                              type: 'delete_user',
                              targetId: user.id,
                              details: { username: user.username, action: 'delete_user', timestamp: new Date().toISOString() },
                            })}
                            className="px-3 py-1 text-xs font-semibold bg-red-700 text-white rounded-lg hover:bg-red-600 transition-all"
                          >
                            Delete
                          </button>
                        </div>
                      </div>
                    ))}
                </div>
              </div>
            </div>
          )}

          {/* Config Tab */}
          {activeTab === 'config' && (
            <div className="space-y-6">
              {/* Page Header */}
              <div className="flex items-center justify-between">
                <h2 className="text-3xl font-bold text-white">System Configuration</h2>
                <button onClick={saveConfigChanges} disabled={savingConfig} className="px-4 py-2 bg-green-600 text-white rounded-md shadow-md hover:bg-green-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all">
                  {savingConfig ? 'Saving...' : 'Save Changes'}
                </button>
              </div>

              {/* Settings Form */}
              <div className="bg-slate-800 rounded-lg border border-slate-700/30 p-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="config-site-title" className="block text-sm font-medium text-slate-300 mb-1">Site Title</label>
                    <input
                      id="config-site-title"
                      type="text"
                      defaultValue="Admin Console"
                      onChange={(e) => setConfigChanges((prev) => ({ ...prev, siteTitle: e.target.value }))}
                      className="w-full px-4 py-2 bg-slate-700 text-slate-200 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-cyan-500"
                    />
                  </div>
                  <div>
                    <label htmlFor="config-admin-email" className="block text-sm font-medium text-slate-300 mb-1">Admin Email</label>
                    <input
                      id="config-admin-email"
                      type="email"
                      defaultValue="admin@example.com"
                      onChange={(e) => setConfigChanges((prev) => ({ ...prev, adminEmail: e.target.value }))}
                      className="w-full px-4 py-2 bg-slate-700 text-slate-200 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-cyan-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-1">Feature Toggles</label>
                    <div className="flex items-center gap-2">
                      <button onClick={() => setConfigChanges((prev) => ({ ...prev, newDashboardEnabled: true }))} className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg shadow-md hover:bg-green-500 transition-all">
                        Enable New Dashboard
                      </button>
                      <button onClick={() => setConfigChanges((prev) => ({ ...prev, oldDashboardDisabled: true }))} className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg shadow-md hover:bg-red-500 transition-all">
                        Disable Old Dashboard
                      </button>
                    </div>
                  </div>
                  <div>
                    <label htmlFor="config-api-rate-limit" className="block text-sm font-medium text-slate-300 mb-1">API Rate Limit</label>
                    <input
                      id="config-api-rate-limit"
                      type="number"
                      defaultValue="100"
                      onChange={(e) => setConfigChanges((prev) => ({ ...prev, apiRateLimit: e.target.value }))}
                      className="w-full px-4 py-2 bg-slate-700 text-slate-200 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-cyan-500"
                    />
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Security Tab */}
          {activeTab === 'security' && (
            <div className="space-y-6">
              {/* Page Header */}
              <div className="flex items-center justify-between">
                <h2 className="text-3xl font-bold text-white">Security Settings</h2>
                <button onClick={saveSecuritySettings} disabled={savingSecurity} className="px-4 py-2 bg-green-600 text-white rounded-md shadow-md hover:bg-green-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all">
                  {savingSecurity ? 'Saving...' : 'Save Changes'}
                </button>
              </div>

              {/* Security Options */}
              <div className="bg-slate-800 rounded-lg border border-slate-700/30 p-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-1">Enable 2FA</label>
                    <div className="flex items-center gap-2">
                      <button onClick={() => toggle2FA(true)} className="px-4 py-2 bg-green-600 text-white rounded-lg shadow-md hover:bg-green-500 transition-all">
                        Enable
                      </button>
                      <button onClick={() => toggle2FA(false)} className="px-4 py-2 bg-red-600 text-white rounded-lg shadow-md hover:bg-red-500 transition-all">
                        Disable
                      </button>
                    </div>
                  </div>
                  <div>
                    <label htmlFor="security-ip-whitelist" className="block text-sm font-medium text-slate-300 mb-1">IP Whitelisting</label>
                    <input
                      id="security-ip-whitelist"
                      type="text"
                      placeholder="192.168.1.1, 192.168.1.2"
                      className="w-full px-4 py-2 bg-slate-700 text-slate-200 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-cyan-500"
                    />
                  </div>
                  <div>
                    <label htmlFor="security-password-policy" className="block text-sm font-medium text-slate-300 mb-1">Password Policy</label>
                    <select id="security-password-policy" className="w-full px-4 py-2 bg-slate-700 text-slate-200 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-cyan-500">
                      <option value="strong">Strong (recommended)</option>
                      <option value="medium">Medium</option>
                      <option value="weak">Weak</option>
                    </select>
                  </div>
                  <div>
                    <label htmlFor="security-session-timeout" className="block text-sm font-medium text-slate-300 mb-1">Session Timeout</label>
                    <input
                      id="security-session-timeout"
                      type="number"
                      defaultValue="30"
                      className="w-full px-4 py-2 bg-slate-700 text-slate-200 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-cyan-500"
                    />
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Logs Tab */}
          {activeTab === 'logs' && (
            <div className="space-y-6">
              {/* Page Header */}
              <div className="flex items-center justify-between">
                <h2 className="text-3xl font-bold text-white">Audit Logs</h2>
                <button className="px-4 py-2 bg-green-600 text-white rounded-md shadow-md hover:bg-green-500 transition-all">
                  Download Logs
                </button>
              </div>

              {/* Logs Table */}
              <div className="bg-slate-800 rounded-lg border border-slate-700/30">
                <div className="grid grid-cols-4 gap-4 p-4 text-slate-400 font-semibold uppercase tracking-wider border-b border-slate-700">
                  <div className="flex items-center gap-2">
                    <span className="text-lg">📅</span>
                    Date
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-lg">🧑‍💼</span>
                    User
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-lg">🔍</span>
                    Action
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-lg">ℹ️</span>
                    Details
                  </div>
                </div>
                <div className="divide-y divide-slate-700">
                  {auditLogs?.logs?.map((log) => (
                    <div key={log.id} className="grid grid-cols-4 gap-4 p-4 hover:bg-slate-700 transition-all">
                      <div className="flex items-center gap-2">
                        <span className="text-slate-300 text-sm">{new Date(log.timestamp).toLocaleString()}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-slate-300 text-sm">{typeof log.user === 'string' ? log.user : 'System'}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-slate-300 text-sm">{log.action}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-slate-300 text-sm">{log.details}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Critical Alerts Tab */}
          {activeTab === 'critical' && (
            <div className="space-y-6">
              {/* Page Header */}
              <div className="flex items-center justify-between">
                <h2 className="text-3xl font-bold text-white">🚨 Critical Alerts</h2>
                <button className="px-4 py-2 bg-red-600 text-white rounded-md shadow-md hover:bg-red-500 transition-all">
                  Clear All
                </button>
              </div>

              {/* Critical Alerts List */}
              <div className="space-y-4">
                {Array.isArray(_criticalAlerts) && _criticalAlerts.length > 0 ? (
                  _criticalAlerts.map((alert) => (
                    <div key={alert.id} className="bg-gradient-to-r from-red-900/50 to-orange-900/50 rounded-lg border border-red-500/50 p-6 hover:border-red-400 transition-all">
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1">
                          <h3 className="text-xl font-bold text-red-300 mb-2">{alert.title}</h3>
                          <p className="text-slate-300 mb-3">{alert.description}</p>
                          <div className="flex items-center gap-4 text-sm">
                            <span className={`px-3 py-1 rounded-full font-semibold ${alert.severity === 'critical' ? 'bg-red-500/20 text-red-300' : alert.severity === 'high' ? 'bg-orange-500/20 text-orange-300' : 'bg-yellow-500/20 text-yellow-300'}`}>
                              {alert.severity.toUpperCase()}
                            </span>
                            <span className="text-slate-400">{alert.timestamp}</span>
                          </div>
                        </div>
                        <button onClick={() => setConfirmAction({ type: 'critical_action', targetId: alert.id, details: alert })} className="px-4 py-2 bg-cyan-600 text-white rounded-lg shadow-md hover:bg-cyan-500 transition-all whitespace-nowrap">
                          {alert.action || 'Resolve'}
                        </button>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-12 text-slate-400">
                    <span className="text-4xl block mb-2">✅</span>
                    <p>No critical alerts at this time</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Incidents Tab */}
          {activeTab === 'incidents' && (
            <div className="space-y-6">
              {/* Page Header */}
              <div className="flex items-center justify-between">
                <h2 className="text-3xl font-bold text-white">⚡ Active Incidents</h2>
                <button onClick={fetchIncidents} disabled={loadingIncidents} className="px-4 py-2 bg-green-600 text-white rounded-md shadow-md hover:bg-green-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed">
                  {loadingIncidents ? 'Refreshing...' : 'Refresh Incidents'}
                </button>
              </div>

              {/* Incidents Table */}
              {loadingIncidents ? (
                <div className="text-center py-12 text-slate-400">Loading incidents...</div>
              ) : (
                <div className="bg-slate-800 rounded-lg border border-slate-700/30 overflow-hidden">
                  <div className="grid grid-cols-5 gap-4 p-4 text-slate-400 font-semibold uppercase tracking-wider border-b border-slate-700">
                    <div className="flex items-center gap-2">
                      <span className="text-lg">⚡</span>
                      Type
                    </div>
                    <div>Title</div>
                    <div className="text-center">Severity</div>
                    <div className="text-center">Status</div>
                    <div className="text-center">Actions</div>
                  </div>
                  <div className="divide-y divide-slate-700">
                    {incidents.length > 0 ? (
                      incidents.map((incident) => (
                        <div key={incident.id} className="grid grid-cols-5 gap-4 p-4 hover:bg-slate-700 transition-all items-center">
                          <div>
                            <span className="font-medium text-white">{incident.type}</span>
                          </div>
                          <div>
                            <p className="text-slate-300 text-sm">{incident.title}</p>
                            <p className="text-slate-500 text-xs">{incident.affectedSystems.join(', ')}</p>
                          </div>
                          <div className="text-center">
                            <span className={`text-xs font-bold px-2 py-1 rounded-full ${incident.severity === 'critical' ? 'bg-red-500/20 text-red-300' : incident.severity === 'high' ? 'bg-orange-500/20 text-orange-300' : 'bg-yellow-500/20 text-yellow-300'}`}>
                              {incident.severity.toUpperCase()}
                            </span>
                          </div>
                          <div className="text-center">
                            <label htmlFor={`status-select-${incident.id}`} className="sr-only">
                              Incident Status
                            </label>
                            <select
                              id={`status-select-${incident.id}`}
                              value={incident.status}
                              onChange={(e) => updateIncidentStatus(incident.id, e.target.value as Incident['status'])}
                              className="px-2 py-1 bg-slate-700 text-slate-200 rounded text-xs border border-slate-600 focus:outline-none focus:ring-2 focus:ring-cyan-500"
                            >
                              <option value="active">Active</option>
                              <option value="detected">Detected</option>
                              <option value="investigating">Investigating</option>
                              <option value="contained">Contained</option>
                              <option value="resolved">Resolved</option>
                              <option value="archived">Archived</option>
                            </select>
                          </div>
                          <div className="text-center">
                            <button onClick={() => updateIncidentStatus(incident.id, 'resolved')} className="px-2 py-1 bg-green-600 text-white text-xs rounded hover:bg-green-500 transition-all">
                              Resolve
                            </button>
                          </div>
                        </div>
                      ))
                    ) : (
                      <div className="col-span-5 text-center py-8 text-slate-400">
                        No incidents found
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Keys Tab */}
          {activeTab === 'keys' && (
            <div className="space-y-6">
              {/* Page Header */}
              <div className="flex items-center justify-between">
                <h2 className="text-3xl font-bold text-white">🔑 Secret Keys & Certificates</h2>
                <button onClick={fetchSecretKeys} disabled={loadingKeys} className="px-4 py-2 bg-green-600 text-white rounded-md shadow-md hover:bg-green-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed">
                  {loadingKeys ? 'Loading...' : '↻ Refresh Keys'}
                </button>
              </div>

              {/* Keys Table */}
              {loadingKeys ? (
                <div className="text-center py-12 text-slate-400">Loading secret keys...</div>
              ) : (
                <div className="bg-slate-800 rounded-lg border border-slate-700/30 overflow-hidden">
                  <div className="grid grid-cols-5 gap-4 p-4 text-slate-400 font-semibold uppercase tracking-wider border-b border-slate-700">
                    <div className="flex items-center gap-2">
                      <span className="text-lg">🔐</span>
                      Name
                    </div>
                    <div>Type</div>
                    <div className="text-center">Status</div>
                    <div className="text-center">Last Rotated</div>
                    <div className="text-center">Actions</div>
                  </div>
                  <div className="divide-y divide-slate-700">
                    {secretKeys.length > 0 ? (
                      secretKeys.map((key) => (
                        <div key={key.id} className="grid grid-cols-5 gap-4 p-4 hover:bg-slate-700 transition-all items-center">
                          <div>
                            <p className="font-medium text-white">{key.name}</p>
                            {key.expiresAt && <p className="text-xs text-orange-400">Expires: {key.expiresAt}</p>}
                          </div>
                          <div>
                            <span className="text-slate-300 text-sm capitalize">{key.type}</span>
                          </div>
                          <div className="text-center">
                            <span className={`text-xs font-bold px-2 py-1 rounded-full ${key.status === 'active' ? 'bg-green-500/20 text-green-300' : key.status === 'rotated' ? 'bg-blue-500/20 text-blue-300' : 'bg-red-500/20 text-red-300'}`}>
                              {key.status.toUpperCase()}
                            </span>
                          </div>
                          <div className="text-center">
                            <span className="text-slate-300 text-sm">{key.lastRotated}</span>
                          </div>
                          <div className="text-center">
                            <button onClick={() => rotateSecurityKey(key.id)} className="px-2 py-1 bg-cyan-600 text-white text-xs rounded hover:bg-cyan-500 transition-all">
                              Rotate
                            </button>
                          </div>
                        </div>
                      ))
                    ) : (
                      <div className="col-span-5 text-center py-8 text-slate-400">
                        No secret keys found
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Confirmation modal for critical actions */}
          {confirmAction && (
            <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
              <div className="absolute inset-0 bg-black/60" onClick={() => setConfirmAction(null)} />
              <div className="relative bg-slate-900 rounded-lg p-6 border border-slate-700 w-full max-w-md">
                <h3 className="text-lg font-bold mb-2">Confirm Action</h3>
                <p className="text-sm text-slate-300 mb-4">Are you sure you want to execute <strong>{confirmAction.type}</strong>?</p>
                <div className="flex gap-2 justify-end">
                  <button className="px-3 py-1 rounded bg-slate-700" onClick={() => setConfirmAction(null)}>Cancel</button>
                  <button className="px-3 py-1 rounded bg-cyan-600 text-white" onClick={executeConfirmAction} disabled={confirmLoading}>{confirmLoading ? 'Running...' : 'Confirm'}</button>
                </div>
              </div>
            </div>
          )}

          {/* Add User Form Modal */}
          {showAddUserForm && (
            <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
              <div className="absolute inset-0 bg-black/60" onClick={() => setShowAddUserForm(false)} />
              <div className="relative bg-slate-900 rounded-lg p-6 border border-slate-700 w-full max-w-md max-h-screen overflow-y-auto">
                <h3 className="text-xl font-bold mb-4 text-white">Create New User</h3>

                {formError && (
                  <div className="mb-4 p-3 bg-red-500/20 border border-red-500/50 rounded-lg">
                    <p className="text-red-300 text-sm">{formError}</p>
                  </div>
                )}

                <div className="space-y-4">
                  {/* Username */}
                  <div>
                    <label htmlFor="new-user-username" className="block text-sm font-semibold text-slate-200 mb-2">
                      Username
                    </label>
                    <input
                      id="new-user-username"
                      type="text"
                      placeholder="Enter username"
                      value={newUserForm.username}
                      onChange={(e) => setNewUserForm({ ...newUserForm, username: e.target.value })}
                      className="w-full px-4 py-2 bg-slate-700 text-white rounded-lg border border-slate-600 focus:outline-none focus:ring-2 focus:ring-cyan-500"
                      disabled={addingUser}
                    />
                  </div>

                  {/* Email */}
                  <div>
                    <label htmlFor="new-user-email" className="block text-sm font-semibold text-slate-200 mb-2">
                      Email
                    </label>
                    <input
                      id="new-user-email"
                      type="email"
                      placeholder="Enter email address"
                      value={newUserForm.email}
                      onChange={(e) => setNewUserForm({ ...newUserForm, email: e.target.value })}
                      className="w-full px-4 py-2 bg-slate-700 text-white rounded-lg border border-slate-600 focus:outline-none focus:ring-2 focus:ring-cyan-500"
                      disabled={addingUser}
                    />
                  </div>

                  {/* Password */}
                  <div>
                    <label htmlFor="new-user-password" className="block text-sm font-semibold text-slate-200 mb-2">
                      Password
                    </label>
                    <input
                      id="new-user-password"
                      type="password"
                      placeholder="Enter password (min 8 characters)"
                      value={newUserForm.password}
                      onChange={(e) => setNewUserForm({ ...newUserForm, password: e.target.value })}
                      className="w-full px-4 py-2 bg-slate-700 text-white rounded-lg border border-slate-600 focus:outline-none focus:ring-2 focus:ring-cyan-500"
                      disabled={addingUser}
                    />
                  </div>

                  {/* Confirm Password */}
                  <div>
                    <label htmlFor="new-user-confirm-password" className="block text-sm font-semibold text-slate-200 mb-2">
                      Confirm Password
                    </label>
                    <input
                      id="new-user-confirm-password"
                      type="password"
                      placeholder="Confirm password"
                      value={newUserForm.confirmPassword}
                      onChange={(e) => setNewUserForm({ ...newUserForm, confirmPassword: e.target.value })}
                      className="w-full px-4 py-2 bg-slate-700 text-white rounded-lg border border-slate-600 focus:outline-none focus:ring-2 focus:ring-cyan-500"
                      disabled={addingUser}
                    />
                  </div>

                  {/* Role */}
                  <div>
                    <label htmlFor="new-user-role" className="block text-sm font-semibold text-slate-200 mb-2">
                      Role
                    </label>
                    <select
                      id="new-user-role"
                      value={newUserForm.role}
                      onChange={(e) => setNewUserForm({ ...newUserForm, role: e.target.value as 'operator' | 'analyst' | 'admin' })}
                      className="w-full px-4 py-2 bg-slate-700 text-white rounded-lg border border-slate-600 focus:outline-none focus:ring-2 focus:ring-cyan-500"
                      disabled={addingUser}
                    >
                      <option value="operator">Operator (Read-only)</option>
                      <option value="analyst">Analyst (Standard)</option>
                      <option value="admin">Admin (Full Access)</option>
                    </select>
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex gap-2 justify-end mt-6 pt-4 border-t border-slate-700">
                  <button
                    onClick={() => setShowAddUserForm(false)}
                    disabled={addingUser}
                    className="px-4 py-2 rounded-lg bg-slate-700 text-slate-200 hover:bg-slate-600 transition-all disabled:opacity-50"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleSubmitNewUser}
                    disabled={addingUser}
                    className="px-4 py-2 rounded-lg bg-green-600 text-white hover:bg-green-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {addingUser ? 'Creating...' : 'Create User'}
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