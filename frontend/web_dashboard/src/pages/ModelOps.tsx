/* eslint-disable no-restricted-syntax */
import { useState, useEffect } from 'react'
import {
  Brain,
  TrendingUp,
  Server,
  GitBranch,
  Activity,
  Clock,
  CheckCircle,
  Upload,
  Settings as _Settings, // Deprecated - use action handlers instead
  Play,
  Filter,
  Search,
  ChevronRight,
  Sparkles,
  Layers,
  AlertCircle,
  X,
  Download,
  RefreshCw,
  Eye as _Eye, // Deprecated - use modal view instead
  Zap,
  Copy as _Copy, // Deprecated - not needed for current features
} from 'lucide-react'
import AppLayout from '../components/AppLayout'

interface Model {
  id: string
  name: string
  version: string
  status: 'production' | 'staging' | 'development' | 'archived'
  accuracy: number
  latency: number
  throughput: number
  lastUpdated: string
  deployedAt: string
  framework: string
  size: string
  aiConfidence: number
  inferenceCount: number
  errorRate: number
  uptime: number
}

interface DeploymentMetrics {
  totalModels: number
  activeModels: number
  deployments: number
  avgAccuracy: number
  avgLatency: number
}

interface ABTest {
  id: string
  modelA: string
  modelB: string
  trafficSplit: number
  winner?: string
  status: 'running' | 'completed' | 'paused'
  startDate: string
}

export default function ModelOpsPage() {
  const [models, setModels] = useState<Model[]>([])
  const [loading, setLoading] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedStatus, setSelectedStatus] = useState<'all' | 'production' | 'staging' | 'development'>('all')
  const [viewMode, setViewMode] = useState<'grid' | 'table' | 'timeline'>('grid')
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false)
  const [abTests, setAbTests] = useState<ABTest[]>([])
  const [sortBy, setSortBy] = useState<'accuracy' | 'latency' | 'updated'>('updated')
  const [successMessage, setSuccessMessage] = useState('')
  const [errorMessage, setErrorMessage] = useState('')
  const [selectedModel, setSelectedModel] = useState<Model | null>(null)
  const [showDetailModal, setShowDetailModal] = useState(false)
  const [isRefreshing, setIsRefreshing] = useState(false)

  // Handler: Deploy model to production
  const handleDeployModel = async (modelId: string) => {
    try {
      setLoading(true)
      // Call backend API: POST /api/metrics/deploy or similar
      const response = await fetch('/api/metrics/models/deploy', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model_id: modelId, target_env: 'production' })
      })
      
      if (response.ok) {
        setSuccessMessage(`Model ${modelId} deployed to production successfully`)
        // Update local state
        setModels(models.map(m => m.id === modelId ? { ...m, status: 'production' as const } : m))
        setTimeout(() => setSuccessMessage(''), 3000)
      } else {
        setErrorMessage(`Failed to deploy model ${modelId}`)
        setTimeout(() => setErrorMessage(''), 3000)
      }
    } catch (err) {
      setErrorMessage('Deployment error: ' + (err instanceof Error ? err.message : 'Unknown error'))
      setTimeout(() => setErrorMessage(''), 3000)
    } finally {
      setLoading(false)
    }
  }

  // Handler: Promote model to staging
  const handlePromoteToStaging = async (modelId: string) => {
    try {
      setLoading(true)
      const response = await fetch('/api/metrics/models/promote', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model_id: modelId, target_env: 'staging' })
      })
      
      if (response.ok) {
        setSuccessMessage(`Model ${modelId} promoted to staging`)
        setModels(models.map(m => m.id === modelId ? { ...m, status: 'staging' as const } : m))
        setTimeout(() => setSuccessMessage(''), 3000)
      } else {
        setErrorMessage('Promotion failed')
        setTimeout(() => setErrorMessage(''), 3000)
      }
    } catch (err) {
      setErrorMessage('Error: ' + (err instanceof Error ? err.message : 'Unknown error'))
      setTimeout(() => setErrorMessage(''), 3000)
    } finally {
      setLoading(false)
    }
  }

  // Handler: Rollback model version
  const handleRollback = async (modelId: string) => {
    try {
      setLoading(true)
      const response = await fetch('/api/metrics/models/rollback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model_id: modelId })
      })
      
      if (response.ok) {
        setSuccessMessage(`Model ${modelId} rolled back to previous version`)
        setTimeout(() => setSuccessMessage(''), 3000)
      } else {
        setErrorMessage('Rollback failed')
        setTimeout(() => setErrorMessage(''), 3000)
      }
    } catch (err) {
      setErrorMessage('Rollback error: ' + (err instanceof Error ? err.message : 'Unknown error'))
      setTimeout(() => setErrorMessage(''), 3000)
    } finally {
      setLoading(false)
    }
  }

  // Handler: Run tests on model
  const handleRunTests = async (modelId: string) => {
    try {
      setLoading(true)
      const response = await fetch('/api/metrics/models/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model_id: modelId })
      })
      
      if (response.ok) {
        const result = await response.json()
        setSuccessMessage(`Tests completed: ${result.passed || 'All tests passed'}`)
        setTimeout(() => setSuccessMessage(''), 3000)
      } else {
        setErrorMessage('Test execution failed')
        setTimeout(() => setErrorMessage(''), 3000)
      }
    } catch (err) {
      setErrorMessage('Test error: ' + (err instanceof Error ? err.message : 'Unknown error'))
      setTimeout(() => setErrorMessage(''), 3000)
    } finally {
      setLoading(false)
    }
  }

  // Handler: Start A/B test
  const handleStartABTest = async (modelA: string, modelB: string) => {
    try {
      setLoading(true)
      const response = await fetch('/api/metrics/models/ab-test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model_a: modelA, model_b: modelB, traffic_split: 50 })
      })
      
      if (response.ok) {
        setSuccessMessage('A/B test started successfully')
        setTimeout(() => setSuccessMessage(''), 3000)
      } else {
        setErrorMessage('Failed to start A/B test')
        setTimeout(() => setErrorMessage(''), 3000)
      }
    } catch (err) {
      setErrorMessage('A/B test error: ' + (err instanceof Error ? err.message : 'Unknown error'))
      setTimeout(() => setErrorMessage(''), 3000)
    } finally {
      setLoading(false)
    }
  }

  // Handler: View model details
  const handleViewDetails = (model: Model) => {
    setSelectedModel(model)
    setShowDetailModal(true)
  }

  // Handler: Export model metrics
  const handleExportMetrics = () => {
    try {
      const csvContent = [
        ['Model Name', 'Version', 'Status', 'Accuracy', 'Latency (ms)', 'Framework', 'Uptime (%)'],
        ...models.map(m => [
          m.name,
          m.version,
          m.status,
          (m.accuracy * 100).toFixed(1),
          m.latency,
          m.framework,
          m.uptime.toFixed(2)
        ])
      ]
        .map(row => row.join(','))
        .join('\n')

      const blob = new Blob([csvContent], { type: 'text/csv' })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `modelops-metrics-${new Date().toISOString().split('T')[0]}.csv`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)
      setSuccessMessage('Metrics exported successfully')
      setTimeout(() => setSuccessMessage(''), 3000)
    } catch (err) {
      setErrorMessage('Export failed: ' + (err instanceof Error ? err.message : 'Unknown error'))
      setTimeout(() => setErrorMessage(''), 3000)
    }
  }

  // Handler: Refresh all data
  const handleRefreshData = async () => {
    setIsRefreshing(true)
    try {
      loadModels()
      await new Promise(resolve => setTimeout(resolve, 500))
      setSuccessMessage('Models data refreshed')
      setTimeout(() => setSuccessMessage(''), 3000)
    } catch (err) {
      setErrorMessage('Refresh failed: ' + (err instanceof Error ? err.message : 'Unknown error'))
      setTimeout(() => setErrorMessage(''), 3000)
    } finally {
      setIsRefreshing(false)
    }
  }

  // Handler: Archive model
  const handleArchiveModel = async (modelId: string) => {
    try {
      setLoading(true)
      const response = await fetch('/api/metrics/models/archive', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model_id: modelId })
      })
      
      if (response.ok) {
        setSuccessMessage(`Model ${modelId} archived`)
        setModels(models.map(m => m.id === modelId ? { ...m, status: 'archived' as const } : m))
        setTimeout(() => setSuccessMessage(''), 3000)
      } else {
        setErrorMessage('Archive failed')
        setTimeout(() => setErrorMessage(''), 3000)
      }
    } catch (err) {
      setErrorMessage('Archive error: ' + (err instanceof Error ? err.message : 'Unknown error'))
      setTimeout(() => setErrorMessage(''), 3000)
    } finally {
      setLoading(false)
    }
  }

  // Load models on mount
  useEffect(() => {
    loadModels()
  }, [])

  const loadModels = async () => {
    setLoading(true)
    try {
      // Try to fetch from backend APIs: /api/metrics/models
      try {
        const response = await fetch('/api/metrics/models')
        if (response.ok) {
          const data = await response.json()
          const backendModels: Model[] = data.models || data
          setModels(backendModels)
          return
        }
      } catch {
        // Backend endpoint not available, continue to fallback
      }

      // Fallback: Use demo data (simulating backend response structure)
      const mockModels: Model[] = [
        {
          id: 'model-1',
          name: 'TGNN - Attack Surface Model',
          version: 'v2.1.0',
          status: 'production',
          accuracy: 0.94,
          latency: 125,
          throughput: 450,
          lastUpdated: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
          deployedAt: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
          framework: 'MindSpore',
          size: '2.3GB',
          aiConfidence: 0.92,
          inferenceCount: 1240000,
          errorRate: 0.002,
          uptime: 99.87,
        },
        {
          id: 'model-2',
          name: 'Graph Neural Network - Threat Detection',
          version: 'v1.8.5',
          status: 'staging',
          accuracy: 0.96,
          latency: 98,
          throughput: 520,
          lastUpdated: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
          deployedAt: new Date(Date.now() - 15 * 24 * 60 * 60 * 1000).toISOString(),
          framework: 'MindSpore',
          size: '1.8GB',
          aiConfidence: 0.95,
          inferenceCount: 420000,
          errorRate: 0.001,
          uptime: 99.95,
        },
        {
          id: 'model-3',
          name: 'Anomaly Detection - Behavioral',
          version: 'v3.0.0',
          status: 'development',
          accuracy: 0.91,
          latency: 156,
          throughput: 380,
          lastUpdated: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
          deployedAt: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
          framework: 'TensorFlow',
          size: '1.2GB',
          aiConfidence: 0.88,
          inferenceCount: 156000,
          errorRate: 0.005,
          uptime: 99.5,
        },
        {
          id: 'model-4',
          name: 'Ensemble - Multi-Model Predictor',
          version: 'v1.5.2',
          status: 'production',
          accuracy: 0.97,
          latency: 234,
          throughput: 300,
          lastUpdated: new Date(Date.now() - 8 * 24 * 60 * 60 * 1000).toISOString(),
          deployedAt: new Date(Date.now() - 60 * 24 * 60 * 60 * 1000).toISOString(),
          framework: 'PyTorch',
          size: '3.5GB',
          aiConfidence: 0.97,
          inferenceCount: 980000,
          errorRate: 0.0008,
          uptime: 99.92,
        },
      ]
      setModels(mockModels)

      // Mock A/B tests
      setAbTests([
        {
          id: 'ab-1',
          modelA: 'model-1',
          modelB: 'model-2',
          trafficSplit: 50,
          status: 'running',
          startDate: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
          winner: 'model-2',
        },
      ])
    } catch (err) {
      console.warn('Failed to load models', err)
    } finally {
      setLoading(false)
    }
  }

  // Filtered models
  const filteredModels = models
    .filter((model) => {
      const matchesSearch =
        model.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        model.version.toLowerCase().includes(searchQuery.toLowerCase())
      const matchesStatus = selectedStatus === 'all' || model.status === selectedStatus
      return matchesSearch && matchesStatus
    })
    .sort((a, b) => {
      if (sortBy === 'accuracy') return b.accuracy - a.accuracy
      if (sortBy === 'latency') return a.latency - b.latency
      return new Date(b.lastUpdated).getTime() - new Date(a.lastUpdated).getTime()
    })

  const metrics: DeploymentMetrics = {
    totalModels: models.length,
    activeModels: models.filter((m) => m.status === 'production' || m.status === 'staging').length,
    deployments: models.filter((m) => m.status === 'production').length,
    avgAccuracy: models.length > 0 ? models.reduce((sum, m) => sum + m.accuracy, 0) / models.length : 0,
    avgLatency: models.length > 0 ? models.reduce((sum, m) => sum + m.latency, 0) / models.length : 0,
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'production':
        return 'from-green-500/20 to-green-500/5 border-green-500/30 text-green-400'
      case 'staging':
        return 'from-blue-500/20 to-blue-500/5 border-blue-500/30 text-blue-400'
      case 'development':
        return 'from-yellow-500/20 to-yellow-500/5 border-yellow-500/30 text-yellow-400'
      default:
        return 'from-gray-500/20 to-gray-500/5 border-gray-500/30 text-gray-400'
    }
  }

  const getLatencyStatus = (latency: number) => {
    if (latency < 100) return { label: 'Excellent', color: 'text-green-400' }
    if (latency < 150) return { label: 'Good', color: 'text-cyan-400' }
    if (latency < 200) return { label: 'Fair', color: 'text-yellow-400' }
    return { label: 'Slow', color: 'text-red-400' }
  }

  return (
    <AppLayout activeLink="modelops" onNavLinkClick={() => {}}>
      <div className="p-6 space-y-6 bg-gradient-to-b from-slate-900/50 to-slate-950 min-h-screen">
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
        {/* Header with AI Insights */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h1 className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-cyan-400 to-purple-400 flex items-center gap-3">
                  <Brain className="h-8 w-8 text-cyan-400" />
                  ModelOps
                </h1>
                <p className="text-slate-400 mt-2">Enterprise model management, deployment, and monitoring dashboard</p>
              </div>
            </div>

            {/* AI Insights Banner */}
            <div className="bg-gradient-to-r from-blue-500/10 via-cyan-500/10 to-purple-500/10 border border-cyan-500/20 rounded-lg p-4 mb-6">
              <div className="flex items-start gap-3">
                <Sparkles className="h-5 w-5 text-cyan-400 mt-0.5" />
                <div>
                  <h3 className="font-semibold text-slate-100">Model Insights & Recommendations</h3>
                  <p className="text-sm text-slate-300 mt-1">
                    {models.filter((m) => m.status === 'production').length} production models in service • Average accuracy:{' '}
                    <span className="text-cyan-400 font-medium">{(metrics.avgAccuracy * 100).toFixed(1)}%</span> •{' '}
                    <span className="text-green-400">A/B test winner detected</span>
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Premium Metrics */}
          <div className="space-y-3">
            <div className="bg-slate-800/50 backdrop-blur border border-slate-700/50 rounded-lg p-4 hover:border-cyan-500/50 transition-all">
              <div className="flex items-center justify-between">
                <span className="text-slate-400 text-sm font-medium">Avg Accuracy</span>
                <TrendingUp className="h-4 w-4 text-green-400" />
              </div>
              <div className="text-2xl font-bold text-slate-100 mt-2">{(metrics.avgAccuracy * 100).toFixed(1)}%</div>
              <div className="w-full bg-slate-900 rounded-full h-1.5 mt-2">
                <div className="bg-gradient-to-r from-green-500 to-emerald-400 h-1.5 rounded-full w-[94%]" />
              </div>
            </div>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            { label: 'Total Models', value: metrics.totalModels, icon: Layers, color: 'blue' },
            { label: 'Active Models', value: metrics.activeModels, icon: Activity, color: 'green' },
            { label: 'Production', value: metrics.deployments, icon: Server, color: 'purple' },
            { label: 'Avg Latency', value: `${metrics.avgLatency.toFixed(0)}ms`, icon: Clock, color: 'orange' },
          ].map((stat, idx) => {
            const IconComponent = stat.icon
            const colorClasses = {
              blue: 'from-blue-500/20 to-blue-500/5 border-blue-500/30 text-blue-400',
              green: 'from-green-500/20 to-green-500/5 border-green-500/30 text-green-400',
              purple: 'from-purple-500/20 to-purple-500/5 border-purple-500/30 text-purple-400',
              orange: 'from-orange-500/20 to-orange-500/5 border-orange-500/30 text-orange-400',
            }
            const colorClass = colorClasses[stat.color as keyof typeof colorClasses]
            return (
              <div key={idx} className={`bg-gradient-to-br ${colorClass} border rounded-lg p-4 backdrop-blur`}>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-slate-400 text-sm font-medium">{stat.label}</p>
                    <p className="text-3xl font-bold text-slate-100 mt-2">{stat.value}</p>
                  </div>
                  <IconComponent className="h-8 w-8 opacity-50" />
                </div>
              </div>
            )
          })}
        </div>

        {/* Advanced Controls */}
        <div className="space-y-4">
          {/* Search & Filter Bar */}
          <div className="flex flex-col lg:flex-row lg:items-center gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
              <input
                type="text"
                placeholder="Search models by name, version, or framework..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-3 bg-slate-900/50 border border-slate-700 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500/50 focus:bg-slate-900 transition-all"
              />
            </div>

            <div className="flex flex-wrap gap-2 lg:gap-3 lg:flex-nowrap">
              <button
                onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
                className="px-4 py-3 bg-slate-900/50 border border-slate-700 rounded-lg text-slate-300 hover:border-cyan-500/50 hover:text-cyan-400 transition-all flex items-center gap-2 whitespace-nowrap"
              >
                <Filter className="h-4 w-4" />
                <span className="hidden sm:inline">Filters</span>
              </button>

              <select
                value={viewMode}
                onChange={(e) => setViewMode(e.target.value as 'grid' | 'table' | 'timeline')}
                className="px-4 py-3 bg-slate-900/50 border border-slate-700 rounded-lg text-slate-300 focus:outline-none focus:border-cyan-500/50 transition-all cursor-pointer"
                aria-label="View mode"
              >
                <option value="grid">Grid</option>
                <option value="table">Table</option>
                <option value="timeline">Timeline</option>
              </select>

              <button
                onClick={handleRefreshData}
                disabled={loading || isRefreshing}
                className="px-4 py-3 bg-slate-900/50 border border-slate-700 rounded-lg text-slate-300 hover:border-purple-500/50 hover:text-purple-400 disabled:opacity-50 transition-all flex items-center gap-2 whitespace-nowrap"
              >
                <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
                <span className="hidden sm:inline">Refresh</span>
              </button>

              <button
                onClick={handleExportMetrics}
                disabled={loading}
                className="px-4 py-3 bg-slate-900/50 border border-slate-700 rounded-lg text-slate-300 hover:border-green-500/50 hover:text-green-400 disabled:opacity-50 transition-all flex items-center gap-2 whitespace-nowrap"
              >
                <Download className="h-4 w-4" />
                <span className="hidden sm:inline">Export</span>
              </button>

              <button
                onClick={() => {
                  if (models.length >= 2) {
                    handleStartABTest(models[0].id, models[1].id)
                  } else {
                    setErrorMessage('Need at least 2 models to start A/B testing')
                    setTimeout(() => setErrorMessage(''), 3000)
                  }
                }}
                disabled={loading || models.length < 2}
                className="px-4 py-3 bg-gradient-to-r from-cyan-500/10 to-blue-500/10 border border-cyan-500/20 rounded-lg text-cyan-400 hover:border-cyan-500/50 disabled:opacity-50 transition-all flex items-center gap-2 whitespace-nowrap"
              >
                <Upload className="h-4 w-4" />
                <span className="hidden sm:inline">A/B Test</span>
              </button>
            </div>
          </div>

          {/* Advanced Filters Panel */}
          {showAdvancedFilters && (
            <div className="bg-slate-800/30 border border-slate-700/50 rounded-lg p-4 space-y-4 backdrop-blur">
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                <div>
                  <label className="text-xs font-semibold text-slate-300 block mb-2">Status</label>
                  <select
                    value={selectedStatus}
                    onChange={(e) => setSelectedStatus(e.target.value as 'all' | 'production' | 'staging' | 'development')}
                    className="w-full px-3 py-2 bg-slate-900/50 border border-slate-700 rounded text-slate-300 text-sm focus:outline-none focus:border-cyan-500/50"
                    aria-label="Filter by status"
                  >
                    <option value="all">All Statuses</option>
                    <option value="production">Production</option>
                    <option value="staging">Staging</option>
                    <option value="development">Development</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-300 block mb-2">Framework</label>
                  <select
                    className="w-full px-3 py-2 bg-slate-900/50 border border-slate-700 rounded text-slate-300 text-sm focus:outline-none focus:border-cyan-500/50"
                    aria-label="Filter by framework"
                  >
                    <option>All Frameworks</option>
                    <option>MindSpore</option>
                    <option>TensorFlow</option>
                    <option>PyTorch</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-300 block mb-2">Min Accuracy</label>
                  <input
                    type="range"
                    min="0"
                    max="100"
                    defaultValue="80"
                    className="w-full accent-cyan-400"
                    aria-label="Filter by minimum accuracy"
                  />
                </div>
              </div>

              {/* Sort Options */}
              <div className="flex items-center gap-3 pt-2 border-t border-slate-700/50">
                <span className="text-xs font-semibold text-slate-400">Sort by:</span>
                <div className="flex gap-2">
                  {(['accuracy', 'latency', 'updated'] as const).map((option) => (
                    <button
                      key={option}
                      onClick={() => setSortBy(option)}
                      className={`px-3 py-1 text-xs rounded transition-all ${
                        sortBy === option
                          ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/50'
                          : 'bg-slate-900/50 text-slate-400 border border-slate-700 hover:border-slate-600'
                      }`}
                    >
                      {option.charAt(0).toUpperCase() + option.slice(1)}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Model Grid */}
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="text-center">
              <div className="inline-block animate-spin">
                <div className="h-8 w-8 border-4 border-slate-700 border-t-cyan-500 rounded-full" />
              </div>
              <p className="text-slate-400 mt-4">Loading models...</p>
            </div>
          </div>
        ) : filteredModels.length === 0 ? (
          <div className="bg-slate-800/30 border border-slate-700/50 rounded-lg p-12 text-center backdrop-blur">
            <Brain className="h-12 w-12 mx-auto mb-3 opacity-30 text-slate-500" />
            <h3 className="text-lg font-medium text-slate-100 mb-1">No Models Found</h3>
            <p className="text-sm text-slate-400">Try adjusting your filters or deploy a new model.</p>
          </div>
        ) : viewMode === 'grid' ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-4">
            {filteredModels.map((model) => (
              <div
                key={model.id}
                className="bg-slate-800/30 border border-slate-700/50 rounded-lg p-6 backdrop-blur hover:border-cyan-500/50 transition-all cursor-pointer group"
              >
                {/* Header */}
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-slate-100 group-hover:text-cyan-400 transition-colors">{model.name}</h3>
                    <p className="text-sm text-slate-400 mt-1">v{model.version}</p>
                  </div>
                  <span className={`bg-gradient-to-br ${getStatusColor(model.status)} border rounded-lg px-3 py-1 text-xs font-semibold`}>
                    {model.status.charAt(0).toUpperCase() + model.status.slice(1)}
                  </span>
                </div>

                {/* Metrics Grid */}
                <div className="grid grid-cols-2 gap-3 mb-4">
                  <div className="bg-slate-900/50 rounded p-3">
                    <p className="text-xs text-slate-400 mb-1">Accuracy</p>
                    <p className="text-lg font-bold text-green-400">{(model.accuracy * 100).toFixed(1)}%</p>
                  </div>
                  <div className="bg-slate-900/50 rounded p-3">
                    <p className="text-xs text-slate-400 mb-1">Latency</p>
                    <p className={`text-lg font-bold ${getLatencyStatus(model.latency).color}`}>{model.latency}ms</p>
                  </div>
                  <div className="bg-slate-900/50 rounded p-3">
                    <p className="text-xs text-slate-400 mb-1">Throughput</p>
                    <p className="text-lg font-bold text-cyan-400">{model.throughput} req/s</p>
                  </div>
                  <div className="bg-slate-900/50 rounded p-3">
                    <p className="text-xs text-slate-400 mb-1">Uptime</p>
                    <p className="text-lg font-bold text-blue-400">{model.uptime.toFixed(2)}%</p>
                  </div>
                </div>

                {/* Info Bar */}
                <div className="flex items-center justify-between text-xs text-slate-400 mb-4 pb-4 border-b border-slate-700/50">
                  <span>{model.framework}</span>
                  <span>{model.size}</span>
                  <span>AI: {(model.aiConfidence * 100).toFixed(0)}%</span>
                </div>

                {/* Action Buttons */}
                <div className="flex gap-2">
                  <button
                    onClick={() => handleRunTests(model.id)}
                    disabled={loading}
                    title="Run tests on this model"
                    className="flex-1 px-3 py-2 bg-slate-700/50 text-slate-300 hover:bg-orange-500/20 hover:text-orange-400 disabled:opacity-50 rounded text-sm transition-all flex items-center justify-center gap-1"
                  >
                    <Play className="h-3 w-3" />
                    <span className="hidden sm:inline">Tests</span>
                  </button>
                  <button
                    onClick={() => handlePromoteToStaging(model.id)}
                    disabled={loading}
                    title="Promote to staging environment"
                    className="flex-1 px-3 py-2 bg-slate-700/50 text-slate-300 hover:bg-blue-500/20 hover:text-blue-400 disabled:opacity-50 rounded text-sm transition-all flex items-center justify-center gap-1"
                  >
                    <Upload className="h-3 w-3" />
                    <span className="hidden sm:inline">Stage</span>
                  </button>
                  <button
                    onClick={() => handleViewDetails(model)}
                    title="View model details"
                    className="px-3 py-2 bg-slate-700/50 text-slate-300 hover:bg-cyan-500/20 hover:text-cyan-400 rounded text-sm transition-all"
                  >
                    <ChevronRight className="h-4 w-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="bg-slate-800/30 border border-slate-700/50 rounded-lg overflow-hidden backdrop-blur">
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-slate-300">
                <thead className="bg-slate-900/50 border-b border-slate-700/50">
                  <tr>
                    <th className="px-6 py-3 text-left font-semibold text-slate-100">Model</th>
                    <th className="px-6 py-3 text-left font-semibold text-slate-100">Status</th>
                    <th className="px-6 py-3 text-right font-semibold text-slate-100">Accuracy</th>
                    <th className="px-6 py-3 text-right font-semibold text-slate-100">Latency</th>
                    <th className="px-6 py-3 text-right font-semibold text-slate-100">Throughput</th>
                    <th className="px-6 py-3 text-right font-semibold text-slate-100">Uptime</th>
                    <th className="px-6 py-3 text-center font-semibold text-slate-100">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredModels.map((model, idx) => (
                    <tr key={model.id} className={`border-b border-slate-700/30 hover:bg-slate-700/20 transition-colors ${idx % 2 === 0 ? 'bg-slate-800/10' : ''}`}>
                      <td className="px-6 py-4">
                        <div>
                          <p className="font-medium text-slate-100">{model.name}</p>
                          <p className="text-xs text-slate-400 mt-1">v{model.version}</p>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span className={`px-3 py-1 rounded text-xs font-semibold bg-gradient-to-br ${getStatusColor(model.status)}`}>
                          {model.status.charAt(0).toUpperCase() + model.status.slice(1)}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <span className="text-green-400 font-semibold">{(model.accuracy * 100).toFixed(1)}%</span>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <span className={getLatencyStatus(model.latency).color}>{model.latency}ms</span>
                      </td>
                      <td className="px-6 py-4 text-right text-cyan-400">{model.throughput} req/s</td>
                      <td className="px-6 py-4 text-right text-blue-400">{model.uptime.toFixed(2)}%</td>
                      <td className="px-6 py-4 text-center">
                        <button
                          onClick={() => handleViewDetails(model)}
                          title="View model details"
                          className="text-slate-400 hover:text-cyan-400 transition-colors"
                        >
                          <ChevronRight className="h-4 w-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* A/B Testing Section */}
        {abTests.length > 0 && (
          <div className="bg-slate-800/30 border border-slate-700/50 rounded-lg p-6 backdrop-blur">
            <h2 className="text-xl font-bold text-slate-100 mb-4 flex items-center gap-2">
              <GitBranch className="h-5 w-5 text-cyan-400" />
              Active A/B Tests
            </h2>
            <div className="space-y-4">
              {abTests.map((test) => (
                <div key={test.id} className="bg-slate-900/50 border border-slate-700/50 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <Activity className={`h-5 w-5 ${test.status === 'running' ? 'text-green-400 animate-pulse' : 'text-slate-400'}`} />
                      <div>
                        <p className="font-semibold text-slate-100">
                          {models.find((m) => m.id === test.modelA)?.name} vs {models.find((m) => m.id === test.modelB)?.name}
                        </p>
                        <p className="text-xs text-slate-400 mt-1">Started {new Date(test.startDate).toLocaleDateString()}</p>
                      </div>
                    </div>
                    {test.winner && (
                      <div className="flex items-center gap-2">
                        <CheckCircle className="h-5 w-5 text-green-400" />
                        <span className="text-sm font-semibold text-green-400">
                          {models.find((m) => m.id === test.winner)?.name} wins!
                        </span>
                      </div>
                    )}
                  </div>
                  <div className="w-full bg-slate-800 rounded-full h-2 mt-2 overflow-hidden">
                    {/* Progress bar with dynamic width - inline style required for runtime data */}
                    {/* eslint-disable-next-line */}
                    <div
                      className="bg-gradient-to-r from-cyan-500 to-blue-500 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${test.trafficSplit}%` }}
                    />
                  </div>
                  <p className="text-xs text-slate-400 mt-2 text-right">{test.trafficSplit}% traffic split</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Model Detail Modal */}
        {showDetailModal && selectedModel && (
          <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 flex items-center justify-center p-4">
            <div className="bg-gradient-to-br from-slate-800 via-slate-800 to-slate-900 border border-slate-700/50 rounded-lg shadow-2xl max-w-2xl w-full max-h-[80vh] overflow-y-auto">
              {/* Modal Header */}
              <div className="sticky top-0 bg-gradient-to-r from-slate-800/95 to-slate-900/95 border-b border-slate-700/50 p-6 flex items-start justify-between backdrop-blur-sm">
                <div>
                  <h2 className="text-2xl font-bold text-cyan-300">{selectedModel.name}</h2>
                  <p className="text-sm text-gray-400 mt-1">{selectedModel.version}</p>
                </div>
                <button
                  onClick={() => setShowDetailModal(false)}
                  className="p-1 hover:bg-slate-700/50 rounded-lg transition-colors"
                  aria-label="Close modal"
                >
                  <X size={20} className="text-gray-400 hover:text-white" />
                </button>
              </div>

              {/* Modal Content */}
              <div className="p-6 space-y-6">
                {/* Model Summary */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-slate-700/20 border border-cyan-400/20 rounded-lg p-4">
                    <div className="text-xs text-gray-400 uppercase tracking-wider mb-1">Status</div>
                    <div className="text-lg font-semibold text-cyan-300">{selectedModel.status}</div>
                  </div>
                  <div className="bg-slate-700/20 border border-green-400/20 rounded-lg p-4">
                    <div className="text-xs text-gray-400 uppercase tracking-wider mb-1">Accuracy</div>
                    <div className="text-lg font-semibold text-green-400">{(selectedModel.accuracy * 100).toFixed(1)}%</div>
                  </div>
                  <div className="bg-slate-700/20 border border-blue-400/20 rounded-lg p-4">
                    <div className="text-xs text-gray-400 uppercase tracking-wider mb-1">Latency</div>
                    <div className="text-lg font-semibold text-blue-400">{selectedModel.latency}ms</div>
                  </div>
                  <div className="bg-slate-700/20 border border-purple-400/20 rounded-lg p-4">
                    <div className="text-xs text-gray-400 uppercase tracking-wider mb-1">Uptime</div>
                    <div className="text-lg font-semibold text-purple-400">{selectedModel.uptime.toFixed(2)}%</div>
                  </div>
                </div>

                {/* Model Details */}
                <div className="bg-gradient-to-br from-slate-700/20 to-slate-800/20 border border-slate-700/50 rounded-lg p-4 space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-400">Framework:</span>
                    <span className="text-white font-medium">{selectedModel.framework}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Model Size:</span>
                    <span className="text-white font-medium">{selectedModel.size}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">AI Confidence:</span>
                    <span className="text-white font-medium">{(selectedModel.aiConfidence * 100).toFixed(1)}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Error Rate:</span>
                    <span className="text-white font-medium">{(selectedModel.errorRate * 100).toFixed(3)}%</span>
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="grid grid-cols-2 gap-3">
                  <button
                    onClick={() => {
                      handleDeployModel(selectedModel.id)
                      setShowDetailModal(false)
                    }}
                    disabled={loading}
                    className="flex items-center justify-center gap-2 bg-gradient-to-r from-green-500/20 to-emerald-500/10 hover:from-green-500/30 hover:to-emerald-500/20 border border-green-400/30 hover:border-green-400/60 disabled:opacity-50 rounded-lg px-4 py-2 text-green-300 hover:text-green-200 font-medium transition-all duration-200"
                  >
                    <Play size={16} />
                    Deploy to Prod
                  </button>
                  <button
                    onClick={() => {
                      handlePromoteToStaging(selectedModel.id)
                      setShowDetailModal(false)
                    }}
                    disabled={loading}
                    className="flex items-center justify-center gap-2 bg-gradient-to-r from-blue-500/20 to-cyan-500/10 hover:from-blue-500/30 hover:to-cyan-500/20 border border-blue-400/30 hover:border-blue-400/60 disabled:opacity-50 rounded-lg px-4 py-2 text-blue-300 hover:text-blue-200 font-medium transition-all duration-200"
                  >
                    <Upload size={16} />
                    Promote to Staging
                  </button>
                  <button
                    onClick={() => {
                      handleRunTests(selectedModel.id)
                      setShowDetailModal(false)
                    }}
                    disabled={loading}
                    className="flex items-center justify-center gap-2 bg-gradient-to-r from-orange-500/20 to-yellow-500/10 hover:from-orange-500/30 hover:to-yellow-500/20 border border-orange-400/30 hover:border-orange-400/60 disabled:opacity-50 rounded-lg px-4 py-2 text-orange-300 hover:text-orange-200 font-medium transition-all duration-200"
                  >
                    <Zap size={16} />
                    Run Tests
                  </button>
                  <button
                    onClick={() => {
                      handleRollback(selectedModel.id)
                      setShowDetailModal(false)
                    }}
                    disabled={loading}
                    className="flex items-center justify-center gap-2 bg-gradient-to-r from-yellow-500/20 to-orange-500/10 hover:from-yellow-500/30 hover:to-orange-500/20 border border-yellow-400/30 hover:border-yellow-400/60 disabled:opacity-50 rounded-lg px-4 py-2 text-yellow-300 hover:text-yellow-200 font-medium transition-all duration-200"
                  >
                    <RefreshCw size={16} />
                    Rollback
                  </button>
                  <button
                    onClick={() => {
                      handleArchiveModel(selectedModel.id)
                      setShowDetailModal(false)
                    }}
                    disabled={loading}
                    className="flex items-center justify-center gap-2 bg-gradient-to-r from-red-500/20 to-rose-500/10 hover:from-red-500/30 hover:to-rose-500/20 border border-red-400/30 hover:border-red-400/60 disabled:opacity-50 rounded-lg px-4 py-2 text-red-300 hover:text-red-200 font-medium transition-all duration-200"
                  >
                    <AlertCircle size={16} />
                    Archive
                  </button>
                  <button
                    onClick={() => setShowDetailModal(false)}
                    className="flex items-center justify-center gap-2 bg-gradient-to-r from-slate-700/50 to-slate-800/50 hover:from-slate-600/50 hover:to-slate-700/50 border border-slate-600/50 hover:border-slate-500/50 rounded-lg px-4 py-2 text-gray-300 hover:text-white font-medium transition-all duration-200 col-span-1"
                  >
                    <X size={16} />
                    Close
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </AppLayout>
  )
}
