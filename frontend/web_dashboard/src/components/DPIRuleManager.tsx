import { useState, useEffect } from 'react'
import axios from 'axios'

const DPI_API_BASE = 'http://localhost:8000/dpi'

interface DPIRule {
  rule_id: number
  name: string
  pattern: string
  type: string
  severity: string
  protocol?: string
  category: string
  description: string
  enabled: boolean
  created_at: number
  match_count?: number
}

interface RuleFormData {
  name: string
  pattern: string
  type: 'REGEX' | 'SNORT' | 'YARA' | 'CONTENT' | 'BEHAVIORAL'
  severity: 'INFO' | 'WARNING' | 'CRITICAL' | 'MALWARE' | 'ANOMALY'
  protocol?: string
  category: string
  description: string
  action?: 'ALLOW' | 'BLOCK' | 'ALERT_ONLY' | 'REDIRECT_IPS' | 'QUARANTINE'
}

const RULE_TEMPLATES: Record<string, RuleFormData> = {
  'SQL Injection': {
    name: 'SQL Injection Detection',
    pattern: `(union.*select|select.*from|insert.*into|delete.*from|drop.*table|update.*set)`,
    type: 'REGEX',
    severity: 'CRITICAL',
    category: 'injection',
    description: 'Detects common SQL injection patterns in HTTP requests'
  },
  'XSS Detection': {
    name: 'Cross-Site Scripting Detection',
    pattern: `<script[^>]*>|javascript:|onerror=|onload=`,
    type: 'REGEX',
    severity: 'CRITICAL',
    category: 'xss',
    description: 'Detects XSS attack vectors in requests'
  },
  'Command Injection': {
    name: 'Command Injection Detection',
    pattern: `(;|\\||&&)[^a-zA-Z0-9]*(cat|bash|sh|cmd|powershell)`,
    type: 'REGEX',
    severity: 'CRITICAL',
    category: 'injection',
    description: 'Detects shell command injection attempts'
  },
  'Data Exfiltration': {
    name: 'Data Exfiltration Detection',
    pattern: `(POST|PUT).*(password|token|secret|api_key|credit_card)`,
    type: 'REGEX',
    severity: 'MALWARE',
    category: 'exfiltration',
    description: 'Detects suspicious data transmission to external hosts'
  }
}

const DPIRuleManager = () => {
  const [rules, setRules] = useState<DPIRule[]>([])
  const [loading, setLoading] = useState(false)
  const [showForm, setShowForm] = useState(false)
  const [selectedRule, setSelectedRule] = useState<DPIRule | null>(null)
  const [filterType, setFilterType] = useState('all')
  const [searchTerm, setSearchTerm] = useState('')
  const [formData, setFormData] = useState<RuleFormData>({
    name: '',
    pattern: '',
    type: 'REGEX',
    severity: 'WARNING',
    category: 'general',
    description: '',
    action: 'ALERT_ONLY'
  })

  // Fetch rules on mount
  useEffect(() => {
    fetchRules()
    const interval = setInterval(fetchRules, 5000)
    return () => clearInterval(interval)
  }, [])

  const fetchRules = async () => {
    try {
      setLoading(true)
      // Mock data since endpoint may not exist yet
      const mockRules: DPIRule[] = [
        {
          rule_id: 1,
          name: 'HTTP GET Anomaly',
          pattern: 'GET.*\\.\\.(\\.\\/)+',
          type: 'REGEX',
          severity: 'WARNING',
          protocol: 'HTTP',
          category: 'recon',
          description: 'Detects path traversal attempts in HTTP GET requests',
          enabled: true,
          created_at: Date.now() - 86400000,
          match_count: 42
        },
        {
          rule_id: 2,
          name: 'DNS Tunneling',
          pattern: '[a-z0-9]{32,}\\.',
          type: 'REGEX',
          severity: 'CRITICAL',
          protocol: 'DNS',
          category: 'exfiltration',
          description: 'Detects data exfiltration via DNS tunneling',
          enabled: true,
          created_at: Date.now() - 172800000,
          match_count: 8
        },
        {
          rule_id: 3,
          name: 'SMB Lateral Movement',
          pattern: 'SMB.*IPC\\$',
          type: 'SNORT',
          severity: 'MALWARE',
          protocol: 'SMB',
          category: 'lateral_movement',
          description: 'Detects SMB IPC$ access for lateral movement',
          enabled: true,
          created_at: Date.now() - 259200000,
          match_count: 3
        }
      ]
      setRules(mockRules)
    } catch (error) {
      console.error('Failed to fetch rules:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleAddRule = async () => {
    if (!formData.name || !formData.pattern) {
      alert('Name and pattern are required')
      return
    }

    try {
      await axios.post(`${DPI_API_BASE}/rules/add`, formData)
      alert('Rule added successfully!')
      setFormData({
        name: '',
        pattern: '',
        type: 'REGEX',
        severity: 'WARNING',
        category: 'general',
        description: '',
        action: 'ALERT_ONLY'
      })
      setShowForm(false)
      fetchRules()
    } catch (error) {
      console.error('Failed to add rule:', error)
      alert('Failed to add rule')
    }
  }

  const handleDeleteRule = async (ruleId: number) => {
    if (!window.confirm('Are you sure you want to delete this rule?')) return

    try {
      await axios.delete(`${DPI_API_BASE}/rules/${ruleId}`)
      alert('Rule deleted successfully')
      fetchRules()
    } catch (error) {
      console.error('Failed to delete rule:', error)
      alert('Failed to delete rule')
    }
  }

  const handleApplyTemplate = (template: RuleFormData) => {
    setFormData(template)
    setShowForm(true)
  }

  const filteredRules = rules.filter(rule => {
    const matchesFilter = filterType === 'all' || rule.type === filterType
    const matchesSearch = rule.name.toLowerCase().includes(searchTerm.toLowerCase())
    return matchesFilter && matchesSearch
  })

  const getSeverityColor = (severity: string): string => {
    const colors: Record<string, string> = {
      INFO: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
      WARNING: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30',
      CRITICAL: 'bg-red-500/20 text-red-300 border-red-500/30',
      MALWARE: 'bg-rose-500/20 text-rose-300 border-rose-500/30',
      ANOMALY: 'bg-amber-500/20 text-amber-300 border-amber-500/30'
    }
    return colors[severity] || colors.INFO
  }

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-white">📋 DPI Rule Management</h2>
          <p className="text-slate-400 text-sm mt-1">Create and manage detection rules ({filteredRules.length} total)</p>
        </div>
        <button
          onClick={() => setShowForm(true)}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition"
        >
          + New Rule
        </button>
      </div>

      {/* Search & Filter */}
      <div className="flex gap-4">
        <input
          type="text"
          placeholder="Search rules..."
          value={searchTerm}
          onChange={e => setSearchTerm(e.target.value)}
          className="flex-1 px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
        />
        <select
          value={filterType}
          onChange={e => setFilterType(e.target.value)}
          className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-blue-500"
        >
          <option value="all">All Types</option>
          <option value="REGEX">REGEX</option>
          <option value="SNORT">SNORT</option>
          <option value="YARA">YARA</option>
          <option value="CONTENT">CONTENT</option>
          <option value="BEHAVIORAL">BEHAVIORAL</option>
        </select>
      </div>

      {/* Rule Templates */}
      <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-slate-300 mb-3">📚 Quick Templates</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
          {Object.entries(RULE_TEMPLATES).map(([name, template]) => (
            <button
              key={name}
              onClick={() => handleApplyTemplate(template)}
              className="px-3 py-2 bg-slate-700/50 hover:bg-slate-700 border border-slate-600 rounded text-xs text-slate-300 hover:text-white transition"
            >
              {name}
            </button>
          ))}
        </div>
      </div>

      {/* Rules Table */}
      <div className="bg-slate-900 border border-slate-700 rounded-lg overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-slate-400">Loading rules...</div>
        ) : filteredRules.length === 0 ? (
          <div className="p-8 text-center text-slate-400">No rules found</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-slate-800 border-b border-slate-700">
                <tr>
                  <th className="px-4 py-3 text-left font-semibold text-slate-300">Name</th>
                  <th className="px-4 py-3 text-left font-semibold text-slate-300">Type</th>
                  <th className="px-4 py-3 text-left font-semibold text-slate-300">Severity</th>
                  <th className="px-4 py-3 text-left font-semibold text-slate-300">Protocol</th>
                  <th className="px-4 py-3 text-left font-semibold text-slate-300">Matches</th>
                  <th className="px-4 py-3 text-right font-semibold text-slate-300">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700">
                {filteredRules.map(rule => (
                  <tr
                    key={rule.rule_id}
                    className="hover:bg-slate-800/50 transition"
                    onClick={() => setSelectedRule(rule)}
                  >
                    <td className="px-4 py-3 text-white font-medium">{rule.name}</td>
                    <td className="px-4 py-3">
                      <span className="px-2 py-1 bg-slate-700/50 rounded text-xs text-slate-300">
                        {rule.type}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 rounded text-xs border ${getSeverityColor(rule.severity)}`}>
                        {rule.severity}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-slate-400">{rule.protocol || '—'}</td>
                    <td className="px-4 py-3 text-slate-400">{rule.match_count || 0}</td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={e => {
                          e.stopPropagation()
                          handleDeleteRule(rule.rule_id)
                        }}
                        className="px-2 py-1 text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded text-xs transition"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Rule Detail Panel */}
      {selectedRule && (
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
          <div className="flex justify-between items-start mb-4">
            <div>
              <h3 className="text-lg font-bold text-white">{selectedRule.name}</h3>
              <p className="text-slate-400 text-sm">{selectedRule.description}</p>
            </div>
            <button
              onClick={() => setSelectedRule(null)}
              className="text-slate-400 hover:text-white"
            >
              ✕
            </button>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-slate-400">Type</label>
              <p className="text-white font-medium">{selectedRule.type}</p>
            </div>
            <div>
              <label className="text-xs text-slate-400">Severity</label>
              <p className="text-white font-medium">{selectedRule.severity}</p>
            </div>
            <div>
              <label className="text-xs text-slate-400">Category</label>
              <p className="text-white font-medium">{selectedRule.category}</p>
            </div>
            <div>
              <label className="text-xs text-slate-400">Matches</label>
              <p className="text-white font-medium">{selectedRule.match_count || 0}</p>
            </div>
            <div className="col-span-2">
              <label className="text-xs text-slate-400">Pattern</label>
              <p className="text-slate-300 font-mono text-sm break-all bg-slate-900/50 p-2 rounded border border-slate-700">
                {selectedRule.pattern}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Add Rule Form Modal */}
      {showForm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-slate-900 border border-slate-700 rounded-lg p-6 w-96 max-h-96 overflow-y-auto">
            <h3 className="text-lg font-bold text-white mb-4">Add New Rule</h3>

            <div className="space-y-3">
              <div>
                <label className="text-sm text-slate-300">Name *</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={e => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded text-white text-sm focus:outline-none focus:border-blue-500"
                  placeholder="Rule name"
                />
              </div>

              <div>
                <label className="text-sm text-slate-300">Pattern *</label>
                <textarea
                  value={formData.pattern}
                  onChange={e => setFormData({ ...formData, pattern: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded text-white text-sm focus:outline-none focus:border-blue-500 font-mono"
                  placeholder="Regex pattern or signature"
                  rows={3}
                />
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-sm text-slate-300">Type</label>
                  <select
                    value={formData.type}
                    onChange={e => setFormData({ ...formData, type: e.target.value as any })}
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded text-white text-sm"
                  >
                    <option>REGEX</option>
                    <option>SNORT</option>
                    <option>YARA</option>
                    <option>CONTENT</option>
                    <option>BEHAVIORAL</option>
                  </select>
                </div>
                <div>
                  <label className="text-sm text-slate-300">Severity</label>
                  <select
                    value={formData.severity}
                    onChange={e => setFormData({ ...formData, severity: e.target.value as any })}
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded text-white text-sm"
                  >
                    <option>INFO</option>
                    <option>WARNING</option>
                    <option>CRITICAL</option>
                    <option>MALWARE</option>
                    <option>ANOMALY</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="text-sm text-slate-300">Category</label>
                <input
                  type="text"
                  value={formData.category}
                  onChange={e => setFormData({ ...formData, category: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded text-white text-sm"
                  placeholder="e.g. injection, xss, malware"
                />
              </div>

              <div>
                <label className="text-sm text-slate-300">Description</label>
                <textarea
                  value={formData.description}
                  onChange={e => setFormData({ ...formData, description: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded text-white text-sm focus:outline-none focus:border-blue-500"
                  placeholder="Rule description"
                  rows={2}
                />
              </div>
            </div>

            <div className="flex gap-2 mt-4">
              <button
                onClick={handleAddRule}
                className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded font-medium transition"
              >
                Add Rule
              </button>
              <button
                onClick={() => setShowForm(false)}
                className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded font-medium transition"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default DPIRuleManager
