import { useState, useEffect } from 'react'
import axios from 'axios'
import DPIRuleManager from '../components/DPIRuleManager'

const API_BASE = 'http://localhost:8000/packet_capture'
const DPI_API_BASE = 'http://localhost:8000/dpi'
const _THREAT_INTEL_API = 'http://localhost:8000/threat-intel'
const _ANALYTICS_API = 'http://localhost:8000/analytics'
void _THREAT_INTEL_API
void _ANALYTICS_API

const PageHeader = () => (
  <div className="relative overflow-hidden bg-gradient-to-r from-slate-900 via-blue-900/20 to-slate-900 border-b border-slate-700">
    <div className="absolute inset-0 opacity-30">
      <div className="absolute top-0 left-1/4 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl"></div>
      <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl"></div>
    </div>
    <div className="relative p-8">
      <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent">
        🛡️ Network Security Dashboard
      </h1>
      <p className="text-slate-400 mt-2">Real-time threat detection and network monitoring with packet capture</p>
    </div>
  </div>
)

interface PacketCaptureStatus {
  running: boolean
  interface: string
  backend: string
  packets_captured: number
  packets_dropped: number
  uptime_sec: number
  buffer_usage_percent: number
}

interface CaptureMetrics {
  throughput_mbps: number
  packets_per_sec: number
  avg_packet_size: number
  drop_rate_percent: number
  buffer_usage_percent: number
  active_flows: number
}

interface DPIAlert {
  alert_id: number
  severity: string
  protocol: string
  rule_id: number
  rule_name: string
  message: string
  flow: [string, number, string, number]
  timestamp: number
}

interface DPIStatistics {
  packets_processed: number
  bytes_processed: number
  flows_created: number
  active_sessions: number
  alerts_generated: number
  anomalies_detected: number
  http_packets: number
  dns_packets: number
  tls_packets: number
  smtp_packets: number
  smb_packets: number
  avg_processing_time_us: number
}

interface AnomalyDetection {
  anomaly_id: string
  type: string
  confidence: number
  detected_at: string
  affected_ips: string[]
  risk_score: number
  description: string
}

interface ThreatIntelData {
  indicator: string
  type: string
  threat_level: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW'
  source: string
  last_seen: string
  confidence: number
  attributes: Record<string, any>
}

interface NetworkMetricCardProps {
  label: string
  value: string
  icon: string
  color: string
  trend?: string
}

const NetworkMetricCard = ({ label, value, icon, color, trend }: NetworkMetricCardProps) => {
  const colorClass: Record<string, string> = {
    blue: 'from-blue-500/20 to-blue-500/5 border-blue-500/30',
    indigo: 'from-indigo-500/20 to-indigo-500/5 border-indigo-500/30',
    cyan: 'from-cyan-500/20 to-cyan-500/5 border-cyan-500/30',
    red: 'from-red-500/20 to-red-500/5 border-red-500/30',
    emerald: 'from-emerald-500/20 to-emerald-500/5 border-emerald-500/30',
  }

  return (
    <div className={`bg-gradient-to-br ${colorClass[color] || 'from-slate-700/50 to-slate-800/50 border-slate-600'} border rounded-lg p-4`}>
      <div className="text-2xl mb-2">{icon}</div>
      <p className="text-slate-400 text-xs font-medium uppercase">{label}</p>
      <p className="text-2xl font-bold text-slate-100 mt-1">{value}</p>
      {trend && <p className={`text-xs mt-2 ${trend.includes('↓') ? 'text-emerald-400' : 'text-orange-400'}`}>{trend}</p>}
    </div>
  )
}

const NetworkMetricsGrid = () => (
  <div className="grid grid-cols-6 gap-4 p-6 bg-slate-900/50">
    <NetworkMetricCard label="Packet Loss" value="0.02%" icon="📦" color="emerald" trend="↓ 15% from last hour" />
    <NetworkMetricCard label="Latency" value="12ms" icon="⏱️" color="blue" trend="↑ 2ms increase" />
    <NetworkMetricCard label="Active Flows" value="8.4K" icon="🌊" color="cyan" trend="↑ 340 new" />
    <NetworkMetricCard label="Threats Detected" value="47" icon="🚨" color="red" trend="↑ 8 this hour" />
    <NetworkMetricCard label="Blocked IPs" value="312" icon="🔒" color="indigo" trend="↑ 23 today" />
    <NetworkMetricCard label="Uptime" value="99.97%" icon="✓" color="emerald" trend="↑ +0.03%" />
  </div>
)

const ThreatMap = () => (
  <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 m-6">
    <h3 className="text-lg font-semibold text-slate-100 mb-4">🗺️ Global Threat Distribution</h3>
    <div className="space-y-3">
      {[
        { region: 'Asia-Pacific', threats: 23, severity: 'HIGH', color: 'bg-red-500/20 text-red-400 border-red-500/30' },
        { region: 'Europe', threats: 15, severity: 'MEDIUM', color: 'bg-orange-500/20 text-orange-400 border-orange-500/30' },
        { region: 'North America', threats: 8, severity: 'MEDIUM', color: 'bg-orange-500/20 text-orange-400 border-orange-500/30' },
        { region: 'South America', threats: 3, severity: 'LOW', color: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30' },
        { region: 'Africa', threats: 2, severity: 'LOW', color: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30' },
      ].map((item, i) => (
        <div key={i} className="bg-slate-700/50 rounded p-4 border border-slate-600">
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <p className="font-semibold text-slate-100">{item.region}</p>
              <p className="text-xs text-slate-400 mt-1">{item.threats} detected threats</p>
            </div>
            <div className="flex gap-2 items-center">
              <div className="w-32 bg-slate-600 rounded-full h-2">
                <div className="bg-red-500 h-2 rounded-full w-[45%]"></div>
              </div>
              <span className={`px-2 py-1 text-xs font-semibold rounded border ${item.color}`}>
                {item.severity}
              </span>
            </div>
          </div>
        </div>
      ))}
    </div>
  </div>
)

const NetworkTopology = () => (
  <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 m-6">
    <h3 className="text-lg font-semibold text-slate-100 mb-4">🔗 Network Topology</h3>
    <div className="space-y-3">
      {[
        { name: 'Core Router', status: 'HEALTHY', ips: 512, health: 98 },
        { name: 'Firewall Primary', status: 'HEALTHY', ips: 1024, health: 99 },
        { name: 'Firewall Secondary', status: 'MONITORING', ips: 768, health: 92 },
        { name: 'IDS/IPS Engine', status: 'HEALTHY', ips: 256, health: 97 },
        { name: 'VPN Gateway', status: 'HEALTHY', ips: 384, health: 95 },
      ].map((device, i) => (
        <div key={i} className="bg-slate-700/50 rounded p-4 border border-slate-600">
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full ${device.status === 'HEALTHY' ? 'bg-emerald-500' : 'bg-yellow-500'}`}></div>
                <p className="font-semibold text-slate-100">{device.name}</p>
              </div>
              <p className="text-xs text-slate-400 mt-1">Connected IPs: {device.ips}</p>
            </div>
            <div className="text-right">
              <p className="text-sm font-bold text-blue-400">{device.health}%</p>
              <div className="w-24 bg-slate-600 rounded-full h-2 mt-1">
                <div className="bg-blue-500 h-2 rounded-full w-[98%]"></div>
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  </div>
)

const ProtocolAnalysis = () => (
  <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 m-6">
    <h3 className="text-lg font-semibold text-slate-100 mb-4">📊 Protocol Analysis</h3>
    <div className="space-y-2">
      {[
        { protocol: 'TCP', percentage: 45, icon: '🔵', colorWidth: 'w-[45%]', color: 'bg-blue-500' },
        { protocol: 'UDP', percentage: 35, icon: '🟣', colorWidth: 'w-[35%]', color: 'bg-purple-500' },
        { protocol: 'ICMP', percentage: 12, icon: '🟠', colorWidth: 'w-[12%]', color: 'bg-orange-500' },
        { protocol: 'Other', percentage: 8, icon: '⚫', colorWidth: 'w-[8%]', color: 'bg-gray-500' },
      ].map((item, i) => (
        <div key={i} className="flex items-center gap-3">
          <span className="text-lg">{item.icon}</span>
          <span className="w-16 text-sm font-medium text-slate-300">{item.protocol}</span>
          <div className="flex-1 bg-slate-700 rounded-full h-2">
            <div className={`${item.color} h-2 rounded-full ${item.colorWidth}`}></div>
          </div>
          <span className="text-sm font-bold text-slate-300 w-12 text-right">{item.percentage}%</span>
        </div>
      ))}
    </div>
  </div>
)

const RecentAlerts = () => (
  <div className="p-6">
    <h3 className="text-lg font-semibold text-slate-100 mb-4">🔔 Recent Alerts</h3>
    <div className="space-y-3">
      {[
        { time: '2 min ago', alert: 'Suspicious port scanning detected from 192.168.1.105', severity: 'HIGH' },
        { time: '5 min ago', alert: 'Multiple failed login attempts on SSH server', severity: 'MEDIUM' },
        { time: '12 min ago', alert: 'DDoS mitigation triggered for incoming traffic spike', severity: 'HIGH' },
        { time: '18 min ago', alert: 'Certificate expiry warning for domain jarvis.internal', severity: 'LOW' },
        { time: '24 min ago', alert: 'Unauthorized access attempt blocked by firewall', severity: 'MEDIUM' },
      ].map((item, i) => (
        <div key={i} className="bg-slate-800 border border-slate-700 rounded-lg p-4 hover:border-blue-500/50 transition-colors">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <p className="text-sm text-slate-300">{item.alert}</p>
              <p className="text-xs text-slate-500 mt-2">{item.time}</p>
            </div>
            <span className={`px-2 py-1 text-xs font-semibold rounded border whitespace-nowrap ml-4 ${item.severity === 'HIGH' ? 'bg-red-500/20 text-red-400 border-red-500/30' :
              item.severity === 'MEDIUM' ? 'bg-orange-500/20 text-orange-400 border-orange-500/30' :
                'bg-yellow-500/20 text-yellow-400 border-yellow-500/30'
              }`}>
              {item.severity}
            </span>
          </div>
        </div>
      ))}
    </div>
  </div>
)

const BandwidthMonitoring = () => (
  <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 m-6">
    <h3 className="text-lg font-semibold text-slate-100 mb-4">📈 Bandwidth Monitoring</h3>
    <div className="space-y-4">
      {[
        { interface: 'eth0 (WAN)', inbound: 2.4, outbound: 1.8, limit: 10, widthClass: 'w-[24%]' },
        { interface: 'eth1 (Internal)', inbound: 3.2, outbound: 2.9, limit: 10, widthClass: 'w-[32%]' },
        { interface: 'eth2 (DMZ)', inbound: 0.8, outbound: 0.6, limit: 5, widthClass: 'w-[16%]' },
        { interface: 'Backup Link', inbound: 0.2, outbound: 0.1, limit: 2, widthClass: 'w-[10%]' },
      ].map((item, i) => (
        <div key={i}>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-semibold text-slate-300">{item.interface}</span>
            <span className="text-xs text-slate-400">↓ {item.inbound}Gbps ↑ {item.outbound}Gbps / {item.limit}Gbps</span>
          </div>
          <div className="bg-slate-700 rounded-full h-3 overflow-hidden">
            <div className={`bg-gradient-to-r from-blue-500 to-indigo-500 h-3 ${item.widthClass}`}></div>
          </div>
        </div>
      ))}
    </div>
  </div>
)

const PacketCapturePanel = () => {
  const [isCapturing, setIsCapturing] = useState(false)
  const [status, setStatus] = useState<PacketCaptureStatus | null>(null)
  const [metrics, setMetrics] = useState<CaptureMetrics | null>(null)
  const [selectedInterface, setSelectedInterface] = useState('eth0')
  const [flowMeteringEnabled, setFlowMeteringEnabled] = useState(false)
  const [netflowEnabled, setNetflowEnabled] = useState(false)
  const [encryptionEnabled, setEncryptionEnabled] = useState(false)
  const [loading, setLoading] = useState(false)

  const startCapture = async () => {
    setLoading(true)
    try {
      await axios.post(`${API_BASE}/capture/start`, {
        interface: selectedInterface,
        backend: 'pcap',
        buffer_size_mb: 256,
      })
      setIsCapturing(true)
    } catch (error) {
      console.error('Failed to start capture:', error)
    } finally {
      setLoading(false)
    }
  }

  const stopCapture = async () => {
    setLoading(true)
    try {
      await axios.post(`${API_BASE}/capture/stop`, { reason: 'manual' })
      setIsCapturing(false)
      setFlowMeteringEnabled(false)
      setNetflowEnabled(false)
      setEncryptionEnabled(false)
    } catch (error) {
      console.error('Failed to stop capture:', error)
    } finally {
      setLoading(false)
    }
  }

  const toggleFlowMetering = async () => {
    try {
      await axios.post(`${API_BASE}/capture/flow/meter/enable`, {
        enable: !flowMeteringEnabled,
        flow_timeout_sec: 300,
      })
      setFlowMeteringEnabled(!flowMeteringEnabled)
    } catch (error) {
      console.error('Failed to toggle flow metering:', error)
    }
  }

  const toggleNetflow = async () => {
    try {
      await axios.post(`${API_BASE}/capture/netflow/export/enable`, {
        collector_ip: '127.0.0.1',
        collector_port: 9995,
        export_interval_sec: 60,
      })
      setNetflowEnabled(!netflowEnabled)
    } catch (error) {
      console.error('Failed to toggle NetFlow:', error)
    }
  }

  const toggleEncryption = async () => {
    try {
      await axios.post(`${API_BASE}/capture/encryption/enable`, {
        cipher_suite: 'AES-256-GCM',
        key_file: '/etc/jarvis/capture.key',
      })
      setEncryptionEnabled(!encryptionEnabled)
    } catch (error) {
      console.error('Failed to toggle encryption:', error)
    }
  }

  useEffect(() => {
    let interval: NodeJS.Timeout | null = null

    if (isCapturing) {
      const fetchStatus = async () => {
        try {
          const [statusRes, metricsRes] = await Promise.all([
            axios.get(`${API_BASE}/capture/status`),
            axios.get(`${API_BASE}/capture/metrics`),
          ])
          setStatus(statusRes.data)
          setMetrics(metricsRes.data)
        } catch (error) {
          console.error('Failed to fetch status:', error)
        }
      }

      fetchStatus()
      interval = setInterval(fetchStatus, 2000)
    }

    return () => {
      if (interval) clearInterval(interval)
    }
  }, [isCapturing])

  return (
    <div className="p-6 space-y-6">
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-slate-100 mb-4">🎯 Packet Capture Control</h3>

        {/* Capture Controls */}
        <div className="bg-slate-700/50 rounded-lg p-4 mb-4">
          <div className="flex items-center justify-between mb-4">
            <div>
              <p className="text-sm text-slate-300 font-medium">Capture Status</p>
              <p className={`text-2xl font-bold mt-1 ${isCapturing ? 'text-emerald-400' : 'text-slate-400'}`}>
                {isCapturing ? '🔴 CAPTURING' : '⚫ INACTIVE'}
              </p>
            </div>
            <button
              onClick={isCapturing ? stopCapture : startCapture}
              disabled={loading}
              className={`px-6 py-3 rounded-lg font-semibold transition-all ${isCapturing
                ? 'bg-red-500/20 text-red-400 border border-red-500/30 hover:bg-red-500/30'
                : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 hover:bg-emerald-500/30'
                } disabled:opacity-50`}
            >
              {loading ? '...' : isCapturing ? '⏹ Stop Capture' : '▶ Start Capture'}
            </button>
          </div>

          {isCapturing && status && (
            <div className="grid grid-cols-4 gap-3 text-sm">
              <div className="bg-slate-600/50 rounded p-2">
                <p className="text-slate-400">Interface</p>
                <p className="text-blue-400 font-semibold">{status.interface}</p>
              </div>
              <div className="bg-slate-600/50 rounded p-2">
                <p className="text-slate-400">Backend</p>
                <p className="text-cyan-400 font-semibold">{status.backend}</p>
              </div>
              <div className="bg-slate-600/50 rounded p-2">
                <p className="text-slate-400">Packets</p>
                <p className="text-emerald-400 font-semibold">{status.packets_captured.toLocaleString()}</p>
              </div>
              <div className="bg-slate-600/50 rounded p-2">
                <p className="text-slate-400">Dropped</p>
                <p className={`font-semibold ${status.packets_dropped > 0 ? 'text-orange-400' : 'text-emerald-400'}`}>
                  {status.packets_dropped}
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Interface Selection */}
        <div className="mb-4">
          <label className="text-sm text-slate-300 font-medium block mb-2">Network Interface</label>
          <select
            value={selectedInterface}
            onChange={(e) => setSelectedInterface(e.target.value)}
            disabled={isCapturing}
            className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-slate-100 disabled:opacity-50"
          >
            <option>eth0</option>
            <option>eth1</option>
            <option>en0</option>
            <option>en1</option>
            <option>any</option>
          </select>
        </div>

        {/* Advanced Features */}
        <div className="space-y-2">
          <p className="text-sm text-slate-300 font-medium">Advanced Features</p>
          {[
            { enabled: flowMeteringEnabled, toggle: toggleFlowMetering, label: '🔄 Flow Metering', icon: '📊' },
            { enabled: netflowEnabled, toggle: toggleNetflow, label: '📡 NetFlow Export', icon: '📤' },
            { enabled: encryptionEnabled, toggle: toggleEncryption, label: '🔐 Buffer Encryption', icon: '🔒' },
          ].map((feature, i) => (
            <button
              key={i}
              onClick={feature.toggle}
              disabled={!isCapturing || loading}
              className={`w-full flex items-center justify-between p-3 rounded border transition-all ${feature.enabled
                ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
                : 'bg-slate-700/50 text-slate-300 border-slate-600 hover:border-slate-500'
                } disabled:opacity-50`}
            >
              <span>{feature.label}</span>
              <span className={`text-lg ${feature.enabled ? 'opacity-100' : 'opacity-50'}`}>{feature.icon}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Live Metrics */}
      {isCapturing && metrics && (
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-slate-100 mb-4">📊 Live Capture Metrics</h3>
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-slate-700/50 rounded p-3">
              <p className="text-slate-400 text-sm">Throughput</p>
              <p className="text-2xl font-bold text-blue-400">{metrics.throughput_mbps.toFixed(2)} Mbps</p>
            </div>
            <div className="bg-slate-700/50 rounded p-3">
              <p className="text-slate-400 text-sm">Packets/sec</p>
              <p className="text-2xl font-bold text-cyan-400">{metrics.packets_per_sec.toLocaleString()}</p>
            </div>
            <div className="bg-slate-700/50 rounded p-3">
              <p className="text-slate-400 text-sm">Active Flows</p>
              <p className="text-2xl font-bold text-emerald-400">{metrics.active_flows}</p>
            </div>
            <div className="bg-slate-700/50 rounded p-3">
              <p className="text-slate-400 text-sm">Drop Rate</p>
              <p className={`text-2xl font-bold ${metrics.drop_rate_percent > 1 ? 'text-orange-400' : 'text-emerald-400'}`}>
                {metrics.drop_rate_percent.toFixed(2)}%
              </p>
            </div>
            <div className="bg-slate-700/50 rounded p-3">
              <p className="text-slate-400 text-sm">Avg Packet Size</p>
              <p className="text-2xl font-bold text-indigo-400">{metrics.avg_packet_size.toFixed(0)} B</p>
            </div>
            <div className="bg-slate-700/50 rounded p-3">
              <p className="text-slate-400 text-sm">Buffer Usage</p>
              <div className="flex items-center gap-2 mt-2">
                <div className="flex-1 bg-slate-600 rounded-full h-2">
                  <div
                    className="bg-gradient-to-r from-blue-500 to-indigo-500 h-2 rounded-full"
                    style={{ width: `${metrics.buffer_usage_percent}%` }}
                  ></div>
                </div>
                <span className="text-sm font-bold text-slate-100">{metrics.buffer_usage_percent.toFixed(1)}%</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

const DPIEnginePanel = () => {
  const [stats, setStats] = useState<DPIStatistics | null>(null)
  const [alerts, setAlerts] = useState<DPIAlert[]>([])
  const [loading, setLoading] = useState(false)
  const [autoRefresh, setAutoRefresh] = useState(true)

  useEffect(() => {
    if (!autoRefresh) return

    const interval = setInterval(async () => {
      setLoading(true)
      try {
        const [statsRes, alertsRes] = await Promise.all([
          axios.get(`${DPI_API_BASE}/statistics`),
          axios.get(`${DPI_API_BASE}/alerts?max_alerts=50`),
        ])
        setStats(statsRes.data)
        setAlerts(alertsRes.data.alerts || [])
      } catch (error) {
        console.error('Failed to fetch DPI data:', error)
      } finally {
        setLoading(false)
      }
    }, 2000)

    return () => clearInterval(interval)
  }, [autoRefresh])

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'CRITICAL':
        return 'bg-red-500/20 text-red-400 border-red-500/30'
      case 'WARNING':
        return 'bg-orange-500/20 text-orange-400 border-orange-500/30'
      case 'MALWARE':
        return 'bg-rose-500/20 text-rose-400 border-rose-500/30'
      case 'ANOMALY':
        return 'bg-amber-500/20 text-amber-400 border-amber-500/30'
      default:
        return 'bg-blue-500/20 text-blue-400 border-blue-500/30'
    }
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-100">🔍 Deep Packet Inspection Engine</h2>
          <p className="text-slate-400 text-sm mt-1">Real-time protocol analysis, threat detection, and traffic classification</p>
        </div>
        <button
          onClick={() => setAutoRefresh(!autoRefresh)}
          className={`px-4 py-2 rounded border transition-all ${autoRefresh
            ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
            : 'bg-slate-700/50 text-slate-300 border-slate-600'
            }`}
        >
          {autoRefresh ? '⏸ Auto-refresh ON' : '▶ Auto-refresh OFF'}
        </button>
      </div>

      {/* Statistics Grid */}
      {stats && (
        <div className="grid grid-cols-4 gap-4">
          <div className="bg-blue-500/20 border border-blue-500/30 rounded-lg p-4">
            <p className="text-blue-400 text-sm font-medium">Packets Processed</p>
            <p className="text-2xl font-bold text-blue-300 mt-2">{(stats.packets_processed / 1000000).toFixed(1)}M</p>
            <p className="text-xs text-blue-400/60 mt-1">{stats.bytes_processed} bytes</p>
          </div>
          <div className="bg-emerald-500/20 border border-emerald-500/30 rounded-lg p-4">
            <p className="text-emerald-400 text-sm font-medium">Active Sessions</p>
            <p className="text-2xl font-bold text-emerald-300 mt-2">{stats.active_sessions.toLocaleString()}</p>
            <p className="text-xs text-emerald-400/60 mt-1">{stats.flows_created} flows created</p>
          </div>
          <div className="bg-red-500/20 border border-red-500/30 rounded-lg p-4">
            <p className="text-red-400 text-sm font-medium">Alerts Generated</p>
            <p className="text-2xl font-bold text-red-300 mt-2">{stats.alerts_generated}</p>
            <p className="text-xs text-red-400/60 mt-1">{stats.anomalies_detected} anomalies</p>
          </div>
          <div className="bg-indigo-500/20 border border-indigo-500/30 rounded-lg p-4">
            <p className="text-indigo-400 text-sm font-medium">Avg Processing</p>
            <p className="text-2xl font-bold text-indigo-300 mt-2">{stats.avg_processing_time_us.toFixed(2)}µs</p>
            <p className="text-xs text-indigo-400/60 mt-1">per packet</p>
          </div>
        </div>
      )}

      {/* Protocol Breakdown */}
      {stats && (
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-slate-100 mb-4">📊 Protocol Distribution</h3>
          <div className="grid grid-cols-5 gap-4">
            <div className="bg-slate-700/50 rounded p-3 text-center">
              <p className="text-slate-400 text-sm">HTTP</p>
              <p className="text-xl font-bold text-cyan-400 mt-1">{stats.http_packets.toLocaleString()}</p>
              <p className="text-xs text-slate-500 mt-1">packets</p>
            </div>
            <div className="bg-slate-700/50 rounded p-3 text-center">
              <p className="text-slate-400 text-sm">DNS</p>
              <p className="text-xl font-bold text-emerald-400 mt-1">{stats.dns_packets.toLocaleString()}</p>
              <p className="text-xs text-slate-500 mt-1">packets</p>
            </div>
            <div className="bg-slate-700/50 rounded p-3 text-center">
              <p className="text-slate-400 text-sm">TLS/HTTPS</p>
              <p className="text-xl font-bold text-blue-400 mt-1">{stats.tls_packets.toLocaleString()}</p>
              <p className="text-xs text-slate-500 mt-1">packets</p>
            </div>
            <div className="bg-slate-700/50 rounded p-3 text-center">
              <p className="text-slate-400 text-sm">SMTP</p>
              <p className="text-xl font-bold text-orange-400 mt-1">{stats.smtp_packets.toLocaleString()}</p>
              <p className="text-xs text-slate-500 mt-1">packets</p>
            </div>
            <div className="bg-slate-700/50 rounded p-3 text-center">
              <p className="text-slate-400 text-sm">SMB</p>
              <p className="text-xl font-bold text-purple-400 mt-1">{stats.smb_packets.toLocaleString()}</p>
              <p className="text-xs text-slate-500 mt-1">packets</p>
            </div>
          </div>
        </div>
      )}

      {/* Recent Alerts */}
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-slate-100 mb-4">🚨 Recent DPI Alerts</h3>
        {alerts.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-slate-400">No alerts generated yet</p>
            <p className="text-slate-500 text-sm mt-1">System is monitoring traffic...</p>
          </div>
        ) : (
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {alerts.slice(0, 20).map((alert) => (
              <div
                key={alert.alert_id}
                className={`border rounded-lg p-4 ${getSeverityColor(alert.severity)}`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <p className="font-semibold text-sm">{alert.rule_name}</p>
                    <p className="text-xs mt-1 opacity-90">{alert.message}</p>
                    <p className="text-xs mt-2 opacity-75">
                      {alert.protocol} • {alert.flow[0]}:{alert.flow[1]} → {alert.flow[2]}:{alert.flow[3]}
                    </p>
                  </div>
                  <span className="text-xs font-mono text-slate-300 ml-4">Rule #{alert.rule_id}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Loading State */}
      {loading && (
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-4 text-center">
          <p className="text-slate-400 text-sm">🔄 Fetching latest DPI data...</p>
        </div>
      )}
    </div>
  )
}

const ThreatHuntingPanel = () => {
  const [huntingResults, setHuntingResults] = useState<AnomalyDetection[]>([])
  const [queryType, setQueryType] = useState<'IOC' | 'BEHAVIOR' | 'ANOMALY' | 'PATTERN'>('ANOMALY')
  const [searchValue, setSearchValue] = useState('')
  const [timeRange, setTimeRange] = useState('24h')
  const [isSearching, setIsSearching] = useState(false)
  const [threatIntel, setThreatIntel] = useState<ThreatIntelData[]>([])

  const performHunt = async () => {
    if (!searchValue) return
    setIsSearching(true)
    try {
      const response = await axios.post(`${API_BASE}/threat-hunt`, {
        query_type: queryType,
        filter_value: searchValue,
        time_range: timeRange,
      })
      setHuntingResults(response.data.results || [])
    } catch (error) {
      console.error('Threat hunt failed:', error)
    } finally {
      setIsSearching(false)
    }
  }

  const enrichIOC = async (ioc: string) => {
    try {
      const response = await axios.get(`${API_BASE}/threat-intel/enrich`, { params: { indicator: ioc } })
      setThreatIntel([response.data, ...threatIntel])
    } catch (error) {
      console.error('IOC enrichment failed:', error)
    }
  }

  return (
    <div className="p-6 space-y-6">
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-slate-100 mb-4">🎯 Advanced Threat Hunting</h3>

        <div className="space-y-4">
          <div className="grid grid-cols-4 gap-4">
            <div>
              <label className="text-sm text-slate-300 font-medium block mb-2">Hunt Type</label>
              <select
                title="Select threat hunting type"
                value={queryType}
                onChange={(e) => setQueryType(e.target.value as any)}
                className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-slate-100"
              >
                <option value="ANOMALY">🚨 Anomaly Detection</option>
                <option value="IOC">🔍 IOC Search</option>
                <option value="BEHAVIOR">📊 Behavior Pattern</option>
                <option value="PATTERN">🧩 Pattern Matching</option>
              </select>
            </div>

            <div>
              <label className="text-sm text-slate-300 font-medium block mb-2">Time Range</label>
              <select
                title="Select time range for search"
                value={timeRange}
                onChange={(e) => setTimeRange(e.target.value)}
                className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-slate-100"
              >
                <option value="1h">Last 1 Hour</option>
                <option value="6h">Last 6 Hours</option>
                <option value="24h">Last 24 Hours</option>
                <option value="7d">Last 7 Days</option>
                <option value="30d">Last 30 Days</option>
              </select>
            </div>

            <div>
              <label className="text-sm text-slate-300 font-medium block mb-2">Search Query</label>
              <input
                type="text"
                placeholder="e.g., 192.168.1.x, malware.exe"
                value={searchValue}
                onChange={(e) => setSearchValue(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && performHunt()}
                className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-slate-100 placeholder-slate-500"
              />
            </div>

            <div className="flex items-end">
              <button
                onClick={performHunt}
                disabled={isSearching || !searchValue}
                className="w-full px-4 py-2 bg-cyan-600 hover:bg-cyan-700 disabled:bg-slate-700 rounded text-white font-medium transition-colors"
              >
                {isSearching ? '🔄 Searching...' : '🔍 Hunt'}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Hunting Results */}
      {huntingResults.length > 0 && (
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-slate-100 mb-4">📋 Hunt Results ({huntingResults.length})</h3>
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {huntingResults.map((result) => (
              <div
                key={result.anomaly_id}
                className={`border rounded-lg p-4 ${result.risk_score > 7
                  ? 'bg-red-900/20 border-red-500/30'
                  : result.risk_score > 4
                    ? 'bg-orange-900/20 border-orange-500/30'
                    : 'bg-emerald-900/20 border-emerald-500/30'
                  }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <p className="font-semibold text-slate-100">{result.type}</p>
                    <p className="text-sm text-slate-300 mt-1">{result.description}</p>
                    <div className="flex gap-4 mt-2 text-xs text-slate-400">
                      <span>🎯 Risk: {result.risk_score.toFixed(1)}/10</span>
                      <span>📍 IPs: {result.affected_ips.length}</span>
                      <span>⏰ {new Date(result.detected_at).toLocaleString()}</span>
                    </div>
                  </div>
                  <div className="flex gap-2 ml-4">
                    <button
                      onClick={() => enrichIOC(result.affected_ips[0] || '')}
                      className="px-3 py-1 bg-cyan-600/20 hover:bg-cyan-600/30 text-cyan-400 rounded text-xs border border-cyan-500/30"
                    >
                      Enrich
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Threat Intelligence */}
      {threatIntel.length > 0 && (
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-slate-100 mb-4">🌐 Threat Intelligence Enrichment</h3>
          <div className="space-y-3 max-h-64 overflow-y-auto">
            {threatIntel.map((intel, i) => (
              <div
                key={i}
                className={`border rounded-lg p-4 ${intel.threat_level === 'CRITICAL'
                  ? 'bg-red-900/20 border-red-500/30'
                  : intel.threat_level === 'HIGH'
                    ? 'bg-orange-900/20 border-orange-500/30'
                    : 'bg-emerald-900/20 border-emerald-500/30'
                  }`}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <p className="font-semibold text-slate-100">{intel.indicator}</p>
                    <p className="text-xs text-slate-400 mt-1">Type: {intel.type} • Source: {intel.source}</p>
                    <p className="text-xs text-slate-500 mt-1">Confidence: {(intel.confidence * 100).toFixed(0)}% • Last Seen: {new Date(intel.last_seen).toLocaleDateString()}</p>
                  </div>
                  <span className={`px-2 py-1 text-xs font-semibold rounded whitespace-nowrap ${intel.threat_level === 'CRITICAL' ? 'bg-red-500/20 text-red-300' :
                    intel.threat_level === 'HIGH' ? 'bg-orange-500/20 text-orange-300' :
                      'bg-emerald-500/20 text-emerald-300'
                    }`}>
                    {intel.threat_level}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

const AnomalyDetectionPanel = () => {
  const [anomalies, setAnomalies] = useState<AnomalyDetection[]>([])
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [confidenceFilter, setConfidenceFilter] = useState(0.6)

  useEffect(() => {
    if (!autoRefresh) return

    const fetchAnomalies = async () => {
      try {
        const response = await axios.get(`${API_BASE}/anomalies/detect`, {
          params: { min_confidence: confidenceFilter }
        })
        setAnomalies(response.data.anomalies || [])
      } catch (error) {
        console.error('Failed to fetch anomalies:', error)
      }
    }

    fetchAnomalies()
    const interval = setInterval(fetchAnomalies, 5000)
    return () => clearInterval(interval)
  }, [autoRefresh, confidenceFilter])

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-100">🤖 Behavioral Anomaly Detection</h2>
          <p className="text-slate-400 text-sm mt-1">ML-powered real-time anomaly detection and correlation</p>
        </div>
        <div className="flex gap-4">
          <div>
            <label className="text-sm text-slate-300 font-medium block mb-2">Min. Confidence</label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={confidenceFilter}
              onChange={(e) => setConfidenceFilter(parseFloat(e.target.value))}
              className="w-32"
            />
          </div>
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`h-fit px-4 py-2 rounded border transition-all ${autoRefresh
              ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
              : 'bg-slate-700/50 text-slate-300 border-slate-600'
              }`}
          >
            {autoRefresh ? '✓ Live' : '⏸ Paused'}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-4">
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
          <p className="text-slate-400 text-sm">Active Anomalies</p>
          <p className="text-3xl font-bold text-red-400 mt-2">{anomalies.length}</p>
          <p className="text-xs text-slate-500 mt-1">Last 24 hours</p>
        </div>
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
          <p className="text-slate-400 text-sm">High Risk</p>
          <p className="text-3xl font-bold text-orange-400 mt-2">{anomalies.filter(a => a.risk_score > 7).length}</p>
          <p className="text-xs text-slate-500 mt-1">Risk Score {'>'} 7</p>
        </div>
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
          <p className="text-slate-400 text-sm">Affected IPs</p>
          <p className="text-3xl font-bold text-yellow-400 mt-2">{new Set(anomalies.flatMap(a => a.affected_ips)).size}</p>
          <p className="text-xs text-slate-500 mt-1">Unique sources</p>
        </div>
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
          <p className="text-slate-400 text-sm">Avg Confidence</p>
          <p className="text-3xl font-bold text-cyan-400 mt-2">{anomalies.length > 0 ? (anomalies.reduce((a, b) => a + b.confidence, 0) / anomalies.length * 100).toFixed(0) : 0}%</p>
          <p className="text-xs text-slate-500 mt-1">Detection accuracy</p>
        </div>
      </div>

      <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-slate-100 mb-4">📊 Recent Anomalies</h3>
        <div className="space-y-3 max-h-96 overflow-y-auto">
          {anomalies.slice(0, 20).map((anomaly) => (
            <div
              key={anomaly.anomaly_id}
              className={`border rounded-lg p-4 ${anomaly.risk_score > 7
                ? 'bg-red-900/20 border-red-500/30'
                : anomaly.risk_score > 4
                  ? 'bg-orange-900/20 border-orange-500/30'
                  : 'bg-emerald-900/20 border-emerald-500/30'
                }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <p className="font-semibold text-slate-100">{anomaly.type}</p>
                    <span className={`px-2 py-0.5 text-xs rounded font-medium ${anomaly.risk_score > 7 ? 'bg-red-500/20 text-red-300' :
                      anomaly.risk_score > 4 ? 'bg-orange-500/20 text-orange-300' :
                        'bg-emerald-500/20 text-emerald-300'
                      }`}>
                      Risk {anomaly.risk_score.toFixed(1)}/10
                    </span>
                  </div>
                  <p className="text-sm text-slate-300 mt-1">{anomaly.description}</p>
                  <div className="flex gap-4 mt-2 text-xs text-slate-400">
                    <span>🔒 Confidence: {(anomaly.confidence * 100).toFixed(0)}%</span>
                    <span>📍 IPs: {anomaly.affected_ips.join(', ')}</span>
                    <span>⏰ {new Date(anomaly.detected_at).toLocaleTimeString()}</span>
                  </div>
                </div>
                <button className="px-3 py-1 bg-cyan-600/20 hover:bg-cyan-600/30 text-cyan-400 rounded text-xs border border-cyan-500/30 ml-4 whitespace-nowrap">
                  Investigate
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

const AdvancedAnalyticsPanel = () => {
  const [_analyticsData, _setAnalyticsData] = useState({
    top_ips: [],
    top_ports: [],
    anomalies: [],
  })

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const response = await axios.get(`${API_BASE}/analytics/advanced`)
        _setAnalyticsData(response.data)
      } catch (error) {
        console.error('Failed to fetch analytics:', error)
      }
    }
    fetchAnalytics()
  }, [])

  return (
    <div className="p-6 space-y-6">
      <h2 className="text-2xl font-bold text-slate-100">📈 Advanced Network Analytics</h2>

      <div className="grid grid-cols-2 gap-6">
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-slate-100 mb-4">🗣️ Top Talkers</h3>
          <div className="space-y-3">
            {[
              { ip: '192.168.1.100', bytes: 2.5, packets: 125000, packets_color: 'w-[75%]' },
              { ip: '192.168.1.101', bytes: 1.8, packets: 98000, packets_color: 'w-[65%]' },
              { ip: '192.168.1.105', bytes: 1.2, packets: 67000, packets_color: 'w-[45%]' },
              { ip: '10.0.0.50', bytes: 0.9, packets: 45000, packets_color: 'w-[30%]' },
            ].map((talker, i) => (
              <div key={i}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-slate-300 font-medium">{talker.ip}</span>
                  <span className="text-slate-400">{talker.bytes}GB • {talker.packets.toLocaleString()} pkts</span>
                </div>
                <div className="bg-slate-700 rounded-full h-2">
                  <div className={`bg-gradient-to-r from-blue-500 to-cyan-500 h-2 rounded-full ${talker.packets_color}`}></div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-slate-100 mb-4">🌍 Port Analysis</h3>
          <div className="space-y-2 text-sm">
            {[
              { port: '443 (HTTPS)', percentage: 45, color: 'bg-blue-500' },
              { port: '80 (HTTP)', percentage: 25, color: 'bg-cyan-500' },
              { port: '22 (SSH)', percentage: 12, color: 'bg-emerald-500' },
              { port: '53 (DNS)', percentage: 10, color: 'bg-purple-500' },
              { port: 'Other', percentage: 8, color: 'bg-slate-500' },
            ].map((item, i) => (
              <div key={i} className="flex items-center gap-3">
                <span className="w-24 text-slate-300">{item.port}</span>
                <div className="flex-1 bg-slate-700 rounded-full h-2">
                  <div className={`${item.color} h-2 rounded-full`} style={{ width: `${item.percentage}%` }}></div>
                </div>
                <span className="w-12 text-right text-slate-400">{item.percentage}%</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-slate-100 mb-4">🗺️ Geographical Distribution</h3>
        <div className="grid grid-cols-5 gap-4">
          {[
            { region: 'North America', hosts: 450, threats: 12 },
            { region: 'Europe', hosts: 320, threats: 8 },
            { region: 'Asia-Pacific', hosts: 280, threats: 15 },
            { region: 'South America', hosts: 120, threats: 3 },
            { region: 'Africa', hosts: 80, threats: 2 },
          ].map((geo, i) => (
            <div key={i} className="bg-slate-700/50 rounded-lg p-4 text-center border border-slate-600">
              <p className="text-slate-300 font-medium text-sm">{geo.region}</p>
              <p className="text-2xl font-bold text-blue-400 mt-2">{geo.hosts}</p>
              <p className="text-xs text-slate-500 mt-1">hosts</p>
              <div className="flex items-center gap-1 mt-2 justify-center">
                <span className={`px-2 py-0.5 rounded text-xs font-semibold ${geo.threats > 10 ? 'bg-red-500/20 text-red-300' :
                  geo.threats > 5 ? 'bg-orange-500/20 text-orange-300' :
                    'bg-emerald-500/20 text-emerald-300'
                  }`}>
                  {geo.threats} threats
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default function NetworkSecurityPage() {
  const [activeTab, setActiveTab] = useState('overview')

  return (
    <div className="h-full flex flex-col bg-gradient-to-br from-slate-900 via-slate-900 to-slate-800 overflow-y-auto">
      <PageHeader />

      <div className="border-b border-slate-700 bg-slate-900/30 px-6 flex gap-8 sticky top-0 z-10 overflow-x-auto">
        {[
          { id: 'overview', label: '📊 Overview' },
          { id: 'capture', label: '🎯 Packet Capture' },
          { id: 'dpi', label: '🔍 DPI Engine' },
          { id: 'rules', label: '📋 Rules' },
          { id: 'hunting', label: '🎯 Threat Hunt' },
          { id: 'anomalies', label: '🤖 Anomalies' },
          { id: 'analytics', label: '📈 Analytics' },
          { id: 'threats', label: '🗺️ Threats' },
          { id: 'topology', label: '🔗 Topology' },
          { id: 'protocols', label: '📡 Protocols' },
          { id: 'alerts', label: '🔔 Alerts' },
          { id: 'bandwidth', label: '� Bandwidth' },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-4 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${activeTab === tab.id
              ? 'border-blue-500 text-blue-400'
              : 'border-transparent text-slate-400 hover:text-slate-300'
              }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-y-auto">
        {activeTab === 'overview' && (
          <>
            <NetworkMetricsGrid />
            <RecentAlerts />
          </>
        )}
        {activeTab === 'capture' && <PacketCapturePanel />}
        {activeTab === 'dpi' && <DPIEnginePanel />}
        {activeTab === 'rules' && <DPIRuleManager />}
        {activeTab === 'hunting' && <ThreatHuntingPanel />}
        {activeTab === 'anomalies' && <AnomalyDetectionPanel />}
        {activeTab === 'analytics' && <AdvancedAnalyticsPanel />}
        {activeTab === 'threats' && <ThreatMap />}
        {activeTab === 'topology' && <NetworkTopology />}
        {activeTab === 'protocols' && <ProtocolAnalysis />}
        {activeTab === 'alerts' && <RecentAlerts />}
        {activeTab === 'bandwidth' && <BandwidthMonitoring />}
      </div>

      <div className="border-t border-slate-700 bg-slate-900/50 backdrop-blur-sm px-6 py-3 grid grid-cols-6 gap-4 text-center text-xs sticky bottom-0">
        <div>
          <p className="text-slate-400 font-medium">Total Devices</p>
          <p className="text-blue-400 font-bold text-sm">2.3K</p>
        </div>
        <div>
          <p className="text-slate-400 font-medium">Active Threats</p>
          <p className="text-red-400 font-bold text-sm">47</p>
        </div>
        <div>
          <p className="text-slate-400 font-medium">Blocked</p>
          <p className="text-emerald-400 font-bold text-sm">312</p>
        </div>
        <div>
          <p className="text-slate-400 font-medium">Healthy</p>
          <p className="text-emerald-400 font-bold text-sm">2.1K</p>
        </div>
        <div>
          <p className="text-slate-400 font-medium">Avg Latency</p>
          <p className="text-indigo-400 font-bold text-sm">12ms</p>
        </div>
        <div>
          <p className="text-slate-400 font-medium">Last Update</p>
          <p className="text-cyan-400 font-bold text-sm">Just now</p>
        </div>
      </div>
    </div>
  )
}
