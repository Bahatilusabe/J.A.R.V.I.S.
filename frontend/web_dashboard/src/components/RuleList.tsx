import React, { useState, useMemo } from 'react'
import { Search, Copy, Download, ToggleLeft, ToggleRight, AlertTriangle } from 'lucide-react'
import { DPIRule, SuspiciousSignature } from '../types/tds.types'

interface RuleListProps {
  rules: DPIRule[]
  signatures: SuspiciousSignature[]
  onSelectRule?: (rule: DPIRule) => void
  onToggleRule?: (ruleId: string, enabled: boolean) => void
  onBlockSignature?: (signature: SuspiciousSignature) => void
}

export const RuleList: React.FC<RuleListProps> = ({
  rules,
  signatures,
  onSelectRule,
  onToggleRule,
  onBlockSignature,
}) => {
  const [searchQuery, setSearchQuery] = useState('')
  const [filterSeverity, setFilterSeverity] = useState<string | 'all'>('all')
  const [filterCategory, setFilterCategory] = useState<string | 'all'>('all')
  const [viewMode, setViewMode] = useState<'rules' | 'signatures'>('rules')

  // Filter and search rules
  const filteredRules = useMemo(() => {
    return rules.filter((rule) => {
      const matchesSearch =
        rule.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        rule.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
        rule.signature.toLowerCase().includes(searchQuery.toLowerCase())

      const matchesSeverity = filterSeverity === 'all' || rule.severity === filterSeverity
      const matchesCategory = filterCategory === 'all' || rule.category === filterCategory

      return matchesSearch && matchesSeverity && matchesCategory
    })
  }, [rules, searchQuery, filterSeverity, filterCategory])

  // Filter and search signatures
  const filteredSignatures = useMemo(() => {
    return signatures.filter((sig) => {
      const matchesSearch =
        sig.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        sig.pattern.toLowerCase().includes(searchQuery.toLowerCase()) ||
        sig.category.toLowerCase().includes(searchQuery.toLowerCase())

      const matchesSeverity = filterSeverity === 'all' || sig.severity === filterSeverity
      const matchesCategory = filterCategory === 'all' || sig.category === filterCategory

      return matchesSearch && matchesSeverity && matchesCategory
    })
  }, [signatures, searchQuery, filterSeverity, filterCategory])

  const getSeverityColor = (
    severity: 'info' | 'low' | 'medium' | 'high' | 'critical'
  ): string => {
    switch (severity) {
      case 'critical':
        return 'bg-red-500/20 text-red-300 border-red-500/40'
      case 'high':
        return 'bg-orange-500/20 text-orange-300 border-orange-500/40'
      case 'medium':
        return 'bg-yellow-500/20 text-yellow-300 border-yellow-500/40'
      case 'low':
        return 'bg-blue-500/20 text-blue-300 border-blue-500/40'
      case 'info':
        return 'bg-slate-500/20 text-slate-300 border-slate-500/40'
    }
  }

  const getCategoryColor = (category: string): string => {
    const colors: Record<string, string> = {
      malware: 'bg-red-900/20 text-red-200',
      exploit: 'bg-orange-900/20 text-orange-200',
      reconnaissance: 'bg-blue-900/20 text-blue-200',
      command_control: 'bg-purple-900/20 text-purple-200',
      data_exfiltration: 'bg-pink-900/20 text-pink-200',
      anomaly: 'bg-yellow-900/20 text-yellow-200',
      policy_violation: 'bg-indigo-900/20 text-indigo-200',
    }
    return colors[category] || 'bg-slate-900/20 text-slate-200'
  }

  const handleCopyRule = (rule: DPIRule) => {
    navigator.clipboard.writeText(JSON.stringify(rule, null, 2))
  }

  const handleExportRules = () => {
    const dataStr = JSON.stringify(filteredRules, null, 2)
    const dataBlob = new Blob([dataStr], { type: 'application/json' })
    const url = URL.createObjectURL(dataBlob)
    const link = document.createElement('a')
    link.href = url
    link.download = `dpi-rules-${new Date().toISOString()}.json`
    link.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="w-full h-full bg-gradient-to-br from-slate-900 to-slate-800 rounded-lg border border-blue-500/20 flex flex-col">
      {/* Header */}
      <div className="flex-shrink-0 p-4 border-b border-slate-700/50">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold text-white">
            {viewMode === 'rules' ? 'DPI Rules' : 'Suspicious Signatures'}
          </h2>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setViewMode('rules')}
              className={`px-3 py-1.5 rounded text-sm font-medium transition ${
                viewMode === 'rules'
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-700/50 text-slate-300 hover:bg-slate-700'
              }`}
            >
              Rules ({rules.length})
            </button>
            <button
              onClick={() => setViewMode('signatures')}
              className={`px-3 py-1.5 rounded text-sm font-medium transition ${
                viewMode === 'signatures'
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-700/50 text-slate-300 hover:bg-slate-700'
              }`}
            >
              Signatures ({signatures.length})
            </button>
          </div>
        </div>

        {/* Search bar */}
        <div className="flex gap-2 mb-3">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-500" size={16} />
            <input
              type="text"
              placeholder="Search rules, patterns..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-3 py-2 bg-slate-800/50 border border-slate-600 rounded text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 focus:bg-slate-800"
            />
          </div>
          {viewMode === 'rules' && (
            <button
              onClick={handleExportRules}
              className="px-3 py-2 bg-slate-700/50 hover:bg-slate-700 text-slate-300 rounded text-sm flex items-center gap-2 transition"
            >
              <Download size={16} />
              Export
            </button>
          )}
        </div>

        {/* Filters */}
        <div className="flex gap-3">
          <select
            value={filterSeverity}
            onChange={(e) => setFilterSeverity(e.target.value)}
            className="px-3 py-1.5 bg-slate-800/50 border border-slate-600 rounded text-sm text-white focus:outline-none focus:border-blue-500"
          >
            <option value="all">All Severities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
            <option value="info">Info</option>
          </select>

          <select
            value={filterCategory}
            onChange={(e) => setFilterCategory(e.target.value)}
            className="px-3 py-1.5 bg-slate-800/50 border border-slate-600 rounded text-sm text-white focus:outline-none focus:border-blue-500"
          >
            <option value="all">All Categories</option>
            <option value="malware">Malware</option>
            <option value="exploit">Exploit</option>
            <option value="reconnaissance">Reconnaissance</option>
            <option value="command_control">C&C</option>
            <option value="data_exfiltration">Data Exfil</option>
            <option value="anomaly">Anomaly</option>
            <option value="policy_violation">Policy</option>
          </select>
        </div>
      </div>

      {/* Rules List */}
      {viewMode === 'rules' && (
        <div className="flex-1 overflow-y-auto">
          {filteredRules.length === 0 ? (
            <div className="p-8 text-center text-slate-400">
              <p>No rules match your filters</p>
            </div>
          ) : (
            <div className="divide-y divide-slate-700/50">
              {filteredRules.map((rule) => (
                <div
                  key={rule.ruleId}
                  onClick={() => onSelectRule?.(rule)}
                  className="p-4 hover:bg-slate-800/50 cursor-pointer transition group"
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1 min-w-0">
                      <h3 className="font-semibold text-white group-hover:text-blue-300 transition truncate">
                        {rule.name}
                      </h3>
                      <p className="text-xs text-slate-500 mt-1 truncate">{rule.signature}</p>
                    </div>
                    <div className="flex items-center gap-2 ml-4 flex-shrink-0">
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          onToggleRule?.(rule.ruleId, !rule.enabled)
                        }}
                        className="p-1.5 hover:bg-slate-700 rounded text-slate-400 hover:text-white transition"
                        title={rule.enabled ? 'Disable rule' : 'Enable rule'}
                      >
                        {rule.enabled ? (
                          <ToggleRight size={18} className="text-green-500" />
                        ) : (
                          <ToggleLeft size={18} className="text-slate-600" />
                        )}
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          handleCopyRule(rule)
                        }}
                        className="p-1.5 hover:bg-slate-700 rounded text-slate-400 hover:text-white transition"
                        title="Copy rule"
                      >
                        <Copy size={16} />
                      </button>
                    </div>
                  </div>

                  <p className="text-xs text-slate-400 mb-2">{rule.description}</p>

                  <div className="flex flex-wrap items-center gap-2">
                    <span className={`px-2 py-0.5 rounded text-xs border font-medium ${getSeverityColor(rule.severity)}`}>
                      {rule.severity.toUpperCase()}
                    </span>
                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${getCategoryColor(rule.category)}`}>
                      {rule.category.replace(/_/g, ' ')}
                    </span>
                    <span className="text-xs text-slate-500">
                      {rule.hitCount} hits
                      {rule.lastTriggered && (
                        <>
                          {' - Last: '}
                          {new Date(rule.lastTriggered).toLocaleTimeString()}
                        </>
                      )}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Signatures List */}
      {viewMode === 'signatures' && (
        <div className="flex-1 overflow-y-auto">
          {filteredSignatures.length === 0 ? (
            <div className="p-8 text-center text-slate-400">
              <p>No suspicious signatures detected</p>
            </div>
          ) : (
            <div className="divide-y divide-slate-700/50">
              {filteredSignatures.map((sig) => (
                <div
                  key={sig.signatureId}
                  className="p-4 hover:bg-slate-800/50 transition group border-l-2 border-orange-500/50"
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <AlertTriangle size={16} className="text-orange-500 flex-shrink-0" />
                        <h3 className="font-semibold text-white truncate">{sig.name}</h3>
                      </div>
                      <p className="text-xs text-slate-500 mt-1 truncate">{sig.pattern}</p>
                    </div>
                    <button
                      onClick={() => onBlockSignature?.(sig)}
                      className="px-3 py-1 ml-4 bg-red-600/20 hover:bg-red-600/40 text-red-300 rounded text-xs font-medium transition flex-shrink-0"
                    >
                      Block
                    </button>
                  </div>

                  <p className="text-xs text-slate-400 mb-2">{sig.description}</p>

                  <div className="flex flex-wrap items-center gap-2">
                    <span className={`px-2 py-0.5 rounded text-xs border font-medium ${getSeverityColor(sig.severity)}`}>
                      {sig.severity.toUpperCase()}
                    </span>
                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${getCategoryColor(sig.category)}`}>
                      {sig.category.replace(/_/g, ' ')}
                    </span>
                    <span className="text-xs text-slate-500">
                      {sig.hitCount} detections
                      {sig.lastTriggered && (
                        <>
                          {' - Last: '}
                          {new Date(sig.lastTriggered).toLocaleTimeString()}
                        </>
                      )}
                    </span>
                    {sig.cveId && sig.cveId.length > 0 && (
                      <span className="text-xs text-blue-400">CVE: {sig.cveId.join(', ')}</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
