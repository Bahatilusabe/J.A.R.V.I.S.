import { useState } from 'react'
import { ChevronDown, Copy, Shield, AlertTriangle, Clock } from 'lucide-react'

export interface Vulnerability {
  cveId: string
  cvss: number // 0-10 scale
  severity: 'low' | 'medium' | 'high' | 'critical'
  patchAvailable: boolean
  exploitProbability: number // 0-1
}

export interface Incident {
  timestamp: string
  type: 'reconnaissance' | 'lateral_movement' | 'exploitation' | 'exfiltration'
  severity: 'low' | 'medium' | 'high' | 'critical'
  description: string
}

export interface NodeDetailPanelProps {
  hostname: string
  type: 'web' | 'app' | 'db' | 'firewall' | 'vpn'
  risk: number // 0-1
  confidence: number // 0-1
  criticality: 'critical' | 'high' | 'medium' | 'low'
  owner?: string
  lastScanned?: string
  vulnerabilities: Vulnerability[]
  relatedIncidents?: Incident[]
  onClose: () => void
  className?: string
}

/**
 * NodeDetailPanel Component
 *
 * Detailed information panel for selected graph nodes.
 * Shows asset metadata, vulnerabilities, incident history, and risk assessment.
 * Features tabbed interface and copy-to-clipboard functionality.
 */
export default function NodeDetailPanel({
  hostname,
  type,
  risk,
  confidence,
  criticality,
  owner = 'Unknown',
  lastScanned = new Date().toISOString(),
  vulnerabilities,
  relatedIncidents = [],
  onClose,
  className = '',
}: NodeDetailPanelProps) {
  const [activeTab, setActiveTab] = useState<'overview' | 'vulnerabilities' | 'incidents' | 'timeline'>('overview')
  const [copied, setCopied] = useState(false)

  // Handle copy to clipboard
  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  // Get risk color
  const getRiskColor = (riskValue: number): string => {
    if (riskValue > 0.75) return 'text-red-500'
    if (riskValue > 0.5) return 'text-orange-500'
    if (riskValue > 0.25) return 'text-yellow-500'
    return 'text-green-500'
  }

  // Get background color for severity
  const getSeverityColor = (sev: string): string => {
    switch (sev) {
      case 'critical':
        return 'bg-red-900/30 border-red-700'
      case 'high':
        return 'bg-orange-900/30 border-orange-700'
      case 'medium':
        return 'bg-yellow-900/30 border-yellow-700'
      default:
        return 'bg-green-900/30 border-green-700'
    }
  }

  // Format ISO date
  const formatDate = (isoString: string): string => {
    try {
      return new Date(isoString).toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      })
    } catch {
      return isoString
    }
  }

  // Get type icon
  const getTypeIcon = (assetType: string): string => {
    switch (assetType) {
      case 'web':
        return '🌐'
      case 'app':
        return '⚙️'
      case 'db':
        return '🗄️'
      case 'firewall':
        return '🛡️'
      case 'vpn':
        return '🔒'
      default:
        return '📦'
    }
  }

  return (
    <div
      className={`w-full h-full bg-slate-800 rounded-lg border border-cyan-400/30 overflow-hidden flex flex-col ${className}`}
    >
      {/* Header */}
      <div className="bg-gradient-to-r from-slate-900 to-slate-800 border-b border-cyan-400/20 p-4 flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-2xl">{getTypeIcon(type)}</span>
            <div>
              <h3 className="font-bold text-white text-lg">{hostname}</h3>
              <p className="text-xs text-gray-400 capitalize">
                {type} · Criticality: {criticality}
              </p>
            </div>
          </div>

          {/* Quick stats */}
          <div className="grid grid-cols-3 gap-3 mt-3">
            <div className="bg-slate-900 rounded px-2 py-1">
              <div className={`text-sm font-bold ${getRiskColor(risk)}`}>{Math.round(risk * 100)}%</div>
              <div className="text-xs text-gray-400">Risk Score</div>
            </div>
            <div className="bg-slate-900 rounded px-2 py-1">
              <div className="text-sm font-bold text-cyan-400">{Math.round(confidence * 100)}%</div>
              <div className="text-xs text-gray-400">Confidence</div>
            </div>
            <div className="bg-slate-900 rounded px-2 py-1">
              <div className="text-sm font-bold text-yellow-400">{vulnerabilities.length}</div>
              <div className="text-xs text-gray-400">Vulns</div>
            </div>
          </div>
        </div>

        {/* Close button */}
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-white hover:bg-slate-700 rounded p-2 transition-colors"
        >
          <ChevronDown size={20} className="rotate-90" />
        </button>
      </div>

      {/* Tab navigation */}
      <div className="border-b border-slate-700 bg-slate-900/50 flex">
        {(['overview', 'vulnerabilities', 'incidents', 'timeline'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`flex-1 px-4 py-2 text-sm font-medium transition-colors border-b-2 ${
              activeTab === tab
                ? 'text-cyan-400 border-cyan-400 bg-slate-800/50'
                : 'text-gray-400 border-transparent hover:text-gray-300'
            }`}
          >
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div className="space-y-4">
            {/* Info group */}
            <div className="bg-slate-900 rounded-lg p-3 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-400">Hostname</span>
                <div className="flex items-center gap-2">
                  <code className="text-xs font-mono text-cyan-400">{hostname}</code>
                  <button
                    onClick={() => handleCopy(hostname)}
                    title="Copy hostname"
                    className="p-1 hover:bg-slate-700 rounded transition-colors"
                  >
                    <Copy size={14} className={copied ? 'text-green-400' : 'text-gray-400'} />
                  </button>
                </div>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-400">Owner</span>
                <span className="text-sm text-gray-200">{owner}</span>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-400">Last Scanned</span>
                <span className="text-sm text-gray-200">{formatDate(lastScanned)}</span>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-400">Asset Type</span>
                <span className="text-sm text-gray-200 capitalize">{type}</span>
              </div>
            </div>

            {/* Risk assessment */}
            <div className="bg-slate-900 rounded-lg p-3">
              <div className="flex items-center gap-2 mb-2">
                <Shield size={16} className="text-cyan-400" />
                <span className="font-semibold text-white">Risk Assessment</span>
              </div>
              <div className="space-y-2">
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-400">Overall Risk</span>
                    <span className={`font-bold ${getRiskColor(risk)}`}>{Math.round(risk * 100)}%</span>
                  </div>
                  <div className="w-full bg-slate-800 rounded h-2">
                    <div
                      className={`h-2 rounded transition-all ${
                        risk > 0.75
                          ? 'bg-red-600'
                          : risk > 0.5
                            ? 'bg-orange-600'
                            : risk > 0.25
                              ? 'bg-yellow-600'
                              : 'bg-green-600'
                      }`}
                      style={{ width: `${Math.round(risk * 100)}%` }}
                    />
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-400">Prediction Confidence</span>
                    <span className="font-bold text-cyan-400">{Math.round(confidence * 100)}%</span>
                  </div>
                  <div className="w-full bg-slate-800 rounded h-2">
                    <div
                      className="h-2 rounded bg-cyan-600 transition-all"
                      style={{ width: `${Math.round(confidence * 100)}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Vulnerability summary */}
            <div className="bg-slate-900 rounded-lg p-3">
              <div className="flex items-center gap-2 mb-2">
                <AlertTriangle size={16} className="text-yellow-400" />
                <span className="font-semibold text-white">Vulnerabilities</span>
              </div>
              <div className="text-sm text-gray-300">
                Found <span className="font-bold text-orange-400">{vulnerabilities.length}</span> known vulnerabilities
              </div>
              {vulnerabilities.length > 0 && (
                <div className="mt-2 space-y-1 text-xs">
                  {vulnerabilities.slice(0, 3).map((v) => (
                    <div key={v.cveId} className="flex justify-between text-gray-400">
                      <span>{v.cveId}</span>
                      <span className="text-gray-500">CVSS {v.cvss.toFixed(1)}</span>
                    </div>
                  ))}
                  {vulnerabilities.length > 3 && (
                    <div className="text-gray-500 pt-1">+{vulnerabilities.length - 3} more</div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Vulnerabilities Tab */}
        {activeTab === 'vulnerabilities' && (
          <div className="space-y-2">
            {vulnerabilities.length === 0 ? (
              <div className="text-center py-8 text-gray-400">No known vulnerabilities</div>
            ) : (
              vulnerabilities.map((vuln) => (
                <div
                  key={vuln.cveId}
                  className={`rounded-lg p-3 border border-gray-700 ${getSeverityColor(vuln.severity)}`}
                >
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <code className="font-mono font-bold text-white">{vuln.cveId}</code>
                      <div className="text-xs text-gray-300 capitalize mt-1">{vuln.severity}</div>
                    </div>
                    <div className="text-right">
                      <div className="font-bold text-lg">{vuln.cvss.toFixed(1)}</div>
                      <div className="text-xs text-gray-400">CVSS</div>
                    </div>
                  </div>

                  <div className="flex items-center justify-between text-xs mt-2">
                    <span className="text-gray-400">
                      Exploit Probability: <span className="text-orange-400">{Math.round(vuln.exploitProbability * 100)}%</span>
                    </span>
                    <span className={vuln.patchAvailable ? 'text-green-400' : 'text-red-400'}>
                      {vuln.patchAvailable ? '✓ Patch Available' : '✗ No Patch'}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {/* Incidents Tab */}
        {activeTab === 'incidents' && (
          <div className="space-y-2">
            {relatedIncidents.length === 0 ? (
              <div className="text-center py-8 text-gray-400">No related incidents</div>
            ) : (
              relatedIncidents.map((incident, idx) => (
                <div
                  key={idx}
                  className={`rounded-lg p-3 border border-gray-700 ${getSeverityColor(incident.severity)}`}
                >
                  <div className="flex items-start justify-between mb-1">
                    <div className="font-semibold text-white capitalize">{incident.type.replace('_', ' ')}</div>
                    <span className="text-xs text-gray-400">{formatDate(incident.timestamp)}</span>
                  </div>
                  <p className="text-sm text-gray-300 mb-2">{incident.description}</p>
                  <div className="text-xs text-gray-400 capitalize">Severity: {incident.severity}</div>
                </div>
              ))
            )}
          </div>
        )}

        {/* Timeline Tab */}
        {activeTab === 'timeline' && (
          <div className="space-y-3">
            {relatedIncidents.length === 0 ? (
              <div className="text-center py-8 text-gray-400">No timeline events</div>
            ) : (
              relatedIncidents
                .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
                .map((incident, idx) => (
                  <div key={idx} className="flex gap-4">
                    <div className="flex flex-col items-center">
                      <div className="w-3 h-3 rounded-full bg-cyan-500 relative z-10" />
                      {idx < relatedIncidents.length - 1 && (
                        <div className="w-0.5 h-12 bg-gradient-to-b from-cyan-500 to-slate-700 mt-2" />
                      )}
                    </div>
                    <div className="pb-4">
                      <div className="flex items-center gap-2 mb-1">
                        <Clock size={14} className="text-gray-500" />
                        <span className="text-xs text-gray-400">{formatDate(incident.timestamp)}</span>
                      </div>
                      <div className="font-semibold text-white capitalize mb-1">
                        {incident.type.replace('_', ' ')}
                      </div>
                      <p className="text-sm text-gray-300">{incident.description}</p>
                    </div>
                  </div>
                ))
            )}
          </div>
        )}
      </div>
    </div>
  )
}
