import { useState, useEffect } from 'react'
import {
  Network,
  Globe,
  Lock,
  Activity,
  TrendingUp,
  AlertCircle,
  CheckCircle2,
  Clock,
  Zap,
  GitBranch,
  Database,
  BarChart3,
  Filter,
  Search,
  Shield,
  Layers,
  Loader,
  X,
} from 'lucide-react'
import AppLayout from '../components/AppLayout'

// Toast notification component
interface Toast {
  id: string
  message: string
  type: 'success' | 'error' | 'info'
  duration?: number
}

interface FederationNode {
  id: string
  country: string
  tag: string
  sync_health: number
  trust_score: number
  last_ledger: string
  last_sync: string
  active?: boolean
}

interface FederatedModel {
  id: string
  version: string
  node_id: string
  created_at: string
  status: 'training' | 'aggregated' | 'validated'
}

interface NodeHistory {
  timestamp: string
  node_id: string
  sync_health: number
  trust_score: number
  last_ledger: string
  active: boolean
}

interface NetworkStats {
  total_nodes: number
  active_nodes: number
  network_health: number
  network_trust: number
  total_models: number
  aggregation_status: string
  privacy_level: number
  sync_efficiency: number
}

export default function Federation() {
  const [nodes, setNodes] = useState<FederationNode[]>([])
  const [models, setModels] = useState<FederatedModel[]>([])
  const [selectedNode, setSelectedNode] = useState<FederationNode | null>(null)
  const [nodeHistory, setNodeHistory] = useState<NodeHistory[]>([])
  const [stats, setStats] = useState<NetworkStats>({
    total_nodes: 0,
    active_nodes: 0,
    network_health: 0,
    network_trust: 0,
    total_models: 0,
    aggregation_status: 'idle',
    privacy_level: 0,
    sync_efficiency: 0,
  })
  const [viewMode, setViewMode] = useState<'network' | 'models' | 'analytics'>('network')
  const [showFilters, setShowFilters] = useState(false)
  const [filters, setFilters] = useState({
    country: 'all',
    healthMin: 0.7,
    trustMin: 0.7,
    syncStatus: 'all', // all, synced, syncing, failed
  })
  const [isAggregating, setIsAggregating] = useState(false)
  const [aggregationProgress, setAggregationProgress] = useState(0)
  
  // Loading states for each action
  const [loadingSync, setLoadingSync] = useState<string | null>(null)
  const [isLoadingData, setIsLoadingData] = useState(false)
  const [loadingHistory, setLoadingHistory] = useState(false)
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

  // Load federation data
  useEffect(() => {
    loadFederationData()
    const interval = setInterval(loadFederationData, 10000) // Refresh every 10s
    return () => clearInterval(interval)
  }, [])

  const loadFederationData = async () => {
    try {
      setIsLoadingData(true)
      // Fetch nodes from backend
      const nodesResponse = await fetch('http://127.0.0.1:8000/api/federation/nodes')
      if (!nodesResponse.ok) throw new Error('Failed to fetch nodes')
      const nodesData = await nodesResponse.json()
      setNodes(nodesData.nodes)

      // Fetch models from backend
      const modelsResponse = await fetch('http://127.0.0.1:8000/api/federation/models')
      if (!modelsResponse.ok) throw new Error('Failed to fetch models')
      const modelsData = await modelsResponse.json()
      setModels(modelsData.models)

      // Fetch stats from backend
      const statsResponse = await fetch('http://127.0.0.1:8000/api/federation/stats')
      if (!statsResponse.ok) throw new Error('Failed to fetch stats')
      const statsData = await statsResponse.json()
      setStats({
        total_nodes: statsData.total_nodes,
        active_nodes: statsData.active_nodes,
        network_health: statsData.network_health,
        network_trust: statsData.network_trust,
        total_models: statsData.total_models,
        aggregation_status: statsData.aggregation_status,
        privacy_level: statsData.privacy_level,
        sync_efficiency: statsData.sync_efficiency,
      })
      setIsLoadingData(false)
    } catch (error) {
      console.error('Failed to load federation data:', error)
      setIsLoadingData(false)
      // Fallback to demo data if API is unavailable
      const mockNodes: FederationNode[] = [
        {
          id: 'node-us-1',
          country: 'USA',
          tag: 'us-east',
          sync_health: 0.95,
          trust_score: 0.92,
          last_ledger: 'block-12345',
          last_sync: new Date().toISOString(),
          active: true,
        },
        {
          id: 'node-eu-1',
          country: 'EU',
          tag: 'eu-central',
          sync_health: 0.88,
          trust_score: 0.85,
          last_ledger: 'block-12340',
          last_sync: new Date(Date.now() - 120000).toISOString(),
          active: true,
        },
        {
          id: 'node-asia-1',
          country: 'ASIA',
          tag: 'asia-pacific',
          sync_health: 0.91,
          trust_score: 0.89,
          last_ledger: 'block-12342',
          last_sync: new Date(Date.now() - 300000).toISOString(),
          active: true,
        },
      ]
      setNodes(mockNodes)
      setStats({
        total_nodes: mockNodes.length,
        active_nodes: mockNodes.filter((n) => n.active).length,
        network_health: 0.91,
        network_trust: 0.89,
        total_models: 3,
        aggregation_status: 'completed',
        privacy_level: 98,
        sync_efficiency: 94,
      })
      addToast('Using demo data - Backend unavailable', 'info')
    }
  }

  const handleSelectNode = async (node: FederationNode) => {
    setSelectedNode(node)
    try {
      setLoadingHistory(true)
      // Fetch node history from backend
      const historyResponse = await fetch(`http://127.0.0.1:8000/api/federation/nodes/${node.id}/history?limit=24`)
      if (!historyResponse.ok) throw new Error('Failed to fetch history')
      const historyData = await historyResponse.json()
      setNodeHistory(historyData.history)
      setLoadingHistory(false)
    } catch (error) {
      console.error('Failed to fetch node history:', error)
      setLoadingHistory(false)
      addToast('Failed to load node history - Using mock data', 'error')
      // Fallback to mock history
      const mockHistory: NodeHistory[] = Array.from({ length: 24 }, (_, i) => ({
        timestamp: new Date(Date.now() - i * 3600000).toISOString(),
        node_id: node.id,
        sync_health: node.sync_health + (Math.random() - 0.5) * 0.1,
        trust_score: node.trust_score + (Math.random() - 0.5) * 0.1,
        last_ledger: `block-${12345 - i}`,
        active: true,
      }))
      setNodeHistory(mockHistory.reverse())
    }
  }

  const handleTriggerSync = async (nodeId: string) => {
    try {
      setLoadingSync(nodeId)
      addToast(`Syncing node ${nodeId}...`, 'info')
      
      const response = await fetch(`http://127.0.0.1:8000/api/federation/nodes/${nodeId}/sync`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      })
      if (!response.ok) throw new Error('Failed to trigger sync')
      const data = await response.json()
      console.log('Sync triggered:', data)
      
      setLoadingSync(null)
      addToast(`Node ${nodeId} synced successfully!`, 'success')
      
      // Refresh data after sync
      loadFederationData()
    } catch (error) {
      console.error('Failed to trigger sync:', error)
      setLoadingSync(null)
      addToast(`Failed to sync node ${nodeId}`, 'error')
    }
  }

  const handleTriggerAggregation = async () => {
    try {
      setIsAggregating(true)
      setAggregationProgress(0)
      addToast('Starting model aggregation...', 'info')

      const response = await fetch('http://127.0.0.1:8000/api/federation/aggregate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      })
      if (!response.ok) throw new Error('Failed to trigger aggregation')
      const data = await response.json()
      console.log('Aggregation triggered:', data)

      // Simulate progress updates
      for (let i = 0; i <= 100; i += 10) {
        await new Promise((resolve) => setTimeout(resolve, 300))
        setAggregationProgress(i)
      }

      setAggregationProgress(100)
      setIsAggregating(false)
      addToast('Model aggregation completed successfully!', 'success')
      
      // Refresh data after aggregation
      loadFederationData()
    } catch (error) {
      console.error('Failed to trigger aggregation:', error)
      setIsAggregating(false)
      addToast('Failed to trigger aggregation', 'error')
    }
  }

  const filteredNodes = nodes.filter((node) => {
    if (filters.country !== 'all' && node.country !== filters.country) return false
    if (node.sync_health < filters.healthMin) return false
    if (node.trust_score < filters.trustMin) return false
    return true
  })

  const getHealthStatus = (health: number) => {
    if (health >= 0.9) return { color: 'text-green-400', bg: 'bg-green-400/10', label: 'Excellent' }
    if (health >= 0.8) return { color: 'text-cyan-400', bg: 'bg-cyan-400/10', label: 'Good' }
    if (health >= 0.7) return { color: 'text-yellow-400', bg: 'bg-yellow-400/10', label: 'Fair' }
    return { color: 'text-red-400', bg: 'bg-red-400/10', label: 'Poor' }
  }

  const getTrustBadgeColor = (score: number) => {
    if (score >= 0.9) return 'from-green-500 to-emerald-500'
    if (score >= 0.8) return 'from-cyan-500 to-blue-500'
    if (score >= 0.7) return 'from-yellow-500 to-amber-500'
    return 'from-red-500 to-orange-500'
  }

  return (
    <AppLayout>
      {/* Toast Notifications Container */}
      <div className="fixed top-4 right-4 z-50 flex flex-col gap-2 pointer-events-none">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            className={`flex items-center gap-3 px-4 py-3 rounded-lg shadow-lg backdrop-blur pointer-events-auto animate-in fade-in slide-in-from-top-2 duration-300 ${
              toast.type === 'success'
                ? 'bg-green-500/90 text-white border border-green-400/30'
                : toast.type === 'error'
                  ? 'bg-red-500/90 text-white border border-red-400/30'
                  : 'bg-blue-500/90 text-white border border-blue-400/30'
            }`}
          >
            <div className="flex-1">
              <p className="text-sm font-medium">{toast.message}</p>
            </div>
            <button
              onClick={() => removeToast(toast.id)}
              className="text-white/70 hover:text-white transition-colors"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        ))}
      </div>

      <div className="h-full overflow-auto bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-blue-400 to-purple-400 mb-2">
                Federated Learning Hub
              </h1>
              <p className="text-slate-400 flex items-center gap-2">
                <Globe className="h-4 w-4" />
                Decentralized AI Model Training Network
              </p>
            </div>
            <button
              onClick={handleTriggerAggregation}
              disabled={isAggregating}
              className="px-6 py-3 bg-gradient-to-r from-cyan-500 to-blue-500 text-white rounded-lg font-semibold hover:shadow-lg hover:shadow-cyan-500/50 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              title="Trigger federated model aggregation across all nodes"
            >
              {isAggregating ? (
                <>
                  <Loader className="h-4 w-4 animate-spin" />
                  Aggregating {aggregationProgress}%
                </>
              ) : (
                <>
                  <Zap className="h-4 w-4" />
                  Trigger Aggregation
                </>
              )}
            </button>
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-4 backdrop-blur">
              <p className="text-xs text-slate-400 mb-2">Total Nodes</p>
              <p className="text-2xl font-bold text-cyan-400">{stats.total_nodes}</p>
              <p className="text-xs text-green-400 mt-1">
                {stats.active_nodes} {stats.active_nodes === stats.total_nodes ? 'all active' : 'active'}
              </p>
            </div>
            <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-4 backdrop-blur">
              <p className="text-xs text-slate-400 mb-2">Network Health</p>
              <p className="text-2xl font-bold text-green-400">{(stats.network_health * 100).toFixed(0)}%</p>
              <div className="w-full bg-slate-700/50 h-1 rounded-full mt-2">
                {/* Dynamic progress width using CSS custom property */}
                <div className="metric-progress-bar" style={{ '--progress-width': `${stats.network_health * 100}%` } as React.CSSProperties} />
              </div>
            </div>
            <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-4 backdrop-blur">
              <p className="text-xs text-slate-400 mb-2">Trust Score</p>
              <p className="text-2xl font-bold text-blue-400">{(stats.network_trust * 100).toFixed(0)}%</p>
              <p className="text-xs text-slate-400 mt-1">Network-wide average</p>
            </div>
            <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-4 backdrop-blur">
              <p className="text-xs text-slate-400 mb-2">Privacy Level</p>
              <p className="text-2xl font-bold text-purple-400">{stats.privacy_level}%</p>
              <div className="w-full bg-slate-700/50 h-1 rounded-full mt-2">
                <div className="metric-progress-bar-privacy" style={{ '--progress-width': `${stats.privacy_level}%` } as React.CSSProperties} />
              </div>
            </div>
          </div>
        </div>

        {/* View Tabs */}
        <div className="flex gap-3 mb-6">
          {[
            { id: 'network', label: 'Network View', icon: Network },
            { id: 'models', label: 'Models', icon: GitBranch },
            { id: 'analytics', label: 'Analytics', icon: BarChart3 },
          ].map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setViewMode(id as 'network' | 'models' | 'analytics')}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${
                viewMode === id
                  ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/50'
                  : 'bg-slate-800/50 text-slate-400 border border-slate-700/50 hover:border-slate-600/50'
              }`}
            >
              <Icon className="h-4 w-4" />
              {label}
            </button>
          ))}
        </div>

        {/* Network View */}
        {viewMode === 'network' && (
          <div className="space-y-6 relative">
            {isLoadingData && (
              <div className="absolute inset-0 bg-black/30 backdrop-blur-sm rounded-lg flex items-center justify-center z-40">
                <div className="flex flex-col items-center gap-2">
                  <Loader className="h-8 w-8 animate-spin text-cyan-400" />
                  <p className="text-sm text-slate-300">Loading network data...</p>
                </div>
              </div>
            )}
            {/* Control Bar */}
            <div className="flex gap-3 flex-wrap lg:flex-row lg:items-center justify-between">
              <div className="relative flex-1 min-w-[200px]">
                <Search className="absolute left-3 top-3 h-4 w-4 text-slate-500" />
                <input
                  type="text"
                  placeholder="Search nodes..."
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
                    <label className="text-xs text-slate-400 mb-2 block">Country</label>
                    <select
                      title="Filter by country"
                      value={filters.country}
                      onChange={(e) => setFilters({ ...filters, country: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded text-slate-200 text-sm"
                    >
                      <option value="all">All Countries</option>
                      <option value="USA">USA</option>
                      <option value="EU">EU</option>
                      <option value="ASIA">ASIA</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-xs text-slate-400 mb-2 block">Min Health: {filters.healthMin.toFixed(2)}</label>
                    <input
                      type="range"
                      title="Filter by minimum health score"
                      min="0"
                      max="1"
                      step="0.05"
                      value={filters.healthMin}
                      onChange={(e) => setFilters({ ...filters, healthMin: parseFloat(e.target.value) })}
                      className="w-full"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-slate-400 mb-2 block">Min Trust: {filters.trustMin.toFixed(2)}</label>
                    <input
                      type="range"
                      title="Filter by minimum trust score"
                      min="0"
                      max="1"
                      step="0.05"
                      value={filters.trustMin}
                      onChange={(e) => setFilters({ ...filters, trustMin: parseFloat(e.target.value) })}
                      className="w-full"
                    />
                  </div>
                </div>
              </div>
            )}

            {/* Nodes Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredNodes.map((node) => {
                const healthStatus = getHealthStatus(node.sync_health)
                const trustBg = getTrustBadgeColor(node.trust_score)
                const lastSyncMinutesAgo = Math.floor((Date.now() - new Date(node.last_sync).getTime()) / 60000)
                const isLoadingThisNode = selectedNode?.id === node.id && loadingHistory

                return (
                  <div
                    key={node.id}
                    onClick={() => !isLoadingThisNode && handleSelectNode(node)}
                    className={`bg-slate-800/40 border rounded-lg p-4 backdrop-blur cursor-pointer transition-all hover:border-cyan-500/50 ${
                      selectedNode?.id === node.id ? 'border-cyan-500/50 ring-2 ring-cyan-500/20' : 'border-slate-700/50'
                    } ${isLoadingThisNode ? 'opacity-70 cursor-wait' : ''}`}
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <div className={`p-2 rounded-lg ${healthStatus.bg}`}>
                          {isLoadingThisNode ? (
                            <Loader className="h-4 w-4 animate-spin text-cyan-400" />
                          ) : (
                            <Globe className={`h-4 w-4 ${healthStatus.color}`} />
                          )}
                        </div>
                        <div>
                          <h3 className="font-semibold text-slate-100">{node.tag}</h3>
                          <p className="text-xs text-slate-500">{node.id}</p>
                        </div>
                      </div>
                      {node.active && <CheckCircle2 className="h-4 w-4 text-green-400" />}
                    </div>

                    {/* Metrics */}
                    <div className="space-y-3 mb-4">
                      <div>
                        <div className="flex justify-between items-center mb-1">
                          <span className="text-xs text-slate-400">Sync Health</span>
                          <span className="text-xs font-semibold text-cyan-400">{(node.sync_health * 100).toFixed(0)}%</span>
                        </div>
                        <div className="w-full bg-slate-700/50 h-1.5 rounded-full">
                          <div
                            className="metric-progress-bar"
                            style={{ '--progress-width': `${node.sync_health * 100}%` } as React.CSSProperties}
                          />
                        </div>
                      </div>

                      <div>
                        <div className="flex justify-between items-center mb-1">
                          <span className="text-xs text-slate-400">Trust Score</span>
                          <span className={`text-xs font-semibold bg-gradient-to-r ${trustBg} bg-clip-text text-transparent`}>
                            {(node.trust_score * 100).toFixed(0)}%
                          </span>
                        </div>
                        <div className="w-full bg-slate-700/50 h-1.5 rounded-full">
                          <div
                            className="metric-progress-bar-trust"
                            style={{ '--progress-width': `${node.trust_score * 100}%`, background: `linear-gradient(to right, rgb(${trustBg.includes('green') ? '34, 197, 94' : trustBg.includes('cyan') ? '6, 182, 212' : trustBg.includes('yellow') ? '234, 179, 8' : '239, 68, 68'}))`} as React.CSSProperties}
                          />
                        </div>
                      </div>
                    </div>

                    {/* Info */}
                    <div className="text-xs text-slate-400 space-y-1 mb-4 pb-4 border-b border-slate-700/50">
                      <div className="flex items-center gap-2">
                        <Clock className="h-3 w-3" />
                        Last sync: {lastSyncMinutesAgo}m ago
                      </div>
                      <div className="flex items-center gap-2">
                        <Database className="h-3 w-3" />
                        {node.last_ledger}
                      </div>
                    </div>

                    {/* Action */}
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        handleTriggerSync(node.id)
                      }}
                      disabled={loadingSync === node.id}
                      className="w-full flex items-center justify-center gap-2 px-3 py-2 bg-slate-700/50 text-slate-300 hover:bg-cyan-500/20 hover:text-cyan-400 rounded transition-all text-sm font-medium disabled:opacity-60 disabled:cursor-not-allowed"
                      title={`Trigger synchronization for node ${node.id}`}
                    >
                      {loadingSync === node.id ? (
                        <>
                          <Loader className="h-3 w-3 animate-spin" />
                          Syncing...
                        </>
                      ) : (
                        <>
                          <Zap className="h-3 w-3" />
                          Trigger Sync
                        </>
                      )}
                    </button>
                  </div>
                )
              })}
            </div>

            {/* Node Detail Panel */}
            {selectedNode && (
              <div className="bg-slate-800/30 border border-slate-700/50 rounded-lg p-6 backdrop-blur">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
                    <Activity className="h-5 w-5 text-cyan-400" />
                    {selectedNode.tag} Details
                  </h2>
                  <button
                    onClick={() => setSelectedNode(null)}
                    className="text-slate-400 hover:text-slate-200"
                  >
                    ✕
                  </button>
                </div>

                {/* History Chart Simulation */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <div>
                    <h3 className="text-sm font-semibold text-slate-300 mb-4">Sync Health Trend (24h)</h3>
                    <div className="h-24 flex items-end gap-1">
                      {nodeHistory.map((entry, idx) => (
                        <div
                          key={idx}
                          className="flex-1 bg-gradient-to-t from-cyan-500 to-cyan-400 rounded-t opacity-70"
                          style={{ height: `${entry.sync_health * 100}%`, minHeight: '4px' }}
                        />
                      ))}
                    </div>
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-slate-300 mb-4">Trust Score Trend (24h)</h3>
                    <div className="h-24 flex items-end gap-1">
                      {nodeHistory.map((entry, idx) => (
                        <div
                          key={idx}
                          className="flex-1 bg-gradient-to-t from-blue-500 to-blue-400 rounded-t opacity-70"
                          style={{ height: `${entry.trust_score * 100}%`, minHeight: '4px' }}
                        />
                      ))}
                    </div>
                  </div>
                </div>

                {/* Statistics */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6 pt-6 border-t border-slate-700/50">
                  {[
                    {
                      label: 'Avg Health',
                      value: (
                        nodeHistory.reduce((sum, h) => sum + h.sync_health, 0) / nodeHistory.length * 100
                      ).toFixed(1),
                      unit: '%',
                    },
                    {
                      label: 'Avg Trust',
                      value: (nodeHistory.reduce((sum, h) => sum + h.trust_score, 0) / nodeHistory.length * 100).toFixed(1),
                      unit: '%',
                    },
                    { label: 'Syncs', value: nodeHistory.length, unit: '' },
                    { label: 'Uptime', value: '99.8', unit: '%' },
                  ].map((stat) => (
                    <div key={stat.label} className="text-center">
                      <p className="text-xs text-slate-500 mb-1">{stat.label}</p>
                      <p className="text-lg font-bold text-cyan-400">
                        {stat.value}
                        <span className="text-sm ml-1">{stat.unit}</span>
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Models View */}
        {viewMode === 'models' && (
          <div className="space-y-4">
            <h2 className="text-xl font-bold text-slate-100 mb-4 flex items-center gap-2">
              <GitBranch className="h-5 w-5 text-purple-400" />
              Federated Model Provenance
            </h2>

            <div className="grid grid-cols-1 gap-4">
              {models.map((model) => (
                <div key={model.id} className="bg-slate-800/30 border border-slate-700/50 rounded-lg p-4 backdrop-blur">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-purple-500/20 rounded-lg">
                        <GitBranch className="h-4 w-4 text-purple-400" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-slate-100">{model.id}</h3>
                        <p className="text-xs text-slate-500">v{model.version}</p>
                      </div>
                    </div>
                    <span
                      className={`px-3 py-1 rounded-full text-xs font-semibold ${
                        model.status === 'validated'
                          ? 'bg-green-500/20 text-green-400'
                          : model.status === 'aggregated'
                            ? 'bg-blue-500/20 text-blue-400'
                            : 'bg-yellow-500/20 text-yellow-400'
                      }`}
                    >
                      {model.status}
                    </span>
                  </div>

                  <div className="grid grid-cols-3 gap-4 text-xs text-slate-400">
                    <div>
                      <span className="text-slate-500">Created</span>
                      <p className="text-slate-300">{new Date(model.created_at).toLocaleString()}</p>
                    </div>
                    <div>
                      <span className="text-slate-500">Source Node</span>
                      <p className="text-slate-300">{model.node_id}</p>
                    </div>
                    <div>
                      <span className="text-slate-500">Status</span>
                      <div className="flex items-center gap-1 mt-1">
                        <CheckCircle2 className={`h-3 w-3 ${model.status === 'validated' ? 'text-green-400' : 'text-slate-400'}`} />
                        <span className="text-slate-300 capitalize">{model.status}</span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Analytics View */}
        {viewMode === 'analytics' && (
          <div className="space-y-6">
            <h2 className="text-xl font-bold text-slate-100 mb-4 flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-green-400" />
              Network Analytics
            </h2>

            {/* Privacy & Security */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-slate-800/30 border border-slate-700/50 rounded-lg p-6 backdrop-blur">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-semibold text-slate-100 flex items-center gap-2">
                    <Lock className="h-4 w-4 text-purple-400" />
                    Privacy Engine Status
                  </h3>
                  <Shield className="h-4 w-4 text-green-400" />
                </div>

                <div className="space-y-3">
                  {[
                    { label: 'Differential Privacy', value: 98 },
                    { label: 'Secure Aggregation', value: 100 },
                    { label: 'Encryption Coverage', value: 100 },
                    { label: 'Byzantine Resilience', value: 94 },
                  ].map((item) => (
                    <div key={item.label}>
                      <div className="flex justify-between items-center mb-1">
                        <span className="text-sm text-slate-400">{item.label}</span>
                        <span className="text-sm font-semibold text-cyan-400">{item.value}%</span>
                      </div>
                      <div className="w-full bg-slate-700/50 h-2 rounded-full">
                        <div
                          className="bg-gradient-to-r from-green-500 to-cyan-400 h-2 rounded-full"
                          style={{ width: `${item.value}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Sync Efficiency */}
              <div className="bg-slate-800/30 border border-slate-700/50 rounded-lg p-6 backdrop-blur">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-semibold text-slate-100 flex items-center gap-2">
                    <TrendingUp className="h-4 w-4 text-green-400" />
                    Sync Performance
                  </h3>
                  <Activity className="h-4 w-4 text-blue-400" />
                </div>

                <div className="space-y-3">
                  {[
                    { label: 'Sync Efficiency', value: 94 },
                    { label: 'Network Utilization', value: 78 },
                    { label: 'Bandwidth Optimization', value: 92 },
                    { label: 'Latency Reduction', value: 87 },
                  ].map((item) => (
                    <div key={item.label}>
                      <div className="flex justify-between items-center mb-1">
                        <span className="text-sm text-slate-400">{item.label}</span>
                        <span className="text-sm font-semibold text-green-400">{item.value}%</span>
                      </div>
                      <div className="w-full bg-slate-700/50 h-2 rounded-full">
                        <div
                          className="bg-gradient-to-r from-blue-500 to-cyan-400 h-2 rounded-full"
                          style={{ width: `${item.value}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Global Statistics */}
            <div className="bg-slate-800/30 border border-slate-700/50 rounded-lg p-6 backdrop-blur">
              <h3 className="font-semibold text-slate-100 mb-4 flex items-center gap-2">
                <Layers className="h-4 w-4 text-cyan-400" />
                Aggregation Timeline
              </h3>

              <div className="space-y-4">
                {[
                  { phase: 'Model Collection', progress: 100, status: 'completed' },
                  { phase: 'Parameter Aggregation', progress: 100, status: 'completed' },
                  { phase: 'Validation', progress: 85, status: 'in-progress' },
                  { phase: 'Distribution', progress: 0, status: 'pending' },
                ].map((item) => (
                  <div key={item.phase}>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm text-slate-400 flex items-center gap-2">
                        {item.status === 'completed' ? (
                          <CheckCircle2 className="h-4 w-4 text-green-400" />
                        ) : item.status === 'in-progress' ? (
                          <Activity className="h-4 w-4 text-blue-400 animate-pulse" />
                        ) : (
                          <AlertCircle className="h-4 w-4 text-slate-500" />
                        )}
                        {item.phase}
                      </span>
                      <span className="text-sm font-semibold text-slate-300">{item.progress}%</span>
                    </div>
                    <div className="w-full bg-slate-700/50 h-2 rounded-full">
                      <div
                        className="bg-gradient-to-r from-cyan-500 to-blue-400 h-2 rounded-full"
                        style={{ width: `${item.progress}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </AppLayout>
  )
}
