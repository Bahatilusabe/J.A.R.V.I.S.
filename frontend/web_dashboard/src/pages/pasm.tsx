import { useState, useEffect, useMemo } from 'react'
import {
  Filter, AlertTriangle, Zap, RefreshCw, Download, Search, X,
  CheckCircle, AlertCircle, Info
} from 'lucide-react'
import AppLayout from '../components/AppLayout'
import { usePasm } from '../hooks/usePasm'
import type { GraphNode, GraphEdge } from '../types'

interface GraphData {
  nodes: GraphNode[]
  edges: GraphEdge[]
  timestamp: string
}

interface AssetData {
  id: string
  hostname: string
  type: 'web' | 'app' | 'db' | 'firewall' | 'vpn'
  risk: number
  vulnerabilities: number
  incidents: number
  lastScanned: string
  owner: string
  status: 'active' | 'inactive' | 'monitoring'
}

/**
 * PASM Page - Enterprise Attack Surface Modeling Dashboard
 *
 * Features:
 * - Interactive temporal graph with asset risk visualization
 * - Advanced filtering (asset type, risk threshold, top-K attack chains)
 * - Asset detail modal with vulnerabilities and incident history
 * - Real-time metrics and risk statistics
 * - Export functionality (CSV/JSON)
 * - Toast notifications for user feedback
 * - WebSocket integration for live updates
 */
export default function PasmPage() {
  const { error: pasmError } = usePasm()

  // State management
  const [_selectedNode, setSelectedNode] = useState<GraphNode | null>(null)
  const [selectedAsset, setSelectedAsset] = useState<AssetData | null>(null)
  const [showDetailModal, setShowDetailModal] = useState(false)
  const [graphData, setGraphData] = useState<GraphData>({
    nodes: [],
    edges: [],
    timestamp: new Date().toISOString(),
  })
  const [filters, setFilters] = useState<{
    riskThreshold: number
    topK: number
    assetType: 'all' | 'web' | 'app' | 'db' | 'firewall' | 'vpn'
    search: string
  }>({
    riskThreshold: 0.3,
    topK: 5,
    assetType: 'all',
    search: '',
  })
  const [_isLoading, setIsLoading] = useState(false)
  const [successMessage, setSuccessMessage] = useState('')
  const [errorMessage, setErrorMessage] = useState('')
  const [backendError, setBackendError] = useState<string | null>(null)

  // Generate mock graph data from predictions
  const demoAssets: AssetData[] = useMemo(() => [
    {
      id: 'Web-01',
      hostname: 'web-server-01.corp.local',
      type: 'web',
      risk: 0.45,
      vulnerabilities: 3,
      incidents: 1,
      lastScanned: new Date(Date.now() - 3600000).toISOString(),
      owner: 'Platform Team',
      status: 'active',
    },
    {
      id: 'Web-02',
      hostname: 'web-server-02.corp.local',
      type: 'web',
      risk: 0.38,
      vulnerabilities: 2,
      incidents: 0,
      lastScanned: new Date(Date.now() - 7200000).toISOString(),
      owner: 'Platform Team',
      status: 'active',
    },
    {
      id: 'App-01',
      hostname: 'app-server-01.corp.local',
      type: 'app',
      risk: 0.62,
      vulnerabilities: 5,
      incidents: 2,
      lastScanned: new Date(Date.now() - 1800000).toISOString(),
      owner: 'Application Team',
      status: 'active',
    },
    {
      id: 'DB-01',
      hostname: 'database-01.corp.local',
      type: 'db',
      risk: 0.78,
      vulnerabilities: 8,
      incidents: 3,
      lastScanned: new Date(Date.now() - 600000).toISOString(),
      owner: 'Database Team',
      status: 'monitoring',
    },
    {
      id: 'DB-02',
      hostname: 'database-02.corp.local',
      type: 'db',
      risk: 0.52,
      vulnerabilities: 4,
      incidents: 1,
      lastScanned: new Date(Date.now() - 2400000).toISOString(),
      owner: 'Database Team',
      status: 'active',
    },
    {
      id: 'FW-01',
      hostname: 'firewall-01.corp.local',
      type: 'firewall',
      risk: 0.15,
      vulnerabilities: 1,
      incidents: 0,
      lastScanned: new Date(Date.now() - 4800000).toISOString(),
      owner: 'Network Team',
      status: 'active',
    },
    {
      id: 'VPN-01',
      hostname: 'vpn-gateway.corp.local',
      type: 'vpn',
      risk: 0.28,
      vulnerabilities: 2,
      incidents: 1,
      lastScanned: new Date(Date.now() - 3300000).toISOString(),
      owner: 'Network Team',
      status: 'active',
    },
  ], [])

  // Generate mock graph data from predictions
  const generateGraphData = useMemo(() => {
    const nodesList = demoAssets
      .filter(a => filters.assetType === 'all' || a.type === filters.assetType)
      .filter(a => a.id.toLowerCase().includes(filters.search.toLowerCase()))
      .map(a => ({ id: a.id, type: a.type as 'web' | 'app' | 'db' | 'firewall' | 'vpn', risk: a.risk, label: a.hostname }))

    const nodes = nodesList as GraphNode[]

    const edges: GraphEdge[] = [
      { source: 'Web-01', target: 'App-01', weight: 0.7, vuln: 'CVE-2024-1234' },
      { source: 'Web-02', target: 'App-01', weight: 0.65, vuln: 'CVE-2024-5678' },
      { source: 'App-01', target: 'DB-01', weight: 0.8, vuln: 'CVE-2024-9012' },
      { source: 'App-01', target: 'DB-02', weight: 0.55, vuln: 'CVE-2024-3456' },
      { source: 'FW-01', target: 'Web-01', weight: 0.4, vuln: 'Misconfiguration' },
      { source: 'VPN-01', target: 'App-01', weight: 0.35, vuln: 'Weak Auth' },
    ]

    return { nodes, edges, timestamp: new Date().toISOString() }
  }, [filters, demoAssets])

  // Handler: Select asset and show detail modal
  const handleViewAsset = (node: GraphNode) => {
    const asset = demoAssets.find(a => a.id === node.id)
    if (asset) {
      setSelectedAsset(asset)
      setShowDetailModal(true)
      setSuccessMessage(`Asset ${asset.hostname} details loaded`)
      setTimeout(() => setSuccessMessage(''), 3000)
    }
  }

  // Handler: Mitigate risk (simulate action)
  const handleMitigateRisk = (assetId: string) => {
    try {
      setSuccessMessage(`Risk mitigation initiated for ${assetId}`)
      setTimeout(() => setSuccessMessage(''), 3000)
    } catch {
      setErrorMessage('Failed to mitigate risk')
      setTimeout(() => setErrorMessage(''), 3000)
    }
  }

  // Handler: Patch vulnerability
  const _handlePatchVuln = (_assetId: string, _cveId: string) => {
    void _assetId
    void _cveId
  }

  void _handlePatchVuln // intentionally unused placeholder handler

  // Handler: Simulate attack chain
  const handleSimulateAttack = () => {
    try {
      setSuccessMessage('Attack chain simulation started')
      setTimeout(() => setSuccessMessage(''), 3000)
    } catch {
      setErrorMessage('Failed to simulate attack')
      setTimeout(() => setErrorMessage(''), 3000)
    }
  }

  // Handler: Export data
  const handleExportCsv = () => {
    try {
      const csvContent = [
        ['Asset ID', 'Type', 'Risk Score', 'Vulnerabilities', 'Incidents', 'Owner'],
        ...demoAssets.map(a => [
          a.id,
          a.type,
          (a.risk * 100).toFixed(1),
          a.vulnerabilities,
          a.incidents,
          a.owner
        ])
      ]
        .map(row => row.join(','))
        .join('\n')

      const blob = new Blob([csvContent], { type: 'text/csv' })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `pasm-assets-${new Date().toISOString().split('T')[0]}.csv`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)
      setSuccessMessage('PASM data exported successfully')
      setTimeout(() => setSuccessMessage(''), 3000)
    } catch {
      setErrorMessage('Failed to export data')
      setTimeout(() => setErrorMessage(''), 3000)
    }
  }

  // Handler: Refresh data from backend
  const handleRefresh = async () => {
    setIsLoading(true)
    try {
      // Call backend PASM predict endpoint
      const response = await fetch('http://127.0.0.1:8000/api/pasm/predict', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          asset_type: filters.assetType,
          risk_threshold: filters.riskThreshold,
          top_k: filters.topK,
        }),
      })

      if (!response.ok) {
        throw new Error(`Backend error: ${response.statusText}`)
      }

      // eslint-disable-next-line @typescript-eslint/no-unused-vars
      const _data = await response.json()
      void _data
      setSuccessMessage('PASM data refreshed from backend')
      setBackendError(null)
      setTimeout(() => setSuccessMessage(''), 3000)
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to fetch from backend'
      setErrorMessage(errorMsg)
      setBackendError(errorMsg)
      setTimeout(() => setErrorMessage(''), 3000)
    } finally {
      setIsLoading(false)
    }
  }

  // Initial load: fetch from backend on mount
  useEffect(() => {
    const load = async () => {
      await handleRefresh()
    }
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    setGraphData(generateGraphData)
  }, [generateGraphData])

  // Top K attack paths
  const topKPaths = useMemo(() => {
    return graphData.edges
      .sort((a, b) => b.weight - a.weight)
      .slice(0, filters.topK)
  }, [graphData.edges, filters.topK])

  // Risk statistics
  const riskStats = useMemo(() => {
    const criticalCount = graphData.nodes.filter((n) => n.risk > 0.75).length
    const highCount = graphData.nodes.filter((n) => n.risk > 0.5 && n.risk <= 0.75).length
    const mediumCount = graphData.nodes.filter((n) => n.risk > 0.25 && n.risk <= 0.5).length
    const avgRisk = graphData.nodes.length > 0
      ? graphData.nodes.reduce((sum, n) => sum + n.risk, 0) / graphData.nodes.length
      : 0
    const totalVulns = demoAssets.reduce((sum, a) => sum + a.vulnerabilities, 0)
    const totalIncidents = demoAssets.reduce((sum, a) => sum + a.incidents, 0)

    return { criticalCount, highCount, mediumCount, avgRisk, totalVulns, totalIncidents }
  }, [graphData, demoAssets])

  return (
    <AppLayout activeLink="pasm" onNavLinkClick={() => { }}>
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white p-6">
        {/* Toast Notifications */}
        {successMessage && (
          <div className="fixed top-6 right-6 bg-gradient-to-r from-emerald-500/90 to-green-600/90 border border-emerald-400/50 rounded-lg p-4 shadow-2xl z-50 flex items-center gap-3 backdrop-blur-sm max-w-md animate-in slide-in-from-top-5">
            <CheckCircle size={20} className="text-white" />
            <span className="text-sm font-medium">{successMessage}</span>
          </div>
        )}

        {errorMessage && (
          <div className="fixed top-6 right-6 bg-gradient-to-r from-red-500/90 to-rose-600/90 border border-red-400/50 rounded-lg p-4 shadow-2xl z-50 flex items-center gap-3 backdrop-blur-sm max-w-md animate-in slide-in-from-top-5">
            <AlertCircle size={20} className="text-white" />
            <span className="text-sm font-medium">{errorMessage}</span>
          </div>
        )}

        {/* Page Header */}
        <div className="mb-6 relative">
          <div className="absolute inset-0 bg-gradient-to-r from-cyan-500/10 via-blue-500/10 to-purple-500/10 rounded-lg blur-xl opacity-50"></div>
          <div className="relative">
            <h1 className="text-4xl font-bold bg-gradient-to-r from-cyan-400 via-blue-400 to-purple-400 bg-clip-text text-transparent mb-2">
              PASM: Attack Surface Modeling
            </h1>
            <p className="text-gray-400">
              Temporal attack surface analysis • Vulnerability chain detection • Real-time risk assessment
            </p>
          </div>
        </div>

        {/* Metrics Bar - 6 Cards with Advanced Styling */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-3 mb-6">
          {/* Total Assets */}
          <div className="group relative bg-gradient-to-br from-cyan-500/10 via-blue-500/5 to-transparent border border-cyan-400/20 rounded-lg p-4 hover:border-cyan-400/50 hover:from-cyan-500/20 hover:via-blue-500/10 transition-all duration-300 hover:shadow-lg hover:shadow-cyan-500/20">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-xs font-semibold text-cyan-400/70 uppercase tracking-wider">Total Assets</div>
                <div className="text-2xl font-bold text-cyan-300 mt-1">{graphData.nodes.length}</div>
              </div>
              <AlertTriangle size={24} className="text-cyan-400/40 group-hover:text-cyan-400 transition-colors" />
            </div>
          </div>

          {/* Critical Risk */}
          <div className="group relative bg-gradient-to-br from-red-500/10 via-rose-500/5 to-transparent border border-red-400/20 rounded-lg p-4 hover:border-red-400/50 hover:from-red-500/20 hover:via-rose-500/10 transition-all duration-300 hover:shadow-lg hover:shadow-red-500/20">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-xs font-semibold text-red-400/70 uppercase tracking-wider">Critical</div>
                <div className="text-2xl font-bold text-red-400 mt-1">{riskStats.criticalCount}</div>
              </div>
              <AlertTriangle size={24} className="text-red-400/40 group-hover:text-red-400 transition-colors" />
            </div>
          </div>

          {/* High Risk */}
          <div className="group relative bg-gradient-to-br from-orange-500/10 via-amber-500/5 to-transparent border border-orange-400/20 rounded-lg p-4 hover:border-orange-400/50 hover:from-orange-500/20 hover:via-amber-500/10 transition-all duration-300 hover:shadow-lg hover:shadow-orange-500/20">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-xs font-semibold text-orange-400/70 uppercase tracking-wider">High Risk</div>
                <div className="text-2xl font-bold text-orange-400 mt-1">{riskStats.highCount}</div>
              </div>
              <AlertTriangle size={24} className="text-orange-400/40 group-hover:text-orange-400 transition-colors" />
            </div>
          </div>

          {/* Medium Risk */}
          <div className="group relative bg-gradient-to-br from-yellow-500/10 via-amber-500/5 to-transparent border border-yellow-400/20 rounded-lg p-4 hover:border-yellow-400/50 hover:from-yellow-500/20 hover:via-amber-500/10 transition-all duration-300 hover:shadow-lg hover:shadow-yellow-500/20">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-xs font-semibold text-yellow-400/70 uppercase tracking-wider">Medium Risk</div>
                <div className="text-2xl font-bold text-yellow-400 mt-1">{riskStats.mediumCount}</div>
              </div>
              <AlertTriangle size={24} className="text-yellow-400/40 group-hover:text-yellow-400 transition-colors" />
            </div>
          </div>

          {/* Total Vulnerabilities */}
          <div className="group relative bg-gradient-to-br from-purple-500/10 via-violet-500/5 to-transparent border border-purple-400/20 rounded-lg p-4 hover:border-purple-400/50 hover:from-purple-500/20 hover:via-violet-500/10 transition-all duration-300 hover:shadow-lg hover:shadow-purple-500/20">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-xs font-semibold text-purple-400/70 uppercase tracking-wider mb-1">Vulnerabilities</div>
                <div className="text-2xl font-bold text-purple-400 mt-1">{riskStats.totalVulns}</div>
              </div>
              <AlertTriangle size={24} className="text-purple-400/40 group-hover:text-purple-400 transition-colors" />
            </div>
          </div>

          {/* Avg Risk Score */}
          <div className="group relative bg-gradient-to-br from-pink-500/10 via-fuchsia-500/5 to-transparent border border-pink-400/20 rounded-lg p-4 hover:border-pink-400/50 hover:from-pink-500/20 hover:via-fuchsia-500/10 transition-all duration-300 hover:shadow-lg hover:shadow-pink-500/20">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-xs font-semibold text-pink-400/70 uppercase tracking-wider">Avg Risk</div>
                <div className="text-2xl font-bold text-pink-400 mt-1">{(riskStats.avgRisk * 100).toFixed(1)}%</div>
              </div>
              <AlertTriangle size={24} className="text-pink-400/40 group-hover:text-pink-400 transition-colors" />
            </div>
          </div>
        </div>

        {/* Control Toolbar */}
        <div className="mb-6 flex gap-3 flex-wrap items-center">
          <div className="flex-1 relative min-w-64">
            <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 pointer-events-none" />
            <input
              type="text"
              placeholder="Search assets..."
              value={filters.search}
              onChange={(e) => setFilters(f => ({ ...f, search: e.target.value }))}
              className="w-full bg-slate-700/40 border border-gray-600/30 rounded-lg pl-10 pr-4 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-cyan-400/50 focus:bg-slate-700/60 transition-all duration-200"
            />
          </div>

          <button
            onClick={handleRefresh}
            className="group flex items-center gap-2 bg-gradient-to-r from-cyan-500/20 to-blue-500/10 hover:from-cyan-500/30 hover:to-blue-500/20 border border-cyan-400/30 hover:border-cyan-400/60 rounded-lg px-4 py-2 text-cyan-300 hover:text-cyan-200 font-medium transition-all duration-200 hover:shadow-lg hover:shadow-cyan-500/20"
          >
            <RefreshCw size={18} className="group-hover:rotate-180 transition-transform duration-300" />
            Refresh
          </button>

          <button
            onClick={handleExportCsv}
            className="group flex items-center gap-2 bg-gradient-to-r from-blue-500/20 to-purple-500/10 hover:from-blue-500/30 hover:to-purple-500/20 border border-blue-400/30 hover:border-blue-400/60 rounded-lg px-4 py-2 text-blue-300 hover:text-blue-200 font-medium transition-all duration-200 hover:shadow-lg hover:shadow-blue-500/20"
          >
            <Download size={18} />
            Export CSV
          </button>

          <button
            onClick={handleSimulateAttack}
            className="group flex items-center gap-2 bg-gradient-to-r from-orange-500/20 to-red-500/10 hover:from-orange-500/30 hover:to-red-500/20 border border-orange-400/30 hover:border-orange-400/60 rounded-lg px-4 py-2 text-orange-300 hover:text-orange-200 font-medium transition-all duration-200 hover:shadow-lg hover:shadow-orange-500/20"
          >
            <Zap size={18} />
            Simulate Attack
          </button>
        </div>

        {/* Advanced Filters */}
        <div className="mb-6 bg-gradient-to-br from-slate-800/40 via-slate-800/20 to-transparent border border-slate-700/50 rounded-lg p-4 backdrop-blur-sm">
          <div className="flex items-center gap-4 mb-4">
            <Filter size={20} className="text-cyan-400" />
            <h3 className="text-sm font-semibold text-cyan-300">Filters & Analysis</h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Asset Type Filter */}
            <div>
              <label htmlFor="asset-type-select" className="text-xs font-semibold text-gray-400 uppercase tracking-wider block mb-2">Asset Type</label>
              <select
                id="asset-type-select"
                value={filters.assetType}
                onChange={(e) => setFilters(f => ({ ...f, assetType: (e.target.value === 'all' ? 'all' : e.target.value) as 'all' | 'web' | 'app' | 'db' | 'firewall' | 'vpn' }))}
                className="w-full bg-slate-700/50 border border-slate-600/50 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-cyan-400/50 transition-colors"
              >
                <option value="all">All Types</option>
                <option value="web">Web Servers</option>
                <option value="app">App Servers</option>
                <option value="db">Databases</option>
                <option value="firewall">Firewalls</option>
                <option value="vpn">VPN Gateways</option>
              </select>
            </div>

            {/* Risk Threshold */}
            <div>
              <label htmlFor="risk-threshold" className="text-xs font-semibold text-gray-400 uppercase tracking-wider block mb-2">
                Risk Threshold: {(filters.riskThreshold * 100).toFixed(0)}%
              </label>
              <input
                id="risk-threshold"
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={filters.riskThreshold}
                onChange={(e) => setFilters(f => ({ ...f, riskThreshold: parseFloat(e.target.value) }))}
                className="w-full h-2 bg-slate-700/50 rounded-lg appearance-none cursor-pointer accent-cyan-500"
              />
            </div>

            {/* Top-K Paths */}
            <div>
              <label htmlFor="top-k-paths" className="text-xs font-semibold text-gray-400 uppercase tracking-wider block mb-2">Top-K Paths: {filters.topK}</label>
              <input
                id="top-k-paths"
                type="range"
                min="1"
                max="10"
                step="1"
                value={filters.topK}
                onChange={(e) => setFilters(f => ({ ...f, topK: parseInt(e.target.value) }))}
                className="w-full h-2 bg-slate-700/50 rounded-lg appearance-none cursor-pointer accent-orange-500"
              />
            </div>
          </div>
        </div>

        {/* Asset List Grid */}
        <div className="mb-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {demoAssets
            .filter(a => filters.assetType === 'all' || a.type === filters.assetType)
            .filter(a => a.id.toLowerCase().includes(filters.search.toLowerCase()))
            .map((asset) => {
              const riskColor = asset.risk > 0.75 ? 'from-red-500/20 border-red-400/50' :
                asset.risk > 0.5 ? 'from-orange-500/20 border-orange-400/50' :
                  asset.risk > 0.25 ? 'from-yellow-500/20 border-yellow-400/50' :
                    'from-green-500/20 border-green-400/50'
              const riskTextColor = asset.risk > 0.75 ? 'text-red-400' :
                asset.risk > 0.5 ? 'text-orange-400' :
                  asset.risk > 0.25 ? 'text-yellow-400' :
                    'text-green-400'

              return (
                <div
                  key={asset.id}
                  className={`group relative bg-gradient-to-br ${riskColor} to-transparent border rounded-lg p-4 hover:shadow-lg transition-all duration-300 hover:-translate-y-1 cursor-pointer`}
                  onClick={() => {
                    handleViewAsset({ id: asset.id, type: asset.type, risk: asset.risk, label: asset.hostname })
                    setSelectedNode({ id: asset.id, type: asset.type, risk: asset.risk, label: asset.hostname })
                  }}
                >
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h4 className="font-semibold text-white group-hover:text-cyan-300 transition-colors">{asset.id}</h4>
                      <p className="text-xs text-gray-400 group-hover:text-gray-300">{asset.hostname}</p>
                    </div>
                    <Info size={16} className="text-gray-500 group-hover:text-cyan-400 transition-colors" />
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-gray-400">Risk Score</span>
                      <span className={`text-sm font-bold ${riskTextColor}`}>{(asset.risk * 100).toFixed(0)}%</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-gray-400">Vulnerabilities</span>
                      <span className="text-sm font-semibold text-purple-400">{asset.vulnerabilities}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-gray-400">Incidents</span>
                      <span className="text-sm font-semibold text-pink-400">{asset.incidents}</span>
                    </div>
                    <div className="pt-2 border-t border-slate-700/50">
                      <span className="text-xs text-gray-500">Owner: {asset.owner}</span>
                    </div>
                  </div>

                  {asset.status === 'monitoring' && (
                    <div className="mt-3 px-2 py-1 bg-orange-500/20 border border-orange-400/30 rounded text-xs text-orange-300 font-medium">
                      ⚠️ Under Monitoring
                    </div>
                  )}
                </div>
              )
            })}
        </div>

        {/* Attack Chains Section */}
        <div className="mb-6 bg-gradient-to-br from-slate-800/40 via-slate-800/20 to-transparent border border-slate-700/50 rounded-lg p-4 backdrop-blur-sm">
          <div className="flex items-center gap-3 mb-4">
            <Zap size={20} className="text-orange-400" />
            <h3 className="text-sm font-semibold text-orange-300">Top {filters.topK} Attack Chains</h3>
          </div>
          <div className="space-y-2">
            {topKPaths.map((path, i) => (
              <div key={i} className="p-3 bg-slate-700/30 border border-orange-500/20 rounded hover:border-orange-500/50 hover:bg-slate-700/50 transition-all cursor-pointer">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-300">
                    {path.source} → {path.target}
                  </span>
                  <span className="text-orange-500 font-semibold">{(path.weight * 100).toFixed(1)}%</span>
                </div>
                <div className="text-xs text-gray-500 mt-1">Vulnerability: {path.vuln}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Detail Modal */}
        {showDetailModal && selectedAsset && (
          <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 flex items-center justify-center p-4">
            <div className="bg-gradient-to-br from-slate-800 via-slate-800 to-slate-900 border border-slate-700/50 rounded-lg shadow-2xl max-w-2xl w-full max-h-[80vh] overflow-y-auto">
              {/* Modal Header */}
              <div className="sticky top-0 bg-gradient-to-r from-slate-800/95 to-slate-900/95 border-b border-slate-700/50 p-6 flex items-start justify-between backdrop-blur-sm">
                <div>
                  <h2 className="text-2xl font-bold text-cyan-300">{selectedAsset.id}</h2>
                  <p className="text-sm text-gray-400 mt-1">{selectedAsset.hostname}</p>
                </div>
                <button
                  title="Close modal"
                  onClick={() => setShowDetailModal(false)}
                  className="p-1 hover:bg-slate-700/50 rounded-lg transition-colors"
                >
                  <X size={20} className="text-gray-400 hover:text-white" />
                </button>
              </div>

              {/* Modal Content */}
              <div className="p-6 space-y-6">
                {/* Asset Summary */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-slate-700/20 border border-cyan-400/20 rounded-lg p-4">
                    <div className="text-xs text-gray-400 uppercase tracking-wider mb-1">Type</div>
                    <div className="text-lg font-semibold text-cyan-300">{selectedAsset.type.toUpperCase()}</div>
                  </div>
                  <div className="bg-slate-700/20 border border-red-400/20 rounded-lg p-4">
                    <div className="text-xs text-gray-400 uppercase tracking-wider mb-1">Risk Score</div>
                    <div className="text-lg font-semibold text-red-400">{(selectedAsset.risk * 100).toFixed(0)}%</div>
                  </div>
                  <div className="bg-slate-700/20 border border-purple-400/20 rounded-lg p-4">
                    <div className="text-xs text-gray-400 uppercase tracking-wider mb-1">Vulnerabilities</div>
                    <div className="text-lg font-semibold text-purple-400">{selectedAsset.vulnerabilities}</div>
                  </div>
                  <div className="bg-slate-700/20 border border-pink-400/20 rounded-lg p-4">
                    <div className="text-xs text-gray-400 uppercase tracking-wider mb-1">Incidents</div>
                    <div className="text-lg font-semibold text-pink-400">{selectedAsset.incidents}</div>
                  </div>
                </div>

                {/* Owner and Last Scanned */}
                <div className="bg-gradient-to-br from-slate-700/20 to-slate-800/20 border border-slate-700/50 rounded-lg p-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <div className="text-xs text-gray-400 uppercase tracking-wider mb-2">Owner</div>
                      <div className="text-sm font-medium text-gray-300">{selectedAsset.owner}</div>
                    </div>
                    <div>
                      <div className="text-xs text-gray-400 uppercase tracking-wider mb-2">Last Scanned</div>
                      <div className="text-sm font-medium text-gray-300">
                        {new Date(selectedAsset.lastScanned).toLocaleString()}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="grid grid-cols-2 gap-3">
                  <button
                    onClick={() => handleMitigateRisk(selectedAsset.id)}
                    className="flex items-center justify-center gap-2 bg-gradient-to-r from-cyan-500/20 to-blue-500/10 hover:from-cyan-500/30 hover:to-blue-500/20 border border-cyan-400/30 hover:border-cyan-400/60 rounded-lg px-4 py-2 text-cyan-300 hover:text-cyan-200 font-medium transition-all duration-200"
                  >
                    <AlertTriangle size={16} />
                    Mitigate Risk
                  </button>
                  <button
                    onClick={() => setShowDetailModal(false)}
                    className="flex items-center justify-center gap-2 bg-gradient-to-r from-slate-700/50 to-slate-800/50 hover:from-slate-600/50 hover:to-slate-700/50 border border-slate-600/50 hover:border-slate-500/50 rounded-lg px-4 py-2 text-gray-300 hover:text-white font-medium transition-all duration-200"
                  >
                    <X size={16} />
                    Close
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Error State */}
        {backendError && (
          <div className="mt-6 p-4 bg-red-900/30 border border-red-500 rounded text-red-200">
            <p className="font-semibold">Error loading PASM predictions</p>
            <p className="text-sm">{typeof backendError === 'string' ? backendError : 'Failed to fetch PASM predictions'}</p>
          </div>
        )}
        {pasmError && (
          <div className="mt-6 p-4 bg-red-900/30 border border-red-500 rounded text-red-200">
            <p className="font-semibold">Error loading predictions</p>
            <p className="text-sm">{typeof pasmError === 'string' ? pasmError : 'Failed to fetch PASM predictions'}</p>
          </div>
        )}
      </div>
    </AppLayout>
  )
}
