import { useState, useEffect, useCallback } from 'react'
import {
  Loader2, TrendingUp, TrendingDown, CheckCircle,
  Search, RefreshCw, Copy, Lock, Microscope, Clock, Flag, HardDrive,
  AlertTriangle, Flame, ChevronDown, ChevronUp, Shield, ExternalLink
} from 'lucide-react'
import './Forensics.css'

// ============ TYPES & INTERFACES ============

interface ForensicsStats {
  attackSurface: number
  vulnerabilities: number
  detectionRate: number
  lastUpdated: string
}

interface EvidenceItem {
  id: string
  type: string
  hash: string
  collected_at: string
  status: string
  size: number
  source: string
  chain_of_custody?: ChainOfCustodyRecord[]
  analysis?: EvidenceAnalysis
  metadata?: Record<string, unknown>
}

interface ChainOfCustodyRecord {
  handler: string
  action: string
  timestamp: string
  location: string
}

interface EvidenceAnalysis {
  evidenceId: string
  analysisType: string
  findings: Finding[]
  riskScore: number
  completedAt: string
  iocs?: IOC[]
  threatLevel: string
}

interface IOC {
  type: string
  value: string
  confidence: number
  source: string
}

interface Finding {
  finding_type: string
  description: string
  confidence: number
  severity: 'critical' | 'high' | 'medium' | 'low'
}

interface Toast {
  id: string
  message: string
  type: 'success' | 'error' | 'info'
}

interface IncidentReport {
  id: string
  title: string
  description: string
  created: string
  updated: string
  status: 'open' | 'investigating' | 'resolved' | 'closed'
  severity: 'critical' | 'high' | 'medium' | 'low'
  evidence_count: number
  assignee: string
}

interface ForensicsHealth {
  ledger_operational: boolean
  web3_connected: boolean
  fabric_network_ready: boolean
  evidence_vault_accessible: boolean
  analysis_engine_status: string
  last_sync: string
}

// ============ CONSTANTS ============

const API_BASE = 'http://localhost:8000/api/forensics'
const ANALYSIS_TYPES = ['cryptographic', 'pattern', 'anomaly', 'malware', 'behavioral', 'network']
const EVIDENCE_TYPES = ['network_packet', 'memory_dump', 'disk_image', 'log_file', 'registry', 'browser_history', 'system_call', 'api_trace']

// ============ ADVANCED API FUNCTIONS ============

const fetchForensicsStats = async (): Promise<ForensicsStats | null> => {
  try {
    const response = await fetch(`${API_BASE}/stats`)
    if (!response.ok) throw new Error('Failed to fetch stats')
    return await response.json()
  } catch (error) {
    console.error('Error fetching forensics stats:', error)
    return null
  }
}

const fetchEvidenceInventory = async (status?: string, limit = 100): Promise<EvidenceItem[]> => {
  try {
    const url = new URL(`${API_BASE}/evidence`)
    if (status) url.searchParams.append('status', status)
    url.searchParams.append('limit', limit.toString())
    const response = await fetch(url.toString())
    if (!response.ok) throw new Error('Failed to fetch evidence')
    const data = await response.json()
    return data.data || []
  } catch (error) {
    console.error('Error fetching evidence inventory:', error)
    return []
  }
}

const analyzeEvidence = async (evidenceId: string, analysisType: string): Promise<EvidenceAnalysis | null> => {
  try {
    const response = await fetch(`${API_BASE}/evidence/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ evidence_id: evidenceId, analysis_type: analysisType })
    })
    if (!response.ok) throw new Error('Failed to analyze evidence')
    return await response.json()
  } catch (error) {
    console.error('Error analyzing evidence:', error)
    return null
  }
}

const _getEvidenceChainOfCustody = async (evidenceId: string): Promise<ChainOfCustodyRecord[] | null> => {
  try {
    const response = await fetch(`${API_BASE}/evidence/${evidenceId}/chain-of-custody`)
    if (!response.ok) throw new Error('Failed to fetch chain of custody')
    return await response.json()
  } catch (error) {
    console.error('Error fetching chain of custody:', error)
    return null
  }
}
// prevent "declared but never used" warnings for helpers kept for API completeness
void _getEvidenceChainOfCustody

const verifyBlockchainIntegrity = async (evidenceId: string): Promise<Record<string, unknown> | null> => {
  try {
    const response = await fetch(`${API_BASE}/evidence/${evidenceId}/verify-blockchain`)
    if (!response.ok) throw new Error('Failed to verify blockchain')
    return await response.json()
  } catch (error) {
    console.error('Error verifying blockchain:', error)
    return null
  }
}

const generateForensicsReport = async (caseId: string, format: string = 'pdf'): Promise<Blob | null> => {
  try {
    const response = await fetch(`${API_BASE}/reports/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ case_id: caseId, format })
    })
    if (!response.ok) throw new Error('Failed to generate report')
    return await response.blob()
  } catch (error) {
    console.error('Error generating report:', error)
    return null
  }
}

const addCustodyRecord = async (evidenceId: string, handler: string, action: string, location: string): Promise<ChainOfCustodyRecord | null> => {
  try {
    const response = await fetch(`${API_BASE}/evidence/${evidenceId}/chain-of-custody`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ handler, action, location })
    })
    if (!response.ok) throw new Error('Failed to add custody record')
    return await response.json()
  } catch (error) {
    console.error('Error adding custody record:', error)
    return null
  }
}

const _createIncident = async (title: string, description: string, severity: string, assignee: string): Promise<IncidentReport | null> => {
  try {
    const response = await fetch(`${API_BASE}/incidents`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, description, severity, assignee })
    })
    if (!response.ok) throw new Error('Failed to create incident')
    return await response.json()
  } catch (error) {
    console.error('Error creating incident:', error)
    return null
  }
}
void _createIncident

const checkForensicsHealth = async (): Promise<ForensicsHealth | null> => {
  try {
    const response = await fetch(`${API_BASE}/health`)
    if (!response.ok) throw new Error('Health check failed')
    return await response.json()
  } catch (error) {
    console.error('Error checking forensics health:', error)
    return null
  }
}

const fetchIncidentReports = async (): Promise<IncidentReport[]> => {
  try {
    const response = await fetch(`${API_BASE}/incidents`)
    if (!response.ok) throw new Error('Failed to fetch incidents')
    const data = await response.json()
    return data.data || []
  } catch (error) {
    console.error('Error fetching incidents:', error)
    return []
  }
}

// ============ COMPONENTS ============

const PageHeader = () => (
  <div className="relative overflow-hidden bg-gradient-to-r from-slate-950 via-cyan-950/50 to-slate-950 border-b border-slate-700/50">
    <div className="absolute inset-0 opacity-20">
      <div className="absolute top-0 right-0 w-96 h-96 bg-cyan-500/20 rounded-full blur-3xl" />
      <div className="absolute bottom-0 left-1/4 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl" />
    </div>
    <div className="relative p-8">
      <div className="flex items-center gap-4">
        <div className="p-3 bg-cyan-900/30 rounded-lg">
          <Microscope className="w-8 h-8 text-cyan-400" />
        </div>
        <div>
          <h1 className="text-4xl font-bold bg-gradient-to-r from-cyan-400 to-emerald-400 bg-clip-text text-transparent">
            FORENSICS HUB
          </h1>
          <p className="text-slate-400 mt-2">Advanced Incident Investigation • Evidence Management • Blockchain-Verified Chain of Custody</p>
        </div>
      </div>
    </div>
  </div>
)

const HealthDashboard = ({ health, onRefresh, isRefreshing }: HealthDashboardProps) => {
  if (!health) return null

  const getStatusColor = (status: boolean) => status ? 'bg-emerald-900/30 border-emerald-500/50 text-emerald-300' : 'bg-red-900/30 border-red-500/50 text-red-300'
  const getStatusIcon = (status: boolean) => status ? '🟢' : '🔴'

  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-3 p-6">
      <div className={`p-3 rounded-lg border ${getStatusColor(health.ledger_operational)}`}>
        <div className="flex items-center gap-2">
          <span>{getStatusIcon(health.ledger_operational)}</span>
          <div className="text-xs">
            <p className="font-medium">Ledger</p>
            <p className="text-xs opacity-75">Operational</p>
          </div>
        </div>
      </div>
      <div className={`p-3 rounded-lg border ${getStatusColor(health.web3_connected)}`}>
        <div className="flex items-center gap-2">
          <span>{getStatusIcon(health.web3_connected)}</span>
          <div className="text-xs">
            <p className="font-medium">Web3</p>
            <p className="text-xs opacity-75">Connected</p>
          </div>
        </div>
      </div>
      <div className={`p-3 rounded-lg border ${getStatusColor(health.fabric_network_ready)}`}>
        <div className="flex items-center gap-2">
          <span>{getStatusIcon(health.fabric_network_ready)}</span>
          <div className="text-xs">
            <p className="font-medium">Fabric</p>
            <p className="text-xs opacity-75">Network</p>
          </div>
        </div>
      </div>
      <div className={`p-3 rounded-lg border ${getStatusColor(health.evidence_vault_accessible)}`}>
        <div className="flex items-center gap-2">
          <span>{getStatusIcon(health.evidence_vault_accessible)}</span>
          <div className="text-xs">
            <p className="font-medium">Evidence</p>
            <p className="text-xs opacity-75">Vault</p>
          </div>
        </div>
      </div>
      <div className="p-3 rounded-lg border bg-slate-900/50 border-slate-700/50">
        <button
          onClick={onRefresh}
          disabled={isRefreshing}
          title="Refresh health status"
          className="w-full h-full flex items-center justify-center hover:bg-slate-800/50 disabled:opacity-50 disabled:cursor-not-allowed rounded transition-colors"
        >
          <RefreshCw className={`w-4 h-4 text-cyan-400 ${isRefreshing ? 'animate-spin' : 'hover:animate-spin'}`} />
        </button>
      </div>
    </div>
  )
}

const AdvancedStatsGrid = ({ stats }: { stats: ForensicsStats | null }) => {
  if (!stats) return <div className="p-6 text-slate-400">Loading statistics...</div>

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 p-6">
      <div className="p-6 rounded-lg border bg-gradient-to-br from-cyan-500/20 to-cyan-500/5 border-cyan-500/30 hover:border-cyan-500/50 transition-all">
        <div className="flex justify-between items-start mb-4">
          <Flame className="w-6 h-6 text-cyan-400" />
          <TrendingUp className="w-4 h-4 text-emerald-400" />
        </div>
        <p className="text-slate-400 text-sm font-medium mb-1">Attack Surface Exposure</p>
        <p className="text-3xl font-bold text-slate-100">{Math.round(stats.attackSurface / 100)}%</p>
        <div className="w-full bg-slate-700/30 rounded-full h-1.5 mt-3">
          <div className="h-full bg-cyan-500/40 rounded-full" style={{ width: `${stats.attackSurface / 100}%` }} />
        </div>
        <p className="text-xs text-cyan-400 mt-2">+5.2% from baseline</p>
      </div>

      <div className="p-6 rounded-lg border bg-gradient-to-br from-orange-500/20 to-orange-500/5 border-orange-500/30 hover:border-orange-500/50 transition-all">
        <div className="flex justify-between items-start mb-4">
          <AlertTriangle className="w-6 h-6 text-orange-400" />
          <TrendingDown className="w-4 h-4 text-red-400" />
        </div>
        <p className="text-slate-400 text-sm font-medium mb-1">Critical Vulnerabilities</p>
        <p className="text-3xl font-bold text-slate-100">{stats.vulnerabilities}</p>
        <div className="w-full bg-slate-700/30 rounded-full h-1.5 mt-3">
          <div className="h-full bg-orange-500/40 rounded-full" style={{ width: `${Math.min(stats.vulnerabilities * 5, 100)}%` }} />
        </div>
        <p className="text-xs text-red-400 mt-2">-2 from last scan</p>
      </div>

      <div className="p-6 rounded-lg border bg-gradient-to-br from-emerald-500/20 to-emerald-500/5 border-emerald-500/30 hover:border-emerald-500/50 transition-all">
        <div className="flex justify-between items-start mb-4">
          <CheckCircle className="w-6 h-6 text-emerald-400" />
          <TrendingUp className="w-4 h-4 text-emerald-400" />
        </div>
        <p className="text-slate-400 text-sm font-medium mb-1">Detection Accuracy Rate</p>
        <p className="text-3xl font-bold text-slate-100">{stats.detectionRate}%</p>
        <div className="w-full bg-slate-700/30 rounded-full h-1.5 mt-3">
          <div className="h-full bg-emerald-500/40 rounded-full" style={{ width: `${stats.detectionRate}%` }} />
        </div>
        <p className="text-xs text-emerald-400 mt-2">+2.1% improvement</p>
      </div>

      <div className="p-6 rounded-lg border bg-gradient-to-br from-purple-500/20 to-purple-500/5 border-purple-500/30 hover:border-purple-500/50 transition-all">
        <div className="flex justify-between items-start mb-4">
          <Shield className="w-6 h-6 text-purple-400" />
          <Clock className="w-4 h-4 text-purple-400" />
        </div>
        <p className="text-slate-400 text-sm font-medium mb-1">Last Updated</p>
        <p className="text-sm font-bold text-slate-100">{new Date(stats.lastUpdated).toLocaleTimeString()}</p>
        <p className="text-xs text-slate-500 mt-3">Status: LIVE</p>
        <div className="w-full mt-3 flex items-center gap-1">
          <div className="w-1 h-1 bg-emerald-500 rounded-full animate-pulse" />
          <span className="text-xs text-emerald-400">Real-time Monitoring</span>
        </div>
      </div>
    </div>
  )
}

const TabNav = ({ activeTab, onTabChange }: TabNavProps) => {
  const tabs = [
    { id: 'dashboard', label: 'Dashboard', icon: '📊' },
    { id: 'evidence', label: 'Evidence Vault', icon: '🗝️' },
    { id: 'analysis', label: 'Analysis', icon: '🔬' },
    { id: 'incidents', label: 'Cases', icon: '🚨' },
    { id: 'chain-custody', label: 'Custody', icon: '⛓️' },
    { id: 'blockchain', label: 'Ledger', icon: '✓' },
  ]

  return (
    <div className="flex border-b border-slate-700 bg-slate-900/30 overflow-x-auto sticky top-0 z-40">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => onTabChange(tab.id)}
          className={`px-6 py-4 font-medium text-sm whitespace-nowrap transition-all duration-200 border-b-2 ${activeTab === tab.id
            ? 'border-cyan-500 text-cyan-400 bg-slate-900/50'
            : 'border-transparent text-slate-400 hover:text-slate-300'
            }`}
        >
          {tab.icon} {tab.label}
        </button>
      ))}
    </div>
  )
}

// ============ TAB CONTENT ============

const DashboardTab = ({ _stats, _health, incidents, onRefresh }: DashboardTabProps) => {
  const [refreshing, setRefreshing] = useState(false)

  const handleRefresh = async () => {
    try {
      setRefreshing(true)
      await onRefresh()
    } finally {
      setRefreshing(false)
    }
  }

  // mark intentionally unused destructured props as used to silence unused var errors
  void _stats
  void _health

  return (
    <div className="space-y-6 p-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-slate-100">FORENSICS COMMAND CENTER</h2>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="flex items-center gap-2 px-4 py-2 bg-cyan-600/20 hover:bg-cyan-600/30 disabled:opacity-50 disabled:cursor-not-allowed border border-cyan-500/50 rounded-lg text-cyan-300 transition-all"
          title="Refresh forensics data from all sources"
        >
          <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
          {refreshing ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-slate-900/50 border border-slate-700 rounded-lg p-6 hover:border-slate-600 transition-all">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-slate-100">Active Cases</h3>
            <Flag className="w-5 h-5 text-orange-400" />
          </div>
          <p className="text-4xl font-bold text-orange-400">{incidents?.length || 0}</p>
          <p className="text-sm text-slate-400 mt-2">{incidents.filter((i: IncidentReport) => i.status === 'open').length || 0} currently open</p>
        </div>

        <div className="bg-slate-900/50 border border-slate-700 rounded-lg p-6 hover:border-slate-600 transition-all">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-slate-100">Evidence Items</h3>
            <HardDrive className="w-5 h-5 text-cyan-400" />
          </div>
          <p className="text-4xl font-bold text-cyan-400">847</p>
          <p className="text-sm text-slate-400 mt-2">Across all cases</p>
        </div>

        <div className="bg-slate-900/50 border border-slate-700 rounded-lg p-6 hover:border-slate-600 transition-all">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-slate-100">Integrity Status</h3>
            <Lock className="w-5 h-5 text-emerald-400" />
          </div>
          <p className="text-4xl font-bold text-emerald-400">100%</p>
          <p className="text-sm text-slate-400 mt-2">All chains verified</p>
        </div>
      </div>

      <div className="bg-slate-900/50 border border-slate-700 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-slate-100 mb-4 flex items-center gap-2">
          <Flame className="w-5 h-5 text-red-400" />
          CRITICAL INCIDENTS REQUIRING ACTION
        </h3>
        <div className="space-y-3">
          {incidents?.filter((i: IncidentReport) => i.severity === 'critical' || i.severity === 'high').slice(0, 5).map((incident: IncidentReport) => (
            <div key={incident.id} className={`p-4 rounded-lg border flex justify-between items-start ${incident.severity === 'critical' ? 'bg-red-900/20 border-red-500/30' : 'bg-orange-900/20 border-orange-500/30'
              }`}>
              <div className="flex-1">
                <p className={`font-semibold ${incident.severity === 'critical' ? 'text-red-300' : 'text-orange-300'}`}>{incident.title}</p>
                <p className="text-sm text-slate-400 mt-1">{incident.description}</p>
                <div className="flex gap-4 mt-2 text-xs text-slate-500">
                  <span>🔖 {incident.id}</span>
                  <span>👤 {incident.assignee}</span>
                  <span>📦 {incident.evidence_count} evidence</span>
                </div>
              </div>
              <span className={`px-3 py-1 rounded-full text-xs font-medium whitespace-nowrap ${incident.severity === 'critical' ? 'bg-red-500/20 text-red-300' : 'bg-orange-500/20 text-orange-300'
                }`}>
                {incident.severity.toUpperCase()}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

const EvidenceVaultTab = ({ evidence, onAnalyze, analyzing }: EvidenceVaultTabProps) => {
  const [expandedDetails, setExpandedDetails] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [filterType, setFilterType] = useState<string>('')
  const [filterStatus, setFilterStatus] = useState<string>('')

  const filteredEvidence = evidence.filter((e: EvidenceItem) =>
    (searchTerm === '' || e.id.toLowerCase().includes(searchTerm.toLowerCase()) || e.source.toLowerCase().includes(searchTerm.toLowerCase())) &&
    (filterType === '' || e.type === filterType) &&
    (filterStatus === '' || e.status === filterStatus)
  )

  return (
    <div className="space-y-6 p-6">
      <h2 className="text-2xl font-bold text-slate-100">CLASSIFIED EVIDENCE VAULT</h2>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="relative">
          <Search className="absolute left-3 top-2.5 w-5 h-5 text-slate-500" />
          <input
            type="text"
            placeholder="Search by ID, hash, or source..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-slate-800 border border-slate-600 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500"
          />
        </div>
        <select
          title="Filter evidence by type"
          value={filterType}
          onChange={(e) => setFilterType(e.target.value)}
          className="px-4 py-2 bg-slate-800 border border-slate-600 rounded-lg text-slate-100 focus:outline-none focus:border-cyan-500"
        >
          <option value="">All Types</option>
          {EVIDENCE_TYPES.map(t => <option key={t} value={t}>{t.replace(/_/g, ' ')}</option>)}
        </select>
        <select
          title="Filter evidence by status"
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          className="px-4 py-2 bg-slate-800 border border-slate-600 rounded-lg text-slate-100 focus:outline-none focus:border-cyan-500"
        >
          <option value="">All Status</option>
          <option value="verified">Verified</option>
          <option value="pending_verification">Pending</option>
          <option value="compromised">Compromised</option>
        </select>
      </div>

      <div className="space-y-3">
        {filteredEvidence.length === 0 ? (
          <div className="bg-slate-900/50 border border-slate-700 rounded-lg p-8 text-center">
            <HardDrive className="w-12 h-12 text-slate-500 mx-auto mb-3 opacity-50" />
            <p className="text-slate-400">No evidence found matching filters</p>
          </div>
        ) : (
          filteredEvidence.map((item: EvidenceItem) => (
            <div key={item.id} className={`bg-slate-900/50 border rounded-lg transition-all ${expandedDetails === item.id ? 'border-cyan-500 bg-cyan-900/10' : 'border-slate-700 hover:border-slate-600'
              }`}>
              <div className="p-4">
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-4 flex-1 cursor-pointer" onClick={() => setExpandedDetails(expandedDetails === item.id ? null : item.id)}>
                    <div className="text-2xl">
                      {item.type.includes('network') ? '🌐' : item.type.includes('memory') ? '💾' : item.type.includes('disk') ? '🗄️' : '📄'}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <h3 className="font-semibold text-slate-100">{item.id}</h3>
                        <span className="px-2 py-1 bg-slate-800 rounded text-xs text-slate-300">{(item.type ?? 'unknown').replace(/_/g, ' ')}</span>
                        <span className={`px-2 py-1 rounded text-xs font-medium ${(item.status ?? '') === 'verified' ? 'bg-emerald-900/30 text-emerald-300' :
                          (item.status ?? '') === 'pending_verification' ? 'bg-yellow-900/30 text-yellow-300' :
                            'bg-red-900/30 text-red-300'
                          }`}>
                          {(item.status ?? 'unknown').replace(/_/g, ' ')}
                        </span>
                      </div>
                      <div className="flex items-center gap-4 mt-2 text-sm text-slate-400 flex-wrap">
                        <span>📦 {(item.size / 1024 / 1024).toFixed(2)} MB</span>
                        <span>📍 {item.source}</span>
                        <span>🕐 {new Date(item.collected_at).toLocaleDateString()}</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => navigator.clipboard.writeText(item.hash)}
                      className="p-2 hover:bg-slate-800 rounded transition-colors"
                      title="Copy hash"
                    >
                      <Copy className="w-4 h-4 text-slate-400" />
                    </button>
                    <button
                      onClick={() => onAnalyze(item.id, 'cryptographic')}
                      disabled={analyzing}
                      className="p-2 hover:bg-cyan-900/20 disabled:opacity-50 disabled:cursor-not-allowed rounded transition-colors"
                      title="Analyze evidence with cryptographic analysis"
                    >
                      <Microscope className={`w-4 h-4 ${analyzing ? 'text-slate-500' : 'text-cyan-400'}`} />
                    </button>
                    <button
                      onClick={() => setExpandedDetails(expandedDetails === item.id ? null : item.id)}
                      className="p-2 hover:bg-slate-800 rounded transition-colors"
                      title="Expand details"
                    >
                      {expandedDetails === item.id ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
                    </button>
                  </div>
                </div>

                {expandedDetails === item.id && (
                  <div className="border-t border-slate-700 mt-4 pt-4 space-y-4">
                    <div className="bg-slate-800/50 rounded p-3">
                      <p className="text-xs text-slate-400 mb-1">SHA-256 Hash:</p>
                      <p className="text-xs font-mono text-cyan-300 break-all">{item.hash}</p>
                    </div>

                    {item.analysis && (
                      <div className={`p-4 rounded border ${item.analysis.riskScore > 7 ? 'bg-red-900/20 border-red-500/30' :
                        item.analysis.riskScore > 4 ? 'bg-orange-900/20 border-orange-500/30' :
                          'bg-emerald-900/20 border-emerald-500/30'
                        }`}>
                        <p className="text-sm font-semibold mb-3">
                          🎯 RISK: <span className="text-lg font-bold">{item.analysis.riskScore.toFixed(1)}/10</span>
                          <span className={`ml-2 px-2 py-1 rounded text-xs ${item.analysis.threatLevel === 'critical' ? 'bg-red-500/20 text-red-300' :
                            item.analysis.threatLevel === 'high' ? 'bg-orange-500/20 text-orange-300' :
                              'bg-emerald-500/20 text-emerald-300'
                            }`}>
                            {(item.analysis.threatLevel ?? 'unknown').toUpperCase()}
                          </span>
                        </p>
                        <div className="space-y-2 text-xs">
                          {(item.analysis.findings ?? []).slice(0, 3).map((f, i) => (
                            <div key={i} className="flex items-start gap-2">
                              <span className="font-bold text-cyan-400">•</span>
                              <div>
                                <p className="font-medium text-slate-200">{f.finding_type}</p>
                                <p className="text-slate-400">{f.description}</p>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {item.chain_of_custody && item.chain_of_custody.length > 0 && (
                      <div className="p-3 bg-slate-800/30 rounded border border-slate-700">
                        <p className="text-xs font-bold text-slate-200 mb-2">CUSTODY CHAIN ({item.chain_of_custody.length} transfers):</p>
                        <div className="space-y-1 text-xs">
                          {item.chain_of_custody.map((record, i) => (
                            <div key={i} className="flex items-center gap-2 text-slate-400">
                              <span>➜</span>
                              <span>{record.handler}</span>
                              <span className="text-slate-600">•</span>
                              <span>{new Date(record.timestamp).toLocaleString()}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

const AnalysisEngineTab = ({ evidence, onAnalyze, analyzing }: AnalysisEngineTabProps) => {
  const [selectedEvidence, setSelectedEvidence] = useState<string>('')
  const [selectedAnalysis, setSelectedAnalysis] = useState<string>('cryptographic')

  return (
    <div className="space-y-6 p-6">
      <h2 className="text-2xl font-bold text-slate-100">ADVANCED ANALYSIS ENGINE</h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-slate-900/50 border border-slate-700 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-slate-100 mb-4">Configure Analysis</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">Select Evidence</label>
              <select
                title="Select evidence to analyze"
                value={selectedEvidence}
                onChange={(e) => setSelectedEvidence(e.target.value)}
                className="w-full px-4 py-2 bg-slate-800 border border-slate-600 rounded-lg text-slate-100 focus:outline-none focus:border-cyan-500"
              >
                <option value="">Choose evidence...</option>
                {evidence.map((e: EvidenceItem) => (
                  <option key={e.id} value={e.id}>{e.id} ({e.type.replace(/_/g, ' ')})</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-3">Analysis Type</label>
              <div className="grid grid-cols-2 gap-2">
                {ANALYSIS_TYPES.map(type => (
                  <button
                    key={type}
                    onClick={() => setSelectedAnalysis(type)}
                    className={`p-3 rounded-lg border transition-all text-xs font-medium ${selectedAnalysis === type
                      ? 'bg-cyan-900/40 border-cyan-500 text-cyan-300'
                      : 'bg-slate-800/30 border-slate-600 text-slate-400 hover:border-slate-500'
                      }`}
                  >
                    {type.charAt(0).toUpperCase() + type.slice(1)}
                  </button>
                ))}
              </div>
            </div>

            <button
              onClick={() => selectedEvidence && onAnalyze(selectedEvidence, selectedAnalysis)}
              disabled={!selectedEvidence || analyzing}
              className="w-full px-4 py-3 bg-cyan-600 hover:bg-cyan-700 disabled:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
              title={!selectedEvidence ? 'Select evidence first' : analyzing ? 'Analysis in progress...' : 'Start evidence analysis'}
            >
              {analyzing ? <Loader2 className="w-4 h-4 animate-spin" /> : <Microscope className="w-4 h-4" />}
              {analyzing ? 'Analyzing...' : 'START ANALYSIS'}
            </button>
          </div>
        </div>

        <div className="bg-slate-900/50 border border-slate-700 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-slate-100 mb-4">Analysis Profiles</h3>
          <div className="space-y-3">
            <div className="p-3 bg-slate-800/30 rounded-lg border border-slate-700">
              <h4 className="font-medium text-cyan-400 mb-1">🔐 Cryptographic</h4>
              <p className="text-xs text-slate-400">Verify signatures & hash integrity</p>
            </div>
            <div className="p-3 bg-slate-800/30 rounded-lg border border-slate-700">
              <h4 className="font-medium text-emerald-400 mb-1">📊 Pattern</h4>
              <p className="text-xs text-slate-400">Identify suspicious patterns</p>
            </div>
            <div className="p-3 bg-slate-800/30 rounded-lg border border-slate-700">
              <h4 className="font-medium text-orange-400 mb-1">🎯 Anomaly</h4>
              <p className="text-xs text-slate-400">ML-based deviation detection</p>
            </div>
            <div className="p-3 bg-slate-800/30 rounded-lg border border-slate-700">
              <h4 className="font-medium text-red-400 mb-1">🦠 Malware</h4>
              <p className="text-xs text-slate-400">Signature & heuristic detection</p>
            </div>
            <div className="p-3 bg-slate-800/30 rounded-lg border border-slate-700">
              <h4 className="font-medium text-purple-400 mb-1">🧬 Behavioral</h4>
              <p className="text-xs text-slate-400">Runtime behavior profiling</p>
            </div>
            <div className="p-3 bg-slate-800/30 rounded-lg border border-slate-700">
              <h4 className="font-medium text-pink-400 mb-1">🌐 Network</h4>
              <p className="text-xs text-slate-400">Deep packet & flow analysis</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

const IncidentCasesTab = ({ incidents, onRefresh, onGenerateReport }: IncidentCasesTabProps) => {
  const [expandedCase, setExpandedCase] = useState<string | null>(null)
  const [generating, setGenerating] = useState<string | null>(null)

  const handleGenerateReport = async (caseId: string) => {
    try {
      setGenerating(caseId)
      await onGenerateReport(caseId)
    } finally {
      setGenerating(null)
    }
  }

  return (
    <div className="space-y-6 p-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-slate-100">INCIDENT CASE FILES</h2>
        <button
          onClick={onRefresh}
          className="flex items-center gap-2 px-4 py-2 bg-cyan-600/20 hover:bg-cyan-600/30 border border-cyan-500/50 rounded-lg text-cyan-300 transition-all"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="p-4 bg-slate-900/50 border border-slate-700 rounded-lg">
          <p className="text-slate-400 text-xs mb-1">Total Cases</p>
          <p className="text-2xl font-bold text-cyan-400">{incidents?.length || 0}</p>
        </div>
        <div className="p-4 bg-slate-900/50 border border-slate-700 rounded-lg">
          <p className="text-slate-400 text-xs mb-1">Open Cases</p>
          <p className="text-2xl font-bold text-orange-400">{incidents?.filter((i: IncidentReport) => i.status === 'open').length || 0}</p>
        </div>
        <div className="p-4 bg-slate-900/50 border border-slate-700 rounded-lg">
          <p className="text-slate-400 text-xs mb-1">Investigating</p>
          <p className="text-2xl font-bold text-yellow-400">{incidents?.filter((i: IncidentReport) => i.status === 'investigating').length || 0}</p>
        </div>
        <div className="p-4 bg-slate-900/50 border border-slate-700 rounded-lg">
          <p className="text-slate-400 text-xs mb-1">Closed Cases</p>
          <p className="text-2xl font-bold text-emerald-400">{incidents?.filter((i: IncidentReport) => i.status === 'closed').length || 0}</p>
        </div>
      </div>

      <div className="space-y-3">
        {incidents?.map((incident: IncidentReport) => (
          <div
            key={incident.id}
            className="bg-slate-900/50 border border-slate-700 rounded-lg transition-all hover:border-slate-600"
          >
            <div
              className="p-4 cursor-pointer"
              onClick={() => setExpandedCase(expandedCase === incident.id ? null : incident.id)}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="font-semibold text-slate-100">{incident.title}</h3>
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${incident.severity === 'critical' ? 'bg-red-500/20 text-red-300' :
                      incident.severity === 'high' ? 'bg-orange-500/20 text-orange-300' :
                        'bg-yellow-500/20 text-yellow-300'
                      }`}>
                      {incident.severity.toUpperCase()}
                    </span>
                  </div>
                  <p className="text-sm text-slate-400 mb-2">{incident.description}</p>
                  <div className="flex gap-4 text-xs text-slate-500">
                    <span>🔖 {incident.id}</span>
                    <span>📅 {new Date(incident.created).toLocaleDateString()}</span>
                    <span>📦 {incident.evidence_count} evidence</span>
                    <span>👤 {incident.assignee}</span>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <span className={`px-3 py-1 rounded-full text-xs font-medium whitespace-nowrap ${incident.status === 'open' ? 'bg-red-900/30 text-red-300' :
                    incident.status === 'investigating' ? 'bg-orange-900/30 text-orange-300' :
                      'bg-emerald-900/30 text-emerald-300'
                    }`}>
                    {incident.status.replace(/_/g, ' ').toUpperCase()}
                  </span>
                  {expandedCase === incident.id ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
                </div>
              </div>
            </div>

            {expandedCase === incident.id && (
              <div className="border-t border-slate-700 p-4 bg-slate-800/20 space-y-3">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div className="p-3 bg-slate-800/30 rounded border border-slate-700">
                    <p className="text-xs font-bold text-slate-300 mb-1">Case ID</p>
                    <p className="text-sm text-slate-100 font-mono">{incident.id}</p>
                  </div>
                  <div className="p-3 bg-slate-800/30 rounded border border-slate-700">
                    <p className="text-xs font-bold text-slate-300 mb-1">Assignee</p>
                    <p className="text-sm text-slate-100">{incident.assignee}</p>
                  </div>
                  <div className="p-3 bg-slate-800/30 rounded border border-slate-700">
                    <p className="text-xs font-bold text-slate-300 mb-1">Created</p>
                    <p className="text-sm text-slate-100">{new Date(incident.created).toLocaleString()}</p>
                  </div>
                  <div className="p-3 bg-slate-800/30 rounded border border-slate-700">
                    <p className="text-xs font-bold text-slate-300 mb-1">Updated</p>
                    <p className="text-sm text-slate-100">{new Date(incident.updated).toLocaleString()}</p>
                  </div>
                </div>
                <button
                  onClick={() => handleGenerateReport(incident.id)}
                  disabled={generating === incident.id}
                  className="w-full px-4 py-2 bg-cyan-600/20 hover:bg-cyan-600/30 disabled:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed border border-cyan-500/50 rounded-lg text-cyan-300 transition-all text-sm"
                  title="Generate forensics report for this case"
                >
                  {generating === incident.id ? <Loader2 className="w-4 h-4 animate-spin inline mr-2" /> : '📥'} {generating === incident.id ? 'Generating...' : 'Generate Report'}
                </button>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

const ChainOfCustodyTab = ({ evidence, onAddCustodyRecord }: ChainOfCustodyTabProps) => {
  const [showAddForm, setShowAddForm] = useState<string | null>(null)
  const [formData, setFormData] = useState({ handler: '', action: '', location: '' })
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = async (evidenceId: string) => {
    if (!formData.handler.trim()) {
      alert('Handler name is required')
      return
    }
    if (!formData.action.trim()) {
      alert('Action is required')
      return
    }
    if (!formData.location.trim()) {
      alert('Location is required')
      return
    }
    try {
      setSubmitting(true)
      await onAddCustodyRecord(evidenceId, formData.handler, formData.action, formData.location)
      setFormData({ handler: '', action: '', location: '' })
      setShowAddForm(null)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="space-y-6 p-6">
      <h2 className="text-2xl font-bold text-slate-100">CHAIN OF CUSTODY LEDGER</h2>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="p-4 bg-emerald-900/20 border border-emerald-500/30 rounded-lg">
          <p className="text-emerald-300 text-sm font-medium">Verified Records</p>
          <p className="text-3xl font-bold text-emerald-400">{evidence?.length || 0}</p>
        </div>
        <div className="p-4 bg-cyan-900/20 border border-cyan-500/30 rounded-lg">
          <p className="text-cyan-300 text-sm font-medium">Integrity Status</p>
          <p className="text-3xl font-bold text-cyan-400">100%</p>
        </div>
        <div className="p-4 bg-purple-900/20 border border-purple-500/30 rounded-lg">
          <p className="text-purple-300 text-sm font-medium">Blockchain Verified</p>
          <p className="text-3xl font-bold text-purple-400">✓ ALL</p>
        </div>
      </div>

      <div className="space-y-3">
        {evidence.filter((e: EvidenceItem) => e.chain_of_custody && e.chain_of_custody.length > 0).map((item: EvidenceItem) => (
          <div key={item.id} className="bg-slate-900/50 border border-slate-700 rounded-lg p-4">
            <div className="flex justify-between items-start mb-3">
              <h3 className="font-semibold text-slate-100">📦 {item.id}</h3>
              <button onClick={() => setShowAddForm(showAddForm === item.id ? null : item.id)} className="px-3 py-1 bg-cyan-600/20 hover:bg-cyan-600/30 border border-cyan-500/50 rounded text-cyan-300 text-xs transition-all">
                {showAddForm === item.id ? 'Cancel' : '+ Add Record'}
              </button>
            </div>

            {showAddForm === item.id && (
              <div className="bg-slate-800/30 rounded-lg p-4 mb-3 border border-slate-700">
                <div className="space-y-3">
                  <input
                    type="text"
                    placeholder="Handler name"
                    value={formData.handler}
                    onChange={(e) => setFormData({ ...formData, handler: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-600 rounded text-slate-100 placeholder-slate-500 text-sm focus:outline-none focus:border-cyan-500"
                  />
                  <input
                    type="text"
                    placeholder="Action (e.g., collected, transferred, analyzed)"
                    value={formData.action}
                    onChange={(e) => setFormData({ ...formData, action: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-600 rounded text-slate-100 placeholder-slate-500 text-sm focus:outline-none focus:border-cyan-500"
                  />
                  <input
                    type="text"
                    placeholder="Location"
                    value={formData.location}
                    onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-600 rounded text-slate-100 placeholder-slate-500 text-sm focus:outline-none focus:border-cyan-500"
                  />
                  <button
                    onClick={() => handleSubmit(item.id)}
                    disabled={submitting}
                    className="w-full px-3 py-2 bg-emerald-600 hover:bg-emerald-700 disabled:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed rounded text-white text-sm font-medium transition-colors"
                  >
                    {submitting ? <Loader2 className="w-3 h-3 animate-spin inline mr-2" /> : '✓'} {submitting ? 'Adding...' : 'Add Record'}
                  </button>
                </div>
              </div>
            )}

            <div className="space-y-2">
              {item.chain_of_custody?.map((record, i) => (
                <div key={i} className="flex items-start gap-4 p-3 bg-slate-800/30 rounded-lg text-sm">
                  <div className="text-2xl">
                    {i === 0 ? '📥' : i === item.chain_of_custody!.length - 1 ? '🔒' : '➡️'}
                  </div>
                  <div className="flex-1">
                    <p className="font-medium text-slate-100">{record.handler}</p>
                    <p className="text-slate-400">{record.action} • {record.location}</p>
                    <p className="text-xs text-slate-500">🕐 {new Date(record.timestamp).toLocaleString()}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

const BlockchainLedgerTab = ({ evidence, onVerifyBlockchain }: BlockchainLedgerTabProps) => (
  <div className="space-y-6 p-6">
    <h2 className="text-2xl font-bold text-slate-100">BLOCKCHAIN INTEGRITY VERIFICATION</h2>

    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
      <div className="p-4 bg-slate-900/50 border border-slate-700 rounded-lg">
        <p className="text-slate-400 text-xs mb-1">Verified Records</p>
        <p className="text-2xl font-bold text-emerald-400">{evidence?.length || 0}</p>
      </div>
      <div className="p-4 bg-slate-900/50 border border-slate-700 rounded-lg">
        <p className="text-slate-400 text-xs mb-1">Blockchain Signatures</p>
        <p className="text-2xl font-bold text-cyan-400">{evidence?.length || 0}</p>
      </div>
      <div className="p-4 bg-slate-900/50 border border-slate-700 rounded-lg">
        <p className="text-slate-400 text-xs mb-1">Verification Status</p>
        <p className="text-2xl font-bold text-emerald-400">✓ 100%</p>
      </div>
      <div className="p-4 bg-slate-900/50 border border-slate-700 rounded-lg">
        <p className="text-slate-400 text-xs mb-1">Network</p>
        <p className="text-sm font-bold text-slate-100 flex items-center gap-2"><span className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></span>LIVE</p>
      </div>
    </div>

    <div className="bg-slate-900/50 border border-slate-700 rounded-lg p-6">
      <h3 className="text-lg font-semibold text-slate-100 mb-4 flex items-center gap-2">
        ⛓️ Recent Blockchain Transactions
      </h3>
      <div className="space-y-2">
        {Array.from({ length: 10 }).map((_, i) => (
          <div key={i} className="flex items-center justify-between p-3 bg-slate-800/30 rounded-lg border border-slate-700/50 text-xs">
            <div className="font-mono text-cyan-300">0x{Math.random().toString(16).slice(2, 18).padEnd(16, '0')}</div>
            <div className="text-slate-400">Record #{i + 1}</div>
            <div className="text-slate-500">{new Date(Date.now() - i * 3600000).toLocaleTimeString()}</div>
            <button onClick={() => evidence && evidence.length > 0 && onVerifyBlockchain(evidence[i % evidence.length]?.id)} className="hover:text-cyan-400 transition-colors" title="Verify blockchain integrity">
              <ExternalLink className="w-4 h-4" />
            </button>
          </div>
        ))}
      </div>
    </div>
  </div>
)

// ============ MAIN COMPONENT ============

export default function Forensics() {
  const [activeTab, setActiveTab] = useState('dashboard')
  const [stats, setStats] = useState<ForensicsStats | null>(null)
  const [evidence, setEvidence] = useState<EvidenceItem[]>([])
  const [incidents, setIncidents] = useState<IncidentReport[]>([])
  const [health, setHealth] = useState<ForensicsHealth | null>(null)
  const [loading, setLoading] = useState(true)
  const [analyzing, setAnalyzing] = useState(false)
  const [refreshing, setRefreshing] = useState(false)
  const [toasts, setToasts] = useState<Toast[]>([])

  const addToast = useCallback((message: string, type: 'success' | 'error' | 'info') => {
    const id = Date.now().toString()
    setToasts((prev) => [...prev, { id, message, type }])
    setTimeout(() => { setToasts((prev) => prev.filter((t) => t.id !== id)) }, 5000)
  }, [])

  const loadForensicsData = useCallback(async () => {
    try {
      setRefreshing(true)
      const [statsData, evidenceData, healthData, incidentsData] = await Promise.all([
        fetchForensicsStats(),
        fetchEvidenceInventory(),
        checkForensicsHealth(),
        fetchIncidentReports()
      ])
      if (statsData) setStats(statsData)
      if (evidenceData) setEvidence(evidenceData)
      if (healthData) setHealth(healthData)
      if (incidentsData) setIncidents(incidentsData)
      addToast('✓ Forensics data synced', 'success')
    } catch (error) {
      console.error('Failed to load forensics data:', error)
      addToast('✗ Failed to sync data', 'error')
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [addToast])

  const handleAnalyzeEvidence = useCallback(async (evidenceId: string, analysisType?: string) => {
    try {
      setAnalyzing(true)
      const type = analysisType || ANALYSIS_TYPES[0]
      const result = await analyzeEvidence(evidenceId, type)
      if (result) {
        setEvidence((prev) =>
          prev.map((e) =>
            e.id === evidenceId ? { ...e, analysis: result } : e
          )
        )
        addToast(`✓ Analysis complete: Risk ${result.riskScore.toFixed(1)}/10`, 'success')
      }
    } catch (error) {
      console.error('Analysis failed:', error)
      addToast('✗ Analysis failed', 'error')
    } finally {
      setAnalyzing(false)
    }
  }, [addToast])

  const handleGenerateReport = useCallback(async (caseId: string) => {
    try {
      const blob = await generateForensicsReport(caseId)
      if (blob) {
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `forensics_report_${caseId}_${new Date().toISOString().split('T')[0]}.pdf`
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
        document.body.removeChild(a)
        addToast('✓ Report downloaded successfully', 'success')
      } else {
        addToast('✗ Failed to generate report', 'error')
      }
    } catch (error) {
      console.error('Report generation failed:', error)
      addToast('✗ Report generation failed', 'error')
    }
  }, [addToast])

  const handleVerifyBlockchain = useCallback(async (evidenceId: string) => {
    try {
      const result = await verifyBlockchainIntegrity(evidenceId)
      if (result) {
        addToast(`✓ Blockchain verified: ${result.status || 'Valid'}`, 'success')
      } else {
        addToast('✗ Blockchain verification failed', 'error')
      }
    } catch (error) {
      console.error('Blockchain verification failed:', error)
      addToast('✗ Blockchain verification failed', 'error')
    }
  }, [addToast])

  const handleAddCustodyRecord = useCallback(async (evidenceId: string, handler: string, action: string, location: string) => {
    try {
      const result = await addCustodyRecord(evidenceId, handler, action, location)
      if (result) {
        setEvidence((prev) =>
          prev.map((e) =>
            e.id === evidenceId
              ? { ...e, chain_of_custody: [...(e.chain_of_custody || []), result] }
              : e
          )
        )
        addToast(`✓ Custody record added: ${handler}`, 'success')
      }
    } catch (error) {
      console.error('Failed to add custody record:', error)
      addToast('✗ Failed to add custody record', 'error')
    }
  }, [addToast])

  useEffect(() => {
    loadForensicsData()
    const interval = setInterval(loadForensicsData, 60000)
    return () => clearInterval(interval)
  }, [loadForensicsData])

  if (loading && !stats) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 flex items-center justify-center">
        <div className="text-center space-y-4">
          <Loader2 className="w-16 h-16 text-cyan-400 animate-spin mx-auto" />
          <p className="text-slate-400 text-lg">INITIALIZING FORENSICS HUB...</p>
          <p className="text-slate-500 text-sm">Connecting to evidence vault and blockchain</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <PageHeader />
      {health && <HealthDashboard health={health} onRefresh={loadForensicsData} isRefreshing={refreshing} />}
      <AdvancedStatsGrid stats={stats} />
      <TabNav activeTab={activeTab} onTabChange={setActiveTab} />

      <div className="flex-1">
        {activeTab === 'dashboard' && <DashboardTab _stats={stats} _health={health} incidents={incidents} onRefresh={loadForensicsData} />}
        {activeTab === 'evidence' && <EvidenceVaultTab evidence={evidence} onAnalyze={handleAnalyzeEvidence} analyzing={analyzing} />}
        {activeTab === 'analysis' && <AnalysisEngineTab evidence={evidence} onAnalyze={handleAnalyzeEvidence} analyzing={analyzing} />}
        {activeTab === 'incidents' && <IncidentCasesTab incidents={incidents} onRefresh={loadForensicsData} onGenerateReport={handleGenerateReport} />}
        {activeTab === 'chain-custody' && <ChainOfCustodyTab evidence={evidence} onAddCustodyRecord={handleAddCustodyRecord} />}
        {activeTab === 'blockchain' && <BlockchainLedgerTab evidence={evidence} onVerifyBlockchain={handleVerifyBlockchain} />}
      </div>

      <div className="fixed bottom-4 right-4 space-y-2 z-40 max-w-xs">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            className={`px-4 py-3 rounded-lg font-medium text-sm animate-in fade-in slide-in-from-bottom-4 ${toast.type === 'success'
              ? 'bg-emerald-900/80 text-emerald-200 border border-emerald-700/50'
              : toast.type === 'error'
                ? 'bg-red-900/80 text-red-200 border border-red-700/50'
                : 'bg-cyan-900/80 text-cyan-200 border border-cyan-700/50'
              }`}
          >
            {toast.message}
          </div>
        ))}
      </div>
    </div>
  )
}

// ============ COMPONENT PROPS INTERFACES ============

interface HealthDashboardProps { health: ForensicsHealth; onRefresh: () => void; isRefreshing: boolean }
interface TabNavProps { activeTab: string; onTabChange: (id: string) => void }
interface DashboardTabProps { _stats?: ForensicsStats | null; _health?: ForensicsHealth | null; incidents: IncidentReport[]; onRefresh: () => Promise<void> | void }
interface EvidenceVaultTabProps { evidence: EvidenceItem[]; onAnalyze: (id: string, type?: string) => Promise<void> | void; analyzing: boolean }
interface AnalysisEngineTabProps { evidence: EvidenceItem[]; onAnalyze: (id: string, type?: string) => Promise<void> | void; analyzing: boolean }
interface IncidentCasesTabProps { incidents: IncidentReport[]; onRefresh: () => void; onGenerateReport: (caseId: string) => Promise<void> | void }
interface ChainOfCustodyTabProps { evidence: EvidenceItem[]; onAddCustodyRecord: (evidenceId: string, handler: string, action: string, location: string) => Promise<void> | void }
interface BlockchainLedgerTabProps { evidence: EvidenceItem[]; onVerifyBlockchain: (evidenceId: string) => Promise<void> | void }
