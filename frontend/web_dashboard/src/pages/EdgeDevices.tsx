import { useState, useEffect } from 'react'
import {
  Server,
  Cpu,
  Lock,
  Shield,
  Activity,
  AlertCircle,
  CheckCircle2,
  Zap,
  Network,
  BarChart3,
  Filter,
  Search,
  Power,
  Layers,
  Smartphone,
  Loader,
  X,
} from 'lucide-react'
import AppLayout from '../components/AppLayout'
import './EdgeDevices.css'

// Toast notification interface
interface Toast {
  id: string
  message: string
  type: 'success' | 'error' | 'info'
  duration?: number
}

interface EdgeDevice {
  id: string
  name: string
  platform: 'atlas' | 'hisilicon' | 'unknown'
  status: 'online' | 'offline' | 'degraded'
  cpu_usage: number
  memory_usage: number
  temperature: number
  uptime: number
  last_seen: string
  firmware_version: string
  tee_enabled: boolean
  tpm_attestation: boolean
  location: string
  model: string
  cores: number
  memory_gb: number
}

interface SecurityMetrics {
  total_devices: number
  secure_devices: number
  attestation_success: number
  encryption_enabled: number
  seal_status: string
  device_binding: number
}

interface DeviceHistory {
  timestamp: string
  device_id: string
  cpu_usage: number
  memory_usage: number
  temperature: number
  status: string
}

export default function EdgeDevices() {
  const [devices, setDevices] = useState<EdgeDevice[]>([])
  const [selectedDevice, setSelectedDevice] = useState<EdgeDevice | null>(null)
  const [deviceHistory, setDeviceHistory] = useState<DeviceHistory[]>([])
  const [metrics, setMetrics] = useState<SecurityMetrics>({
    total_devices: 0,
    secure_devices: 0,
    attestation_success: 0,
    encryption_enabled: 0,
    seal_status: 'active',
    device_binding: 0,
  })
  const [viewMode, setViewMode] = useState<'grid' | 'list' | 'security'>('grid')
  const [showFilters, setShowFilters] = useState(false)
  const [filters, setFilters] = useState({
    platform: 'all',
    status: 'all',
    teeEnabled: 'all',
  })
  const [isRemoteCommand, setIsRemoteCommand] = useState(false)

  // New state for UX enhancements
  const [_loadingDeviceId, _setLoadingDeviceId] = useState<string | null>(null)
  const [_isLoadingDevices, setIsLoadingDevices] = useState(false)
  const [toasts, setToasts] = useState<Toast[]>([])

  // Add toast notification
  const addToast = (message: string, type: 'success' | 'error' | 'info' = 'info') => {
    const id = Math.random().toString(36).substr(2, 9)
    setToasts((prev) => [...prev, { id, message, type }])

    // Auto-remove toast after 4 seconds
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id))
    }, 4000)
  }

  // Remove toast manually
  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }

  // Load edge device data
  useEffect(() => {
    loadEdgeDevices()
    const interval = setInterval(loadEdgeDevices, 5000) // Refresh every 5s
    return () => clearInterval(interval)
  }, [])

  const loadEdgeDevices = async () => {
    try {
      setIsLoadingDevices(true)

      // Fetch devices from backend API
      const devicesResponse = await fetch('http://127.0.0.1:8000/api/edge-devices')
      if (!devicesResponse.ok) {
        throw new Error(`Devices API error: ${devicesResponse.status}`)
      }
      const devicesData = await devicesResponse.json()
      setDevices(devicesData.devices)

      // Fetch metrics separately
      try {
        const metricsResponse = await fetch('http://127.0.0.1:8000/api/edge-devices/metrics')
        if (metricsResponse.ok) {
          const metricsData = await metricsResponse.json()
          setMetrics(metricsData.metrics)
        } else {
          // Use metrics from devices response as fallback
          setMetrics(devicesData.metrics)
        }
      } catch (metricsError) {
        console.warn('Failed to fetch metrics separately, using devices metrics:', metricsError)
        setMetrics(devicesData.metrics)
      }

      setIsLoadingDevices(false)
    } catch (error) {
      console.error('Failed to load edge devices from API:', error)
      addToast('Using demo data - Backend unavailable', 'info')
      // Fallback to demo data if API is unavailable
      console.log('Falling back to demo data')
      const demoDevices: EdgeDevice[] = [
        {
          id: 'edge-001',
          name: 'Atlas-500-East',
          platform: 'atlas',
          status: 'online',
          cpu_usage: 45,
          memory_usage: 62,
          temperature: 52,
          uptime: 328,
          last_seen: new Date().toISOString(),
          firmware_version: '2.1.0',
          tee_enabled: true,
          tpm_attestation: true,
          location: 'DataCenter-US-East',
          model: 'Atlas 500',
          cores: 64,
          memory_gb: 256,
        },
        {
          id: 'edge-002',
          name: 'Kunpeng-920-Central',
          platform: 'hisilicon',
          status: 'online',
          cpu_usage: 38,
          memory_usage: 54,
          temperature: 48,
          uptime: 422,
          last_seen: new Date(Date.now() - 30000).toISOString(),
          firmware_version: '1.9.2',
          tee_enabled: true,
          tpm_attestation: true,
          location: 'DataCenter-EU-Central',
          model: 'Kunpeng 920',
          cores: 128,
          memory_gb: 512,
        },
        {
          id: 'edge-003',
          name: 'Atlas-300i-West',
          platform: 'atlas',
          status: 'online',
          cpu_usage: 72,
          memory_usage: 78,
          temperature: 68,
          uptime: 156,
          last_seen: new Date(Date.now() - 60000).toISOString(),
          firmware_version: '2.0.5',
          tee_enabled: true,
          tpm_attestation: true,
          location: 'DataCenter-US-West',
          model: 'Atlas 300i',
          cores: 32,
          memory_gb: 128,
        },
        {
          id: 'edge-004',
          name: 'HiSilicon-Echo-South',
          platform: 'hisilicon',
          status: 'degraded',
          cpu_usage: 89,
          memory_usage: 92,
          temperature: 76,
          uptime: 89,
          last_seen: new Date(Date.now() - 120000).toISOString(),
          firmware_version: '1.8.1',
          tee_enabled: true,
          tpm_attestation: false,
          location: 'DataCenter-APAC-South',
          model: 'HiSilicon Echo',
          cores: 16,
          memory_gb: 64,
        },
      ]

      setDevices(demoDevices)
      setMetrics({
        total_devices: demoDevices.length,
        secure_devices: demoDevices.filter((d) => d.tee_enabled && d.tpm_attestation).length,
        attestation_success: demoDevices.filter((d) => d.tpm_attestation).length,
        encryption_enabled: demoDevices.length,
        seal_status: 'active',
        device_binding: Math.round((demoDevices.filter((d) => d.tee_enabled).length / demoDevices.length) * 100),
      })
    }
  }

  const handleSelectDevice = async (device: EdgeDevice) => {
    setSelectedDevice(device)
    _setLoadingDeviceId(device.id)

    try {
      addToast(`Loading device ${device.name}...`, 'info')

      // Fetch device details and history from backend API
      const response = await fetch(`http://127.0.0.1:8000/api/edge-devices/${device.id}`)

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`)
      }

      const data = await response.json()
      setDeviceHistory(data.history)
      _setLoadingDeviceId(null)
      addToast(`Device ${device.name} loaded successfully!`, 'success')
    } catch (error) {
      console.error('Failed to fetch device history from API:', error)
      addToast(`Failed to load device history - Using demo data`, 'error')
      // Fallback to demo data if API is unavailable
      console.log('Falling back to demo history')
      const demoHistory: DeviceHistory[] = Array.from({ length: 20 }, (_, i) => ({
        timestamp: new Date(Date.now() - i * 30000).toISOString(),
        device_id: device.id,
        cpu_usage: Math.max(5, Math.min(95, device.cpu_usage + (Math.random() - 0.5) * 20)),
        memory_usage: Math.max(5, Math.min(95, device.memory_usage + (Math.random() - 0.5) * 15)),
        temperature: Math.max(20, Math.min(90, device.temperature + (Math.random() - 0.5) * 10)),
        status: device.status,
      }))
      setDeviceHistory(demoHistory.reverse())
      _setLoadingDeviceId(null)
    }
  }

  const handleRemoteCommand = async (deviceId: string, command: string) => {
    try {
      setIsRemoteCommand(true)
      addToast(`Executing ${command}...`, 'info')
      console.log(`Executing ${command} on device:`, deviceId)

      // Execute command via backend API
      const response = await fetch(`http://127.0.0.1:8000/api/edge-devices/${deviceId}/command`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ command }),
      })

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`)
      }

      const result = await response.json()
      console.log('Command executed successfully:', result)
      addToast(`${command} executed successfully!`, 'success')

      // Refresh device data after command execution
      await loadEdgeDevices()
      setIsRemoteCommand(false)
    } catch (error) {
      console.error('Failed to execute command:', error)
      addToast(`Failed to execute ${command} - using demo mode`, 'error')
      // Fallback to simulated execution if API unavailable
      console.log('Falling back to demo execution')
      await new Promise((resolve) => setTimeout(resolve, 1000))
      setIsRemoteCommand(false)
    }
  }

  const handleProvisionDevice = async () => {
    try {
      setIsRemoteCommand(true)
      addToast('Provisioning new device...', 'info')
      console.log('Starting device provisioning')

      // Call backend provision endpoint
      const response = await fetch('http://127.0.0.1:8000/api/edge-devices', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: `EdgeDevice-${Date.now()}`,
          platform: 'atlas',
          model: 'TEE-HPM-001',
          location: 'data-center-1',
        }),
      })

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`)
      }

      const result = await response.json()
      console.log('Device provisioned successfully:', result)
      addToast('Device provisioned successfully!', 'success')

      // Refresh device list after provisioning
      await loadEdgeDevices()
      setIsRemoteCommand(false)
    } catch (error) {
      console.error('Failed to provision device:', error)
      addToast('Failed to provision device - demo mode', 'error')
      // Fallback: simulate provisioning
      console.log('Falling back to demo provisioning')
      await new Promise((resolve) => setTimeout(resolve, 1500))
      setIsRemoteCommand(false)
    }
  }

  const filteredDevices = devices.filter((device) => {
    if (filters.platform !== 'all' && device.platform !== filters.platform) return false
    if (filters.status !== 'all' && device.status !== filters.status) return false
    if (filters.teeEnabled === 'enabled' && !device.tee_enabled) return false
    if (filters.teeEnabled === 'disabled' && device.tee_enabled) return false
    return true
  })

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online':
        return { color: 'text-green-400', bg: 'bg-green-400/10', label: 'Online' }
      case 'offline':
        return { color: 'text-red-400', bg: 'bg-red-400/10', label: 'Offline' }
      case 'degraded':
        return { color: 'text-yellow-400', bg: 'bg-yellow-400/10', label: 'Degraded' }
      default:
        return { color: 'text-slate-400', bg: 'bg-slate-400/10', label: 'Unknown' }
    }
  }

  const getPlatformColor = (platform: string) => {
    switch (platform) {
      case 'atlas':
        return { bg: 'bg-blue-500/20', text: 'text-blue-400', label: 'Ascend/Atlas' }
      case 'hisilicon':
        return { bg: 'bg-purple-500/20', text: 'text-purple-400', label: 'HiSilicon' }
      default:
        return { bg: 'bg-slate-500/20', text: 'text-slate-400', label: 'Unknown' }
    }
  }

  return (
    <AppLayout>
      <div className="h-full overflow-auto bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-blue-400 to-purple-400 mb-2">
                Edge Device Management
              </h1>
              <p className="text-slate-400 flex items-center gap-2">
                <Server className="h-4 w-4" />
                Distributed Trusted Execution Environment Network
              </p>
            </div>
            <button
              onClick={handleProvisionDevice}
              disabled={isRemoteCommand}
              className="px-6 py-3 bg-gradient-to-r from-cyan-500 to-blue-500 text-white rounded-lg font-semibold hover:shadow-lg hover:shadow-cyan-500/50 transition-all flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isRemoteCommand ? (
                <>
                  <Loader className="h-4 w-4 animate-spin" />
                  Provisioning...
                </>
              ) : (
                <>
                  <Zap className="h-4 w-4" />
                  Provision Device
                </>
              )}
            </button>
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-4 backdrop-blur">
              <p className="text-xs text-slate-400 mb-2">Total Devices</p>
              <p className="text-2xl font-bold text-cyan-400">{metrics.total_devices}</p>
              <p className="text-xs text-green-400 mt-1">All operational</p>
            </div>
            <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-4 backdrop-blur">
              <p className="text-xs text-slate-400 mb-2">Secure Devices</p>
              <p className="text-2xl font-bold text-green-400">{metrics.secure_devices}</p>
              <p className="text-xs text-slate-400 mt-1">TEE + TPM enabled</p>
            </div>
            <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-4 backdrop-blur">
              <p className="text-xs text-slate-400 mb-2">Device Binding</p>
              <p className="text-2xl font-bold text-blue-400">{metrics.device_binding}%</p>
              <p className="text-xs text-slate-400 mt-1">TPM attestation active</p>
            </div>
            <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-4 backdrop-blur">
              <p className="text-xs text-slate-400 mb-2">Encryption</p>
              <p className="text-2xl font-bold text-purple-400">{metrics.encryption_enabled}</p>
              <p className="text-xs text-slate-400 mt-1">All devices encrypted</p>
            </div>
          </div>
        </div>

        {/* View Tabs */}
        <div className="flex gap-3 mb-6">
          {[
            { id: 'grid' as const, label: 'Grid View', icon: Layers },
            { id: 'list' as const, label: 'List View', icon: Network },
            { id: 'security' as const, label: 'Security', icon: Shield },
          ].map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setViewMode(id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${viewMode === id
                  ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/50'
                  : 'bg-slate-800/50 text-slate-400 border border-slate-700/50 hover:border-slate-600/50'
                }`}
            >
              <Icon className="h-4 w-4" />
              {label}
            </button>
          ))}
        </div>

        {/* Grid View */}
        {viewMode === 'grid' && (
          <div className="space-y-6">
            {/* Control Bar */}
            <div className="flex gap-3 flex-wrap lg:flex-row lg:items-center justify-between">
              <div className="relative flex-1 min-w-[200px]">
                <Search className="absolute left-3 top-3 h-4 w-4 text-slate-500" />
                <input
                  type="text"
                  placeholder="Search devices..."
                  className="w-full pl-10 pr-4 py-2 bg-slate-800/50 border border-slate-700/50 rounded-lg text-slate-100 placeholder-slate-500 focus:border-cyan-500/50 focus:outline-none"
                />
              </div>
              <button
                onClick={() => setShowFilters(!showFilters)}
                className="flex items-center gap-2 px-4 py-2 bg-slate-800/50 border border-slate-700/50 rounded-lg text-slate-300 hover:bg-slate-700/50 transition-all"
              >
                <Filter className="h-4 w-4" />
                Filters
              </button>
            </div>

            {/* Filters Panel */}
            {showFilters && (
              <div className="bg-slate-800/30 border border-slate-700/50 rounded-lg p-4 backdrop-blur">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="text-xs text-slate-400 mb-2 block">Platform</label>
                    <select
                      title="Filter by platform"
                      value={filters.platform}
                      onChange={(e) => setFilters({ ...filters, platform: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded text-slate-200 text-sm"
                    >
                      <option value="all">All Platforms</option>
                      <option value="atlas">Atlas/Ascend</option>
                      <option value="hisilicon">HiSilicon</option>
                      <option value="unknown">Unknown</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-xs text-slate-400 mb-2 block">Status</label>
                    <select
                      title="Filter by device status"
                      value={filters.status}
                      onChange={(e) => setFilters({ ...filters, status: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded text-slate-200 text-sm"
                    >
                      <option value="all">All Status</option>
                      <option value="online">Online</option>
                      <option value="offline">Offline</option>
                      <option value="degraded">Degraded</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-xs text-slate-400 mb-2 block">TEE Status</label>
                    <select
                      title="Filter by TEE enabled status"
                      value={filters.teeEnabled}
                      onChange={(e) => setFilters({ ...filters, teeEnabled: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded text-slate-200 text-sm"
                    >
                      <option value="all">All Devices</option>
                      <option value="enabled">TEE Enabled</option>
                      <option value="disabled">TEE Disabled</option>
                    </select>
                  </div>
                </div>
              </div>
            )}

            {/* Devices Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {filteredDevices.map((device) => {
                const statusColor = getStatusColor(device.status)
                const platformColor = getPlatformColor(device.platform)

                return (
                  <div
                    key={device.id}
                    onClick={() => handleSelectDevice(device)}
                    className={`bg-slate-800/40 border rounded-lg p-4 backdrop-blur cursor-pointer transition-all hover:border-cyan-500/50 ${selectedDevice?.id === device.id ? 'border-cyan-500/50 ring-2 ring-cyan-500/20' : 'border-slate-700/50'
                      }`}
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <div className={`p-2 rounded-lg ${platformColor.bg}`}>
                          <Smartphone className={`h-4 w-4 ${platformColor.text}`} />
                        </div>
                        <div>
                          <h3 className="font-semibold text-slate-100">{device.name}</h3>
                          <p className="text-xs text-slate-500">{device.id}</p>
                        </div>
                      </div>
                      <div
                        className={`px-2 py-1 rounded text-xs font-semibold ${statusColor.bg} ${statusColor.color}`}
                      >
                        {statusColor.label}
                      </div>
                    </div>

                    {/* Device Info */}
                    <div className="grid grid-cols-2 gap-3 mb-4 text-xs">
                      <div className="bg-slate-700/30 rounded p-2">
                        <span className="text-slate-500">Model</span>
                        <p className="text-slate-300 font-semibold mt-1">{device.model}</p>
                      </div>
                      <div className="bg-slate-700/30 rounded p-2">
                        <span className="text-slate-500">Cores</span>
                        <p className="text-slate-300 font-semibold mt-1">{device.cores}x</p>
                      </div>
                      <div className="bg-slate-700/30 rounded p-2">
                        <span className="text-slate-500">Memory</span>
                        <p className="text-slate-300 font-semibold mt-1">{device.memory_gb}GB</p>
                      </div>
                      <div className="bg-slate-700/30 rounded p-2">
                        <span className="text-slate-500">Uptime</span>
                        <p className="text-slate-300 font-semibold mt-1">{device.uptime}h</p>
                      </div>
                    </div>

                    {/* Metrics */}
                    <div className="space-y-2 mb-4">
                      <div>
                        <div className="flex justify-between items-center mb-1">
                          <span className="text-xs text-slate-400">CPU</span>
                          <span className="text-xs font-semibold text-cyan-400">{device.cpu_usage.toFixed(0)}%</span>
                        </div>
                        <div className="w-full bg-slate-700/50 h-1.5 rounded-full overflow-hidden">
                          <div
                            className="metric-progress-bar h-1.5"
                            style={{ width: `${device.cpu_usage}%` }}
                          />
                        </div>
                      </div>
                      <div>
                        <div className="flex justify-between items-center mb-1">
                          <span className="text-xs text-slate-400">Memory</span>
                          <span className="text-xs font-semibold text-blue-400">{device.memory_usage.toFixed(0)}%</span>
                        </div>
                        <div className="w-full bg-slate-700/50 h-1.5 rounded-full overflow-hidden">
                          <div
                            className="metric-progress-bar h-1.5"
                            style={{ width: `${device.memory_usage}%` }}
                          />
                        </div>
                      </div>
                      <div>
                        <div className="flex justify-between items-center mb-1">
                          <span className="text-xs text-slate-400">Temp</span>
                          <span className={`text-xs font-semibold ${device.temperature > 70 ? 'text-red-400' : 'text-green-400'}`}>
                            {device.temperature}°C
                          </span>
                        </div>
                        <div className="w-full bg-slate-700/50 h-1.5 rounded-full overflow-hidden">
                          <div
                            className={`h-1.5 rounded-full ${device.temperature > 70 ? 'bg-red-500' : 'bg-green-500'}`}
                            style={{ width: `${Math.min(device.temperature / 100, 1) * 100}%` }}
                          />
                        </div>
                      </div>
                    </div>

                    {/* Security Status */}
                    <div className="flex gap-2 mb-4 pb-4 border-b border-slate-700/50">
                      <div className="flex items-center gap-1 text-xs">
                        {device.tee_enabled ? (
                          <CheckCircle2 className="h-3 w-3 text-green-400" />
                        ) : (
                          <AlertCircle className="h-3 w-3 text-yellow-400" />
                        )}
                        <span className="text-slate-400">TEE</span>
                      </div>
                      <div className="flex items-center gap-1 text-xs">
                        {device.tpm_attestation ? (
                          <CheckCircle2 className="h-3 w-3 text-green-400" />
                        ) : (
                          <AlertCircle className="h-3 w-3 text-yellow-400" />
                        )}
                        <span className="text-slate-400">TPM</span>
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex gap-2">
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          handleRemoteCommand(device.id, 'status')
                        }}
                        disabled={isRemoteCommand}
                        className="flex-1 flex items-center justify-center gap-1 px-3 py-2 bg-slate-700/50 text-slate-300 hover:bg-cyan-500/20 hover:text-cyan-400 rounded transition-all text-sm font-medium disabled:opacity-50"
                      >
                        {isRemoteCommand ? (
                          <Loader className="h-3 w-3 animate-spin" />
                        ) : (
                          <Activity className="h-3 w-3" />
                        )}
                        {isRemoteCommand ? 'Loading...' : 'Status'}
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          handleRemoteCommand(device.id, 'reboot')
                        }}
                        disabled={isRemoteCommand}
                        className="flex-1 flex items-center justify-center gap-1 px-3 py-2 bg-slate-700/50 text-slate-300 hover:bg-blue-500/20 hover:text-blue-400 rounded transition-all text-sm font-medium disabled:opacity-50"
                      >
                        {isRemoteCommand ? (
                          <Loader className="h-3 w-3 animate-spin" />
                        ) : (
                          <Power className="h-3 w-3" />
                        )}
                        {isRemoteCommand ? 'Rebooting...' : 'Reboot'}
                      </button>
                    </div>
                  </div>
                )
              })}
            </div>

            {/* Device Detail Panel */}
            {selectedDevice && (
              <div className="bg-slate-800/30 border border-slate-700/50 rounded-lg p-6 backdrop-blur">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
                    <Cpu className="h-5 w-5 text-cyan-400" />
                    {selectedDevice.name} Details
                  </h2>
                  <button
                    onClick={() => setSelectedDevice(null)}
                    className="text-slate-400 hover:text-slate-200"
                  >
                    ✕
                  </button>
                </div>

                {/* Performance Chart Simulation */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
                  <div>
                    <h3 className="text-sm font-semibold text-slate-300 mb-4">CPU Trend</h3>
                    <div className="h-24 flex items-end gap-1">
                      {deviceHistory.map((entry, idx) => (
                        <div
                          key={idx}
                          className="flex-1 bg-gradient-to-t from-cyan-500 to-cyan-400 rounded-t opacity-70"
                          style={{ height: `${Math.min(entry.cpu_usage, 100)}%`, minHeight: '4px' }}
                        />
                      ))}
                    </div>
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-slate-300 mb-4">Memory Trend</h3>
                    <div className="h-24 flex items-end gap-1">
                      {deviceHistory.map((entry, idx) => (
                        <div
                          key={idx}
                          className="flex-1 bg-gradient-to-t from-blue-500 to-blue-400 rounded-t opacity-70"
                          style={{ height: `${Math.min(entry.memory_usage, 100)}%`, minHeight: '4px' }}
                        />
                      ))}
                    </div>
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-slate-300 mb-4">Temperature Trend</h3>
                    <div className="h-24 flex items-end gap-1">
                      {deviceHistory.map((entry, idx) => (
                        <div
                          key={idx}
                          className="flex-1 bg-gradient-to-t from-yellow-500 to-yellow-400 rounded-t opacity-70"
                          style={{ height: `${Math.min(entry.temperature / 100, 1) * 100}%`, minHeight: '4px' }}
                        />
                      ))}
                    </div>
                  </div>
                </div>

                {/* Detailed Specifications */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-6 border-t border-slate-700/50">
                  {[
                    { label: 'Firmware', value: selectedDevice.firmware_version },
                    { label: 'Location', value: selectedDevice.location },
                    { label: 'Cores', value: `${selectedDevice.cores}x` },
                    { label: 'Memory', value: `${selectedDevice.memory_gb}GB` },
                    { label: 'Uptime', value: `${selectedDevice.uptime}h` },
                    { label: 'Platform', value: getPlatformColor(selectedDevice.platform).label },
                    { label: 'TEE', value: selectedDevice.tee_enabled ? 'Enabled' : 'Disabled' },
                    { label: 'TPM', value: selectedDevice.tpm_attestation ? 'Active' : 'Inactive' },
                  ].map((spec) => (
                    <div key={spec.label} className="text-center">
                      <p className="text-xs text-slate-500 mb-1">{spec.label}</p>
                      <p className="text-sm font-bold text-cyan-400">{spec.value}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* List View */}
        {viewMode === 'list' && (
          <div className="space-y-4">
            <h2 className="text-xl font-bold text-slate-100 mb-4 flex items-center gap-2">
              <Network className="h-5 w-5 text-cyan-400" />
              All Edge Devices
            </h2>

            <div className="bg-slate-800/30 border border-slate-700/50 rounded-lg overflow-hidden backdrop-blur">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-slate-700/50 bg-slate-800/50">
                      <th className="px-6 py-3 text-left text-xs font-semibold text-slate-400">Device Name</th>
                      <th className="px-6 py-3 text-left text-xs font-semibold text-slate-400">Platform</th>
                      <th className="px-6 py-3 text-left text-xs font-semibold text-slate-400">Status</th>
                      <th className="px-6 py-3 text-right text-xs font-semibold text-slate-400">CPU</th>
                      <th className="px-6 py-3 text-right text-xs font-semibold text-slate-400">Memory</th>
                      <th className="px-6 py-3 text-right text-xs font-semibold text-slate-400">Temp</th>
                      <th className="px-6 py-3 text-center text-xs font-semibold text-slate-400">Security</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-700/30">
                    {filteredDevices.map((device) => {
                      const statusColor = getStatusColor(device.status)
                      const platformColor = getPlatformColor(device.platform)

                      return (
                        <tr key={device.id} className="hover:bg-slate-700/20 transition-colors">
                          <td className="px-6 py-3">
                            <div className="flex items-center gap-2">
                              <div className={`p-1 rounded ${platformColor.bg}`}>
                                <Smartphone className={`h-3 w-3 ${platformColor.text}`} />
                              </div>
                              <span className="text-sm font-medium text-slate-200">{device.name}</span>
                            </div>
                          </td>
                          <td className="px-6 py-3">
                            <span className="text-sm text-slate-400">{platformColor.label}</span>
                          </td>
                          <td className="px-6 py-3">
                            <span className={`px-2 py-1 rounded text-xs font-semibold ${statusColor.bg} ${statusColor.color}`}>
                              {statusColor.label}
                            </span>
                          </td>
                          <td className="px-6 py-3 text-right">
                            <span className="text-sm text-cyan-400">{device.cpu_usage.toFixed(0)}%</span>
                          </td>
                          <td className="px-6 py-3 text-right">
                            <span className="text-sm text-blue-400">{device.memory_usage.toFixed(0)}%</span>
                          </td>
                          <td className="px-6 py-3 text-right">
                            <span className={`text-sm ${device.temperature > 70 ? 'text-red-400' : 'text-green-400'}`}>
                              {device.temperature}°C
                            </span>
                          </td>
                          <td className="px-6 py-3 text-center">
                            <div className="flex items-center justify-center gap-1">
                              {device.tee_enabled && device.tpm_attestation ? (
                                <CheckCircle2 className="h-4 w-4 text-green-400" />
                              ) : (
                                <AlertCircle className="h-4 w-4 text-yellow-400" />
                              )}
                            </div>
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* Security View */}
        {viewMode === 'security' && (
          <div className="space-y-6">
            <h2 className="text-xl font-bold text-slate-100 mb-4 flex items-center gap-2">
              <Shield className="h-5 w-5 text-green-400" />
              Security Posture
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* TEE & Sealing */}
              <div className="bg-slate-800/30 border border-slate-700/50 rounded-lg p-6 backdrop-blur">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-semibold text-slate-100 flex items-center gap-2">
                    <Lock className="h-4 w-4 text-purple-400" />
                    Trusted Execution Environments
                  </h3>
                  <CheckCircle2 className="h-4 w-4 text-green-400" />
                </div>

                <div className="space-y-3">
                  {[
                    { label: 'Kunpeng TEE (ARM TrustZone)', status: 75 },
                    { label: 'Ascend TEE Integration', status: 100 },
                    { label: 'Key Sealing Active', status: 100 },
                    { label: 'Device Binding', status: 87 },
                  ].map((item) => (
                    <div key={item.label}>
                      <div className="flex justify-between items-center mb-1">
                        <span className="text-sm text-slate-400">{item.label}</span>
                        <span className="text-sm font-semibold text-green-400">{item.status}%</span>
                      </div>
                      <div className="w-full bg-slate-700/50 h-2 rounded-full">
                        <div
                          className="bg-gradient-to-r from-purple-500 to-pink-400 h-2 rounded-full"
                          style={{ width: `${item.status}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* TPM & Attestation */}
              <div className="bg-slate-800/30 border border-slate-700/50 rounded-lg p-6 backdrop-blur">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-semibold text-slate-100 flex items-center gap-2">
                    <Shield className="h-4 w-4 text-blue-400" />
                    TPM & Attestation
                  </h3>
                  <CheckCircle2 className="h-4 w-4 text-green-400" />
                </div>

                <div className="space-y-3">
                  {[
                    { label: 'TPM 2.0 Availability', status: 100 },
                    { label: 'PCR Measurement', status: 94 },
                    { label: 'Device Attestation', status: 92 },
                    { label: 'Secure Boot', status: 100 },
                  ].map((item) => (
                    <div key={item.label}>
                      <div className="flex justify-between items-center mb-1">
                        <span className="text-sm text-slate-400">{item.label}</span>
                        <span className="text-sm font-semibold text-blue-400">{item.status}%</span>
                      </div>
                      <div className="w-full bg-slate-700/50 h-2 rounded-full">
                        <div
                          className="bg-gradient-to-r from-blue-500 to-cyan-400 h-2 rounded-full"
                          style={{ width: `${item.status}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Encryption & Privacy */}
              <div className="bg-slate-800/30 border border-slate-700/50 rounded-lg p-6 backdrop-blur">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-semibold text-slate-100 flex items-center gap-2">
                    <Lock className="h-4 w-4 text-cyan-400" />
                    Encryption & Privacy
                  </h3>
                </div>

                <div className="space-y-3">
                  {[
                    { label: 'At-Rest Encryption', status: 100 },
                    { label: 'In-Transit TLS', status: 100 },
                    { label: 'Key Rotation', status: 98 },
                    { label: 'Privacy Compliance', status: 100 },
                  ].map((item) => (
                    <div key={item.label}>
                      <div className="flex justify-between items-center mb-1">
                        <span className="text-sm text-slate-400">{item.label}</span>
                        <span className="text-sm font-semibold text-green-400">{item.status}%</span>
                      </div>
                      <div className="w-full bg-slate-700/50 h-2 rounded-full">
                        <div
                          className="bg-gradient-to-r from-green-500 to-emerald-400 h-2 rounded-full"
                          style={{ width: `${item.status}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Platform Compliance */}
              <div className="bg-slate-800/30 border border-slate-700/50 rounded-lg p-6 backdrop-blur">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-semibold text-slate-100 flex items-center gap-2">
                    <BarChart3 className="h-4 w-4 text-yellow-400" />
                    Platform Compliance
                  </h3>
                </div>

                <div className="space-y-3">
                  {[
                    { label: 'HuaweiCloud Certified', status: 100 },
                    { label: 'OpenEnclave Compatible', status: 95 },
                    { label: 'Hardware Hardening', status: 98 },
                    { label: 'Patch Level', status: 96 },
                  ].map((item) => (
                    <div key={item.label}>
                      <div className="flex justify-between items-center mb-1">
                        <span className="text-sm text-slate-400">{item.label}</span>
                        <span className="text-sm font-semibold text-yellow-400">{item.status}%</span>
                      </div>
                      <div className="w-full bg-slate-700/50 h-2 rounded-full">
                        <div
                          className="bg-gradient-to-r from-yellow-500 to-amber-400 h-2 rounded-full"
                          style={{ width: `${item.status}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Toast Notifications Container */}
        <div className="fixed top-4 right-4 z-50 space-y-2 pointer-events-none">
          {toasts.map((toast) => (
            <div
              key={toast.id}
              className={`
              animate-in fade-in slide-in-from-top-2 pointer-events-auto
              rounded-lg px-4 py-3 shadow-lg flex items-center gap-3 max-w-sm
              ${toast.type === 'success'
                  ? 'bg-green-500 text-white'
                  : toast.type === 'error'
                    ? 'bg-red-500 text-white'
                    : 'bg-blue-500 text-white'
                }
            `}
            >
              <span className="flex-1 text-sm font-medium">{toast.message}</span>
              <button
                onClick={() => removeToast(toast.id)}
                className="hover:bg-white/20 p-1 rounded transition-colors"
                title="Close notification"
              >
                <X size={18} />
              </button>
            </div>
          ))}
        </div>
      </div>
    </AppLayout>
  )
}
