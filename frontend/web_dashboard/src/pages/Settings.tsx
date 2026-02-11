import { useState, useEffect } from 'react'
import { AlertCircle, CheckCircle } from 'lucide-react'

// Simple header used on the Settings page (kept local to avoid cross-file deps)
const SettingsHeader = () => (
  <div className="relative overflow-hidden bg-gradient-to-r from-slate-900 via-purple-900/20 to-slate-900 border-b border-slate-700">
    <div className="absolute inset-0 opacity-20">
      <div className="absolute top-0 left-1/4 w-72 h-72 bg-purple-500/8 rounded-full blur-3xl"></div>
      <div className="absolute bottom-0 right-1/4 w-72 h-72 bg-pink-500/8 rounded-full blur-3xl"></div>
    </div>
    <div className="relative p-6">
      <h1 className="text-2xl font-bold text-slate-100">⚙️ System Settings</h1>
      <p className="text-sm text-slate-400 mt-1">Manage system configuration, keys, and feature flags</p>
    </div>
  </div>
)

// Toast notification system
interface Toast {
  id: string
  message: string
  type: 'success' | 'error' | 'info' | 'warning'
}

// Toast Component
interface ToastProps {
  toasts: Toast[]
  onRemove: (id: string) => void
}

const _ToastContainer = ({ toasts, onRemove }: ToastProps) => (
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

void _ToastContainer // intentionally unused in this file; exists for parity with Settings_Advanced

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



export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState('general')
  const [loading, setLoading] = useState(false)
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle')

  // General Settings
  const [systemName, setSystemName] = useState('JARVIS-SECURITY-AI')
  const [enableTelemetry, setEnableTelemetry] = useState(true)
  const [telemetryUrl, setTelemetryUrl] = useState('http://localhost:8001/telemetry/events')
  const [logLevel, setLogLevel] = useState('INFO')

  // Network Settings
  const [dpiInterface, setDpiInterface] = useState('eth0')
  const [packetSnaplen, setPacketSnaplen] = useState('65535')
  const [dpiEnabled, setDpiEnabled] = useState(true)
  const [ascendEnabled, setAscendEnabled] = useState(false)

  // Backend Settings
  const [backendHost, setBackendHost] = useState('0.0.0.0')
  const [backendPort, setBackendPort] = useState('8000')
  const [mTlsRequired, setMTlsRequired] = useState(false)
  const [keyRotationEnabled, setKeyRotationEnabled] = useState(false)

  // Security Settings
  const [enableBiometric, setEnableBiometric] = useState(true)
  const [enablePQC, setEnablePQC] = useState(true)
  const [enableZeroTrust, setEnableZeroTrust] = useState(true)
  const [sessionTimeout, setSessionTimeout] = useState('3600')

  // Load settings from backend on mount
  useEffect(() => {
    const loadSettings = async () => {
      try {
        const response = await fetch('/admin/settings')
        if (response.ok) {
          const settings = await response.json()
          // Map loaded settings to state
          if (settings.telemetry) setEnableTelemetry(settings.telemetry.enabled ?? true)
          if (settings.dpi) {
            setDpiInterface(settings.dpi.interface ?? 'eth0')
            setPacketSnaplen(settings.dpi.snaplen?.toString() ?? '65535')
            setDpiEnabled(settings.dpi.enabled ?? true)
            if (settings.dpi.ascend) setAscendEnabled(settings.dpi.ascend.enabled ?? false)
          }
          if (settings.backend) {
            setBackendHost(settings.backend.host ?? '0.0.0.0')
            setBackendPort(settings.backend.port?.toString() ?? '8000')
          }
        }
      } catch (error) {
        console.error('Failed to load settings:', error)
      }
    }
    loadSettings()
  }, [])

  const handleSave = async () => {
    setLoading(true)
    setSaveStatus('saving')

    const settings = {
      system_name: systemName,
      telemetry: {
        enabled: enableTelemetry,
        url: telemetryUrl,
      },
      dpi: {
        enabled: dpiEnabled,
        interface: dpiInterface,
        snaplen: parseInt(packetSnaplen),
        ascend: {
          enabled: ascendEnabled,
        },
      },
      backend: {
        host: backendHost,
        port: parseInt(backendPort),
      },
      security: {
        enable_biometric: enableBiometric,
        enable_pqc: enablePQC,
        enable_zero_trust: enableZeroTrust,
        session_timeout: parseInt(sessionTimeout),
      },
      mtls_required: mTlsRequired,
      key_rotation_enabled: keyRotationEnabled,
      log_level: logLevel,
      updated_at: new Date().toISOString(),
    }

    try {
      const response = await fetch('/admin/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings),
      })

      if (response.ok) {
        setSaveStatus('saved')
        setTimeout(() => setSaveStatus('idle'), 3000)
      } else {
        setSaveStatus('error')
      }
    } catch (error) {
      console.error('Failed to save settings:', error)
      setSaveStatus('error')
    } finally {
      setLoading(false)
    }
  }

  const handleKeyRotation = async () => {
    setLoading(true)
    try {
      const response = await fetch('/keys/rotate', { method: 'POST' })
      if (response.ok) {
        setSaveStatus('saved')
        setTimeout(() => setSaveStatus('idle'), 3000)
      } else {
        setSaveStatus('error')
      }
    } catch (error) {
      console.error('Failed to rotate keys:', error)
      setSaveStatus('error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="h-full flex flex-col bg-gradient-to-br from-slate-900 via-slate-900 to-slate-800 overflow-y-auto">
      <SettingsHeader />

      {/* Tabs */}
      <div className="border-b border-slate-700 bg-slate-900/30 px-6 flex gap-8 sticky top-0 z-10">
        {[
          { id: 'general', label: '⚙️ General' },
          { id: 'network', label: '🌐 Network' },
          { id: 'backend', label: '🔧 Backend' },
          { id: 'security', label: '🔐 Security' },
          { id: 'advanced', label: '🚀 Advanced' },
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
              />
              <ToggleSetting
                label="Enable Ascend Device"
                description="Enable Ascend hardware acceleration if available"
                enabled={ascendEnabled}
                onChange={setAscendEnabled}
              />
            </SettingsSection>
          </div>
        )}

        {activeTab === 'backend' && (
          <div>
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
              />
              <ToggleSetting
                label="Require mTLS"
                description="Enforce mutual TLS for all backend connections"
                enabled={mTlsRequired}
                onChange={setMTlsRequired}
              />
            </SettingsSection>

            <SettingsSection
              title="Database Connection"
              description="Database and data persistence settings"
            >
              <div className="p-3 bg-slate-700/50 rounded border border-slate-600">
                <p className="text-sm text-slate-300">
                  📊 <span className="font-semibold">Connection Status:</span> <span className="text-emerald-400">Connected</span>
                </p>
                <p className="text-xs text-slate-400 mt-2">PostgreSQL 13.0 (Replicated Ledger)</p>
              </div>
            </SettingsSection>
          </div>
        )}

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
              <TextInputSetting
                label="Session Timeout (seconds)"
                description="Maximum session duration before re-authentication required"
                value={sessionTimeout}
                onChange={setSessionTimeout}
                placeholder="3600"
              />
            </SettingsSection>

            <SettingsSection
              title="Encryption Keys"
              description="Manage PQC cryptographic keys"
            >
              <button
                onClick={handleKeyRotation}
                disabled={loading}
                className="w-full px-4 py-3 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 disabled:opacity-50 disabled:cursor-not-allowed rounded font-medium text-white transition-colors"
              >
                {loading ? '🔄 Rotating Keys...' : '🔄 Rotate PQC Keys'}
              </button>
              <p className="text-xs text-slate-400 text-center mt-2">Generates new cryptographic key material</p>
            </SettingsSection>
          </div>
        )}

        {activeTab === 'advanced' && (
          <div>
            <SettingsSection
              title="Key Rotation Policy"
              description="Automatic key rotation settings"
            >
              <ToggleSetting
                label="Enable Automatic Key Rotation"
                description="Automatically rotate PQC keys on a scheduled basis"
                enabled={keyRotationEnabled}
                onChange={setKeyRotationEnabled}
              />
            </SettingsSection>

            <SettingsSection
              title="Feature Flags"
              description="Experimental and beta features"
            >
              <div className="space-y-3">
                <div className="p-3 bg-slate-700/50 rounded border border-slate-600 flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-slate-100">Federated Learning</p>
                    <p className="text-xs text-slate-400 mt-1">Distributed model training across nodes</p>
                  </div>
                  <span className="px-2 py-1 text-xs font-semibold rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                    ✓ ENABLED
                  </span>
                </div>
                <div className="p-3 bg-slate-700/50 rounded border border-slate-600 flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-slate-100">Self-Healing Automation</p>
                    <p className="text-xs text-slate-400 mt-1">Automatic system recovery and remediation</p>
                  </div>
                  <span className="px-2 py-1 text-xs font-semibold rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                    ✓ ENABLED
                  </span>
                </div>
                <div className="p-3 bg-slate-700/50 rounded border border-slate-600 flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-slate-100">Blockchain Forensics</p>
                    <p className="text-xs text-slate-400 mt-1">Immutable audit trail via blockchain</p>
                  </div>
                  <span className="px-2 py-1 text-xs font-semibold rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                    ✓ ENABLED
                  </span>
                </div>
              </div>
            </SettingsSection>

            <SettingsSection
              title="System Information"
              description="View system and component versions"
            >
              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 bg-slate-700/50 rounded border border-slate-600">
                  <p className="text-xs text-slate-400">JARVIS Version</p>
                  <p className="text-sm font-bold text-slate-100 mt-1">v3.2.1</p>
                </div>
                <div className="p-3 bg-slate-700/50 rounded border border-slate-600">
                  <p className="text-xs text-slate-400">Backend Version</p>
                  <p className="text-sm font-bold text-slate-100 mt-1">v1.8.0</p>
                </div>
                <div className="p-3 bg-slate-700/50 rounded border border-slate-600">
                  <p className="text-xs text-slate-400">Python Runtime</p>
                  <p className="text-sm font-bold text-slate-100 mt-1">3.11.4</p>
                </div>
                <div className="p-3 bg-slate-700/50 rounded border border-slate-600">
                  <p className="text-xs text-slate-400">Uptime</p>
                  <p className="text-sm font-bold text-emerald-400 mt-1">45d 12h 23m</p>
                </div>
              </div>
            </SettingsSection>
          </div>
        )}
      </div>

      {/* Save Button & Status */}
      <div className="border-t border-slate-700 bg-slate-900/50 backdrop-blur-sm px-8 py-4 sticky bottom-0">
        <div className="flex items-center justify-between">
          <div>
            {saveStatus === 'saving' && <p className="text-sm text-purple-400">💾 Saving settings...</p>}
            {saveStatus === 'saved' && <p className="text-sm text-emerald-400">✓ Settings saved successfully</p>}
            {saveStatus === 'error' && <p className="text-sm text-red-400">✗ Failed to save settings</p>}
          </div>
          <button
            onClick={handleSave}
            disabled={loading || saveStatus === 'saving'}
            className="px-6 py-2 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 disabled:opacity-50 disabled:cursor-not-allowed rounded font-medium text-white transition-colors"
          >
            {loading ? '⏳ Saving...' : '💾 Save Settings'}
          </button>
        </div>
      </div>
    </div>
  )
}
