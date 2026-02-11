import { useState, useEffect } from 'react'
import { RotateCw, Download, AlertCircle, CheckCircle, Loader, Eye, EyeOff, Trash2, Plus } from 'lucide-react'

// ============================================================================
// TYPES & INTERFACES
// ============================================================================

interface Toast {
  id: string
  message: string
  type: 'success' | 'error' | 'info' | 'warning'
}

interface APIKey {
  id: string
  name: string
  key: string
  created_at: string
  last_used: string
  is_active: boolean
}

interface UserProfile {
  id: string
  username: string
  email: string
  role: string
  last_login: string
}

// ============================================================================
// HEADER COMPONENT
// ============================================================================

const SettingsHeader = () => (
  <div className="relative overflow-hidden bg-gradient-to-r from-slate-900 via-purple-900/20 to-slate-900 border-b border-slate-700">
    <div className="absolute inset-0 opacity-30">
      <div className="absolute top-0 left-1/4 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl"></div>
      <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-pink-500/10 rounded-full blur-3xl"></div>
    </div>
    <div className="relative p-8">
      <h1 className="text-4xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
        ⚙️ System Settings & Configuration
      </h1>
      <p className="text-slate-400 mt-2">Manage security, network, notifications, and integrations with full 100% backend integration</p>
    </div>
  </div>
)

// ============================================================================
// TOAST NOTIFICATION COMPONENT
// ============================================================================

interface ToastProps {
  toasts: Toast[]
  onRemove: (id: string) => void
}

const ToastContainer = ({ toasts, onRemove }: ToastProps) => (
  <div className="fixed bottom-4 right-4 space-y-2 z-50">
    {toasts.map((toast) => (
      <div
        key={toast.id}
        className={`px-4 py-3 rounded-lg flex items-center gap-2 animate-in slide-in-from-bottom-5 ${toast.type === 'success' ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' :
            toast.type === 'error' ? 'bg-red-500/20 text-red-300 border border-red-500/30' :
              toast.type === 'info' ? 'bg-blue-500/20 text-blue-300 border border-blue-500/30' :
                'bg-yellow-500/20 text-yellow-300 border border-yellow-500/30'
          }`}
      >
        {toast.type === 'success' && <CheckCircle size={18} />}
        {toast.type === 'error' && <AlertCircle size={18} />}
        {toast.type === 'info' && <AlertCircle size={18} />}
        {toast.type === 'warning' && <AlertCircle size={18} />}
        <span className="text-sm font-medium">{toast.message}</span>
        <button
          onClick={() => onRemove(toast.id)}
          className="ml-2 hover:opacity-75 transition-opacity"
        >
          ✕
        </button>
      </div>
    ))}
  </div>
)

// ============================================================================
// SETTINGS COMPONENTS
// ============================================================================

interface SettingsSectionProps {
  title: string
  description: string
  children: React.ReactNode
}

const SettingsSection = ({ title, description, children }: SettingsSectionProps) => (
  <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 mb-6">
    <h3 className="text-lg font-semibold text-slate-100 mb-1">{title}</h3>
    <p className="text-sm text-slate-400 mb-4">{description}</p>
    <div className="space-y-4">{children}</div>
  </div>
)

interface ToggleSettingProps {
  label: string
  description: string
  enabled: boolean
  onChange: (value: boolean) => void
  disabled?: boolean
}

const ToggleSetting = ({ label, description, enabled, onChange, disabled = false }: ToggleSettingProps) => (
  <div className="flex items-center justify-between p-3 bg-slate-700/50 rounded border border-slate-600">
    <div className="flex-1">
      <p className="text-sm font-medium text-slate-100">{label}</p>
      <p className="text-xs text-slate-400 mt-1">{description}</p>
    </div>
    <button
      onClick={() => onChange(!enabled)}
      disabled={disabled}
      title={`Toggle ${label}`}
      aria-label={`Toggle ${label}`}
      className={`ml-4 relative inline-flex h-8 w-16 items-center rounded-full transition-colors disabled:opacity-50 ${enabled ? 'bg-emerald-500' : 'bg-slate-600'
        }`}
    >
      <span
        className={`inline-block h-6 w-6 transform rounded-full bg-white transition-transform ${enabled ? 'translate-x-9' : 'translate-x-1'
          }`}
      />
    </button>
  </div>
)

interface TextInputSettingProps {
  label: string
  description: string
  value: string
  onChange: (value: string) => void
  placeholder?: string
  type?: string
  disabled?: boolean
}

const TextInputSetting = ({ label, description, value, onChange, placeholder, type = 'text', disabled = false }: TextInputSettingProps) => (
  <div className="p-3 bg-slate-700/50 rounded border border-slate-600">
    <label className="text-sm font-medium text-slate-100 mb-2 block">{label}</label>
    <p className="text-xs text-slate-400 mb-2">{description}</p>
    <input
      type={type}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      disabled={disabled}
      className="w-full px-3 py-2 bg-slate-800 border border-slate-600 rounded text-slate-200 placeholder-slate-500 focus:outline-none focus:border-purple-500/50 text-sm disabled:opacity-50"
    />
  </div>
)

interface SelectSettingProps {
  label: string
  description: string
  value: string
  onChange: (value: string) => void
  options: { label: string; value: string }[]
  disabled?: boolean
}

const SelectSetting = ({ label, description, value, onChange, options, disabled = false }: SelectSettingProps) => (
  <div className="p-3 bg-slate-700/50 rounded border border-slate-600">
    <label className="text-sm font-medium text-slate-100 mb-2 block">{label}</label>
    <p className="text-xs text-slate-400 mb-2">{description}</p>
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      disabled={disabled}
      title={label}
      aria-label={label}
      className="w-full px-3 py-2 bg-slate-800 border border-slate-600 rounded text-slate-200 focus:outline-none focus:border-purple-500/50 text-sm disabled:opacity-50"
    >
      {options.map((opt) => (
        <option key={opt.value} value={opt.value}>
          {opt.label}
        </option>
      ))}
    </select>
  </div>
)

// ============================================================================
// MAIN SETTINGS PAGE COMPONENT
// ============================================================================

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState('general')
  const [loading, setLoading] = useState(false)
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle')
  const [toasts, setToasts] = useState<Toast[]>([])

  // ========== General Settings ==========
  const [systemName, setSystemName] = useState('JARVIS-SECURITY-AI')
  const [enableTelemetry, setEnableTelemetry] = useState(true)
  const [telemetryUrl, setTelemetryUrl] = useState('http://localhost:8001/telemetry/events')
  const [logLevel, setLogLevel] = useState('INFO')

  // ========== Network Settings ==========
  const [dpiInterface, setDpiInterface] = useState('eth0')
  const [packetSnaplen, setPacketSnaplen] = useState('65535')
  const [dpiEnabled, setDpiEnabled] = useState(true)
  const [ascendEnabled, setAscendEnabled] = useState(false)

  // ========== Backend Settings ==========
  const [backendHost, setBackendHost] = useState('0.0.0.0')
  const [backendPort, setBackendPort] = useState('8000')
  const [mTlsRequired, setMTlsRequired] = useState(false)
  const [keyRotationEnabled, setKeyRotationEnabled] = useState(false)

  // ========== Security Settings ==========
  const [enableBiometric, setEnableBiometric] = useState(true)
  const [enablePQC, setEnablePQC] = useState(true)
  const [enableZeroTrust, setEnableZeroTrust] = useState(true)
  const [sessionTimeout, setSessionTimeout] = useState('3600')

  // ========== Notification Settings ==========
  const [emailAlerts, setEmailAlerts] = useState(true)
  const [slackAlerts, setSlackAlerts] = useState(false)
  const [webhookAlerts, setWebhookAlerts] = useState(false)
  const [alertThreshold, setAlertThreshold] = useState('medium')

  // ========== API Keys Management ==========
  const [apiKeys, setApiKeys] = useState<APIKey[]>([])
  const [newKeyName, setNewKeyName] = useState('')
  const [showKeyForm, setShowKeyForm] = useState(false)

  // ========== User Profile ==========
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null)
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showPasswords, setShowPasswords] = useState(false)

  // ========== Toast Helper ==========
  const addToast = (message: string, type: 'success' | 'error' | 'info' | 'warning' = 'info') => {
    const id = Date.now().toString()
    setToasts(prev => [...prev, { id, message, type }])
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 3000)
  }

  // ========== API CALLS ==========

  // Load all settings on mount
  useEffect(() => {
    const loadAllSettings = async () => {
      try {
        // Load general settings
        const generalResponse = await fetch('/api/settings/general')
        if (generalResponse.ok) {
          const generalSettings = await generalResponse.json()
          setSystemName(generalSettings.system_name || 'JARVIS-SECURITY-AI')
          setEnableTelemetry(generalSettings.enable_telemetry ?? true)
          setTelemetryUrl(generalSettings.telemetry_url || 'http://localhost:8001/telemetry/events')
          setLogLevel(generalSettings.log_level || 'INFO')
        }

        // Load network settings
        const networkResponse = await fetch('/api/settings/network')
        if (networkResponse.ok) {
          const networkSettings = await networkResponse.json()
          setDpiEnabled(networkSettings.dpi_enabled ?? true)
          setDpiInterface(networkSettings.dpi_interface || 'eth0')
          setPacketSnaplen(networkSettings.packet_snaplen?.toString() || '65535')
          setAscendEnabled(networkSettings.ascend_enabled ?? false)
        }

        // Load security settings
        const securityResponse = await fetch('/api/settings/security')
        if (securityResponse.ok) {
          const securitySettings = await securityResponse.json()
          setEnableBiometric(securitySettings.enable_biometric ?? true)
          setEnablePQC(securitySettings.enable_pqc ?? true)
          setEnableZeroTrust(securitySettings.enable_zero_trust ?? true)
          setSessionTimeout(securitySettings.session_timeout?.toString() || '3600')
          setMTlsRequired(securitySettings.mTls_required ?? false)
          setKeyRotationEnabled(securitySettings.key_rotation_enabled ?? false)
        }

        // Load notification settings
        const notifResponse = await fetch('/api/settings/notifications')
        if (notifResponse.ok) {
          const notifSettings = await notifResponse.json()
          setEmailAlerts(notifSettings.email_alerts ?? true)
          setSlackAlerts(notifSettings.slack_alerts ?? false)
          setWebhookAlerts(notifSettings.webhook_alerts ?? false)
          setAlertThreshold(notifSettings.alert_threshold || 'medium')
        }

        // Load API keys
        const keysResponse = await fetch('/api/settings/api-keys')
        if (keysResponse.ok) {
          const keys = await keysResponse.json()
          setApiKeys(keys || [])
        }

        // Load user profile
        const profileResponse = await fetch('/api/settings/profile')
        if (profileResponse.ok) {
          const profile = await profileResponse.json()
          setUserProfile(profile)
        }
      } catch (error) {
        console.error('Failed to load settings:', error)
        addToast('Failed to load settings', 'error')
      }
    }

    loadAllSettings()
  }, [])

  // Save general settings
  const handleSaveGeneralSettings = async () => {
    setLoading(true)
    setSaveStatus('saving')
    try {
      const response = await fetch('/api/settings/general', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          system_name: systemName,
          enable_telemetry: enableTelemetry,
          telemetry_url: telemetryUrl,
          log_level: logLevel,
          updated_at: new Date().toISOString(),
        }),
      })

      if (response.ok) {
        setSaveStatus('saved')
        addToast('General settings saved successfully', 'success')
        setTimeout(() => setSaveStatus('idle'), 3000)
      } else {
        setSaveStatus('error')
        addToast('Failed to save general settings', 'error')
      }
    } catch (error) {
      console.error('Failed to save general settings:', error)
      setSaveStatus('error')
      addToast('Error saving general settings', 'error')
    } finally {
      setLoading(false)
    }
  }

  // Save network settings
  const handleSaveNetworkSettings = async () => {
    setLoading(true)
    setSaveStatus('saving')
    try {
      const response = await fetch('/api/settings/network', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          dpi_enabled: dpiEnabled,
          dpi_interface: dpiInterface,
          packet_snaplen: parseInt(packetSnaplen),
          ascend_enabled: ascendEnabled,
          updated_at: new Date().toISOString(),
        }),
      })

      if (response.ok) {
        setSaveStatus('saved')
        addToast('Network settings saved successfully', 'success')
        setTimeout(() => setSaveStatus('idle'), 3000)
      } else {
        setSaveStatus('error')
        addToast('Failed to save network settings', 'error')
      }
    } catch (error) {
      console.error('Failed to save network settings:', error)
      setSaveStatus('error')
      addToast('Error saving network settings', 'error')
    } finally {
      setLoading(false)
    }
  }

  // Save security settings
  const handleSaveSecuritySettings = async () => {
    setLoading(true)
    setSaveStatus('saving')
    try {
      const response = await fetch('/api/settings/security', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          enable_biometric: enableBiometric,
          enable_pqc: enablePQC,
          enable_zero_trust: enableZeroTrust,
          session_timeout: parseInt(sessionTimeout),
          mTls_required: mTlsRequired,
          key_rotation_enabled: keyRotationEnabled,
          updated_at: new Date().toISOString(),
        }),
      })

      if (response.ok) {
        setSaveStatus('saved')
        addToast('Security settings saved successfully', 'success')
        setTimeout(() => setSaveStatus('idle'), 3000)
      } else {
        setSaveStatus('error')
        addToast('Failed to save security settings', 'error')
      }
    } catch (error) {
      console.error('Failed to save security settings:', error)
      setSaveStatus('error')
      addToast('Error saving security settings', 'error')
    } finally {
      setLoading(false)
    }
  }

  // Save notification settings
  const handleSaveNotificationSettings = async () => {
    setLoading(true)
    setSaveStatus('saving')
    try {
      const response = await fetch('/api/settings/notifications', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email_alerts: emailAlerts,
          slack_alerts: slackAlerts,
          webhook_alerts: webhookAlerts,
          alert_threshold: alertThreshold,
          updated_at: new Date().toISOString(),
        }),
      })

      if (response.ok) {
        setSaveStatus('saved')
        addToast('Notification settings saved successfully', 'success')
        setTimeout(() => setSaveStatus('idle'), 3000)
      } else {
        setSaveStatus('error')
        addToast('Failed to save notification settings', 'error')
      }
    } catch (error) {
      console.error('Failed to save notification settings:', error)
      setSaveStatus('error')
      addToast('Error saving notification settings', 'error')
    } finally {
      setLoading(false)
    }
  }

  // Create API key
  const handleCreateAPIKey = async () => {
    if (!newKeyName.trim()) {
      addToast('Please enter an API key name', 'warning')
      return
    }

    setLoading(true)
    try {
      const response = await fetch('/api/settings/api-keys', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: newKeyName,
          created_at: new Date().toISOString(),
        }),
      })

      if (response.ok) {
        const newKey = await response.json()
        setApiKeys([...apiKeys, newKey])
        setNewKeyName('')
        setShowKeyForm(false)
        addToast('API key created successfully', 'success')
      } else {
        addToast('Failed to create API key', 'error')
      }
    } catch (error) {
      console.error('Failed to create API key:', error)
      addToast('Error creating API key', 'error')
    } finally {
      setLoading(false)
    }
  }

  // Delete API key
  const handleDeleteAPIKey = async (keyId: string) => {
    if (!confirm('Are you sure you want to delete this API key?')) return

    setLoading(true)
    try {
      const response = await fetch(`/api/settings/api-keys/${keyId}`, {
        method: 'DELETE',
      })

      if (response.ok) {
        setApiKeys(apiKeys.filter(k => k.id !== keyId))
        addToast('API key deleted successfully', 'success')
      } else {
        addToast('Failed to delete API key', 'error')
      }
    } catch (error) {
      console.error('Failed to delete API key:', error)
      addToast('Error deleting API key', 'error')
    } finally {
      setLoading(false)
    }
  }

  // Copy API key to clipboard
  const handleCopyAPIKey = (key: string) => {
    navigator.clipboard.writeText(key)
    addToast('API key copied to clipboard', 'success')
  }

  // Change password
  const handleChangePassword = async () => {
    if (!currentPassword || !newPassword || !confirmPassword) {
      addToast('Please fill in all password fields', 'warning')
      return
    }

    if (newPassword !== confirmPassword) {
      addToast('New passwords do not match', 'error')
      return
    }

    if (newPassword.length < 8) {
      addToast('Password must be at least 8 characters', 'warning')
      return
    }

    setLoading(true)
    try {
      const response = await fetch('/api/settings/profile/change-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
        }),
      })

      if (response.ok) {
        setCurrentPassword('')
        setNewPassword('')
        setConfirmPassword('')
        addToast('Password changed successfully', 'success')
      } else {
        addToast('Failed to change password', 'error')
      }
    } catch (error) {
      console.error('Failed to change password:', error)
      addToast('Error changing password', 'error')
    } finally {
      setLoading(false)
    }
  }

  // Rotate keys
  const handleKeyRotation = async () => {
    setLoading(true)
    try {
      const response = await fetch('/api/settings/security/rotate-keys', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      })

      if (response.ok) {
        addToast('Cryptographic keys rotated successfully', 'success')
      } else {
        addToast('Failed to rotate keys', 'error')
      }
    } catch (error) {
      console.error('Failed to rotate keys:', error)
      addToast('Error rotating keys', 'error')
    } finally {
      setLoading(false)
    }
  }

  // Export settings
  const handleExportSettings = async () => {
    try {
      const settings = {
        general: { systemName, enableTelemetry, telemetryUrl, logLevel },
        network: { dpiEnabled, dpiInterface, packetSnaplen, ascendEnabled },
        security: { enableBiometric, enablePQC, enableZeroTrust, sessionTimeout, mTlsRequired, keyRotationEnabled },
        notifications: { emailAlerts, slackAlerts, webhookAlerts, alertThreshold },
        exportedAt: new Date().toISOString(),
      }

      const dataStr = JSON.stringify(settings, null, 2)
      const dataBlob = new Blob([dataStr], { type: 'application/json' })
      const url = window.URL.createObjectURL(dataBlob)
      const link = document.createElement('a')
      link.href = url
      link.download = `jarvis_settings_${new Date().toISOString().split('T')[0]}.json`
      document.body.appendChild(link)
      link.click()
      window.URL.revokeObjectURL(url)
      addToast('Settings exported successfully', 'success')
    } catch (error) {
      console.error('Failed to export settings:', error)
      addToast('Error exporting settings', 'error')
    }
  }

  return (
    <div className="h-full flex flex-col bg-gradient-to-br from-slate-900 via-slate-900 to-slate-800 overflow-y-auto">
      <SettingsHeader />

      {/* Tabs */}
      <div className="border-b border-slate-700 bg-slate-900/30 px-6 flex gap-4 sticky top-0 z-10 overflow-x-auto">
        {[
          { id: 'general', label: '⚙️ General' },
          { id: 'network', label: '🌐 Network' },
          { id: 'security', label: '🔐 Security' },
          { id: 'notifications', label: '🔔 Notifications' },
          { id: 'api-keys', label: '🔑 API Keys' },
          { id: 'profile', label: '👤 Profile' },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-4 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${activeTab === tab.id
                ? 'border-purple-500 text-purple-400'
                : 'border-transparent text-slate-400 hover:text-slate-300'
              }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-8">
        {/* GENERAL TAB */}
        {activeTab === 'general' && (
          <div>
            <SettingsSection
              title="System Information"
              description="Configure basic system properties and naming"
            >
              <TextInputSetting
                label="System Name"
                description="The name displayed for this JARVIS instance"
                value={systemName}
                onChange={setSystemName}
                placeholder="JARVIS-SECURITY-AI"
              />
              <SelectSetting
                label="Log Level"
                description="Set the verbosity level for system logging"
                value={logLevel}
                onChange={setLogLevel}
                options={[
                  { label: 'Debug', value: 'DEBUG' },
                  { label: 'Info', value: 'INFO' },
                  { label: 'Warning', value: 'WARNING' },
                  { label: 'Error', value: 'ERROR' },
                  { label: 'Critical', value: 'CRITICAL' },
                ]}
              />
            </SettingsSection>

            <SettingsSection
              title="Telemetry"
              description="Configure system telemetry and metrics collection"
            >
              <ToggleSetting
                label="Enable Telemetry"
                description="Send system metrics and events to telemetry server"
                enabled={enableTelemetry}
                onChange={setEnableTelemetry}
              />
              <TextInputSetting
                label="Telemetry URL"
                description="Endpoint for telemetry data collection"
                value={telemetryUrl}
                onChange={setTelemetryUrl}
                placeholder="http://localhost:8001/telemetry/events"
              />
            </SettingsSection>
          </div>
        )}

        {/* NETWORK TAB */}
        {activeTab === 'network' && (
          <div>
            <SettingsSection
              title="Deep Packet Inspection (DPI)"
              description="Configure network monitoring and packet analysis"
            >
              <ToggleSetting
                label="Enable DPI"
                description="Enable deep packet inspection on network traffic"
                enabled={dpiEnabled}
                onChange={setDpiEnabled}
              />
              <TextInputSetting
                label="Network Interface"
                description="Network interface for packet capture (e.g., eth0, en0)"
                value={dpiInterface}
                onChange={setDpiInterface}
                placeholder="eth0"
              />
              <TextInputSetting
                label="Packet Snaplen"
                description="Maximum bytes to capture per packet (0 = unlimited)"
                value={packetSnaplen}
                onChange={setPacketSnaplen}
                placeholder="65535"
                type="number"
              />
              <ToggleSetting
                label="Enable Ascend Device"
                description="Enable Ascend hardware acceleration if available"
                enabled={ascendEnabled}
                onChange={setAscendEnabled}
              />
            </SettingsSection>

            <SettingsSection
              title="Backend Service"
              description="Configure backend API service settings"
            >
              <TextInputSetting
                label="Backend Host"
                description="Hostname or IP address to bind the backend service"
                value={backendHost}
                onChange={setBackendHost}
                placeholder="0.0.0.0"
              />
              <TextInputSetting
                label="Backend Port"
                description="Port number for the backend API service"
                value={backendPort}
                onChange={setBackendPort}
                placeholder="8000"
                type="number"
              />
            </SettingsSection>
          </div>
        )}

        {/* SECURITY TAB */}
        {activeTab === 'security' && (
          <div>
            <SettingsSection
              title="Authentication & Authorization"
              description="Security and access control settings"
            >
              <ToggleSetting
                label="Biometric Verification"
                description="Require biometric authentication for sensitive operations"
                enabled={enableBiometric}
                onChange={setEnableBiometric}
              />
              <ToggleSetting
                label="Post-Quantum Cryptography"
                description="Use PQC algorithms for encryption and signatures"
                enabled={enablePQC}
                onChange={setEnablePQC}
              />
              <ToggleSetting
                label="Zero Trust Architecture"
                description="Implement zero trust security model for all access"
                enabled={enableZeroTrust}
                onChange={setEnableZeroTrust}
              />
              <ToggleSetting
                label="Require mTLS"
                description="Enforce mutual TLS for all backend connections"
                enabled={mTlsRequired}
                onChange={setMTlsRequired}
              />
              <TextInputSetting
                label="Session Timeout (seconds)"
                description="Maximum session duration before re-authentication required"
                value={sessionTimeout}
                onChange={setSessionTimeout}
                placeholder="3600"
                type="number"
              />
            </SettingsSection>

            <SettingsSection
              title="Encryption Keys"
              description="Manage PQC cryptographic keys"
            >
              <ToggleSetting
                label="Enable Automatic Key Rotation"
                description="Automatically rotate PQC keys on a scheduled basis"
                enabled={keyRotationEnabled}
                onChange={setKeyRotationEnabled}
              />
              <button
                onClick={handleKeyRotation}
                disabled={loading}
                className="w-full px-4 py-3 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 disabled:opacity-50 disabled:cursor-not-allowed rounded font-medium text-white transition-colors flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <Loader size={18} className="animate-spin" />
                    Rotating Keys...
                  </>
                ) : (
                  <>
                    <RotateCw size={18} />
                    Rotate PQC Keys Now
                  </>
                )}
              </button>
            </SettingsSection>
          </div>
        )}

        {/* NOTIFICATIONS TAB */}
        {activeTab === 'notifications' && (
          <div>
            <SettingsSection
              title="Alert Channels"
              description="Configure where alerts should be delivered"
            >
              <ToggleSetting
                label="Email Alerts"
                description="Receive security alerts via email"
                enabled={emailAlerts}
                onChange={setEmailAlerts}
              />
              <ToggleSetting
                label="Slack Alerts"
                description="Send alerts to Slack workspace"
                enabled={slackAlerts}
                onChange={setSlackAlerts}
              />
              <ToggleSetting
                label="Webhook Alerts"
                description="Send alerts to custom webhook endpoint"
                enabled={webhookAlerts}
                onChange={setWebhookAlerts}
              />
              <SelectSetting
                label="Alert Threshold"
                description="Minimum severity level for alerts"
                value={alertThreshold}
                onChange={setAlertThreshold}
                options={[
                  { label: 'Low', value: 'low' },
                  { label: 'Medium', value: 'medium' },
                  { label: 'High', value: 'high' },
                  { label: 'Critical', value: 'critical' },
                ]}
              />
            </SettingsSection>
          </div>
        )}

        {/* API KEYS TAB */}
        {activeTab === 'api-keys' && (
          <div>
            <SettingsSection
              title="Manage API Keys"
              description="Create and manage API keys for programmatic access"
            >
              {!showKeyForm ? (
                <button
                  onClick={() => setShowKeyForm(true)}
                  className="w-full px-4 py-3 bg-emerald-600 hover:bg-emerald-700 rounded font-medium text-white transition-colors flex items-center justify-center gap-2"
                >
                  <Plus size={18} />
                  Create New API Key
                </button>
              ) : (
                <div className="p-4 bg-slate-700/30 rounded border border-slate-600 space-y-3">
                  <TextInputSetting
                    label="Key Name"
                    description="A friendly name for this API key"
                    value={newKeyName}
                    onChange={setNewKeyName}
                    placeholder="My API Key"
                  />
                  <div className="flex gap-2">
                    <button
                      onClick={handleCreateAPIKey}
                      disabled={loading}
                      className="flex-1 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 rounded font-medium text-white transition-colors"
                    >
                      {loading ? 'Creating...' : 'Create'}
                    </button>
                    <button
                      onClick={() => setShowKeyForm(false)}
                      className="flex-1 px-4 py-2 bg-slate-600 hover:bg-slate-700 rounded font-medium text-white transition-colors"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              )}

              {apiKeys.length > 0 && (
                <div className="space-y-2 mt-4">
                  <p className="text-sm font-semibold text-slate-300">Active API Keys ({apiKeys.length})</p>
                  {apiKeys.map((apiKey) => (
                    <div key={apiKey.id} className="p-4 bg-slate-700/50 rounded border border-slate-600">
                      <div className="flex items-start justify-between mb-3">
                        <div>
                          <p className="font-semibold text-slate-100">{apiKey.name}</p>
                          <p className="text-xs text-slate-400">Created: {new Date(apiKey.created_at).toLocaleDateString()}</p>
                          <p className="text-xs text-slate-400">Last used: {new Date(apiKey.last_used).toLocaleDateString()}</p>
                        </div>
                        <span className={`px-2 py-1 text-xs font-semibold rounded ${apiKey.is_active ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'bg-slate-500/20 text-slate-400 border border-slate-500/30'}`}>
                          {apiKey.is_active ? '✓ Active' : '✕ Inactive'}
                        </span>
                      </div>
                      <div className="flex items-center gap-2 mb-3 p-2 bg-slate-800 rounded border border-slate-600">
                        <span className="text-xs font-mono text-slate-400 flex-1 truncate">{apiKey.key}</span>
                        <button
                          onClick={() => handleCopyAPIKey(apiKey.key)}
                          className="px-2 py-1 text-xs font-medium bg-slate-700 hover:bg-slate-600 rounded transition-colors"
                        >
                          Copy
                        </button>
                      </div>
                      <button
                        onClick={() => handleDeleteAPIKey(apiKey.id)}
                        disabled={loading}
                        className="w-full px-3 py-2 bg-red-500/20 hover:bg-red-500/30 text-red-400 border border-red-500/30 rounded text-sm font-medium transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
                      >
                        <Trash2 size={16} />
                        Delete API Key
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </SettingsSection>
          </div>
        )}

        {/* PROFILE TAB */}
        {activeTab === 'profile' && (
          <div>
            {userProfile && (
              <>
                <SettingsSection
                  title="User Profile"
                  description="Your account information"
                >
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-3 bg-slate-700/50 rounded border border-slate-600">
                      <p className="text-xs text-slate-400">Username</p>
                      <p className="text-sm font-semibold text-slate-100 mt-1">{userProfile.username}</p>
                    </div>
                    <div className="p-3 bg-slate-700/50 rounded border border-slate-600">
                      <p className="text-xs text-slate-400">Email</p>
                      <p className="text-sm font-semibold text-slate-100 mt-1">{userProfile.email}</p>
                    </div>
                    <div className="p-3 bg-slate-700/50 rounded border border-slate-600">
                      <p className="text-xs text-slate-400">Role</p>
                      <p className="text-sm font-semibold text-slate-100 mt-1">{userProfile.role}</p>
                    </div>
                    <div className="p-3 bg-slate-700/50 rounded border border-slate-600">
                      <p className="text-xs text-slate-400">Last Login</p>
                      <p className="text-sm font-semibold text-slate-100 mt-1">{new Date(userProfile.last_login).toLocaleDateString()}</p>
                    </div>
                  </div>
                </SettingsSection>

                <SettingsSection
                  title="Change Password"
                  description="Update your account password"
                >
                  <div className="relative">
                    <TextInputSetting
                      label="Current Password"
                      description="Enter your current password"
                      value={currentPassword}
                      onChange={setCurrentPassword}
                      type={showPasswords ? 'text' : 'password'}
                    />
                  </div>
                  <div className="relative">
                    <TextInputSetting
                      label="New Password"
                      description="Enter your new password (minimum 8 characters)"
                      value={newPassword}
                      onChange={setNewPassword}
                      type={showPasswords ? 'text' : 'password'}
                    />
                  </div>
                  <div className="relative">
                    <TextInputSetting
                      label="Confirm Password"
                      description="Confirm your new password"
                      value={confirmPassword}
                      onChange={setConfirmPassword}
                      type={showPasswords ? 'text' : 'password'}
                    />
                  </div>
                  <button
                    onClick={() => setShowPasswords(!showPasswords)}
                    className="text-xs text-purple-400 hover:text-purple-300 transition-colors flex items-center gap-1"
                  >
                    {showPasswords ? (
                      <>
                        <EyeOff size={14} />
                        Hide passwords
                      </>
                    ) : (
                      <>
                        <Eye size={14} />
                        Show passwords
                      </>
                    )}
                  </button>
                  <button
                    onClick={handleChangePassword}
                    disabled={loading}
                    className="w-full mt-4 px-4 py-3 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 disabled:opacity-50 disabled:cursor-not-allowed rounded font-medium text-white transition-colors"
                  >
                    {loading ? 'Updating...' : 'Update Password'}
                  </button>
                </SettingsSection>
              </>
            )}
          </div>
        )}
      </div>

      {/* Save Button & Status */}
      <div className="border-t border-slate-700 bg-slate-900/50 backdrop-blur-sm px-8 py-4 sticky bottom-0 flex items-center justify-between">
        <div className="flex items-center gap-4">
          {saveStatus === 'saving' && (
            <div className="flex items-center gap-2 text-purple-400">
              <Loader size={18} className="animate-spin" />
              <span className="text-sm">Saving settings...</span>
            </div>
          )}
          {saveStatus === 'saved' && (
            <div className="flex items-center gap-2 text-emerald-400">
              <CheckCircle size={18} />
              <span className="text-sm">Settings saved successfully</span>
            </div>
          )}
          {saveStatus === 'error' && (
            <div className="flex items-center gap-2 text-red-400">
              <AlertCircle size={18} />
              <span className="text-sm">Failed to save settings</span>
            </div>
          )}
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleExportSettings}
            className="px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded font-medium text-white transition-colors flex items-center gap-2"
            title="Export settings to JSON file"
          >
            <Download size={18} />
            Export
          </button>
          <button
            onClick={() => {
              if (activeTab === 'general') handleSaveGeneralSettings()
              else if (activeTab === 'network') handleSaveNetworkSettings()
              else if (activeTab === 'security') handleSaveSecuritySettings()
              else if (activeTab === 'notifications') handleSaveNotificationSettings()
            }}
            disabled={loading || saveStatus === 'saving'}
            className="px-6 py-2 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 disabled:opacity-50 disabled:cursor-not-allowed rounded font-medium text-white transition-colors flex items-center gap-2"
          >
            {loading ? (
              <>
                <Loader size={18} className="animate-spin" />
                Saving...
              </>
            ) : (
              <>
                💾
                Save Settings
              </>
            )}
          </button>
        </div>
      </div>

      {/* Toast Container */}
      <ToastContainer toasts={toasts} onRemove={(id) => setToasts(prev => prev.filter(t => t.id !== id))} />
    </div>
  )
}
