/**
 * Stateful Firewall & Policy Manager Component
 *
 * Manages:
 * - Firewall rules (CRUD)
 * - ACL policies
 * - Traffic flows and decisions
 * - Policy versioning
 * - Staged rollouts
 * - Real-time metrics
 * - Connection tracking
 */

import React, { useState, useEffect } from 'react';
import { Plus, Edit2, Trash2, Play, Copy, TrendingUp, AlertCircle, Lock, Zap } from 'lucide-react';

interface FirewallRule {
  rule_id: string;
  name: string;
  priority: number;
  direction: string;
  src_ip_prefix?: string;
  dst_ip_prefix?: string;
  src_port_range?: [number, number];
  dst_port_range?: [number, number];
  protocol?: string;
  app_name?: string;
  dpi_category?: string;
  user_identity?: string;
  user_role?: string;
  action: string;
  qos_class?: string;
  rate_limit_kbps?: number;
  geo_block_countries: string[];
  geo_block_action: string;
  enabled: boolean;
  description: string;
  created_at: string;
  updated_at: string;
}

interface PolicyVersion {
  version_id: string;
  name: string;
  description: string;
  rules: FirewallRule[];
  created_at: string;
  created_by: string;
  status: string;
  deployment_percentage: number;
  deployment_target?: string;
  rule_count: number;
}

interface PolicyMetrics {
  packets_passed: number;
  packets_dropped: number;
  packets_rejected: number;
  connections_established: number;
  connections_terminated: number;
  bytes_passed: number;
  bytes_dropped: number;
  policy_violations: number;
  rate_limit_events: number;
  geo_block_events: number;
  nat_translations: number;
  active_connections: number;
  connection_capacity_percent: number;
}

const RULE_TEMPLATES = [
  {
    name: 'Block Malware Category',
    description: 'Block all traffic matching malware DPI category',
    template: {
      priority: 1000,
      direction: 'bidirectional',
      dpi_category: 'malware',
      action: 'deny',
      description: 'Automatic malware blocking based on DPI detection',
    }
  },
  {
    name: 'Rate Limit Background Traffic',
    description: 'Limit non-business traffic to 1 Mbps',
    template: {
      priority: 500,
      direction: 'outbound',
      qos_class: 'bulk',
      rate_limit_kbps: 1000,
      description: 'Rate limit bulk/background traffic',
    }
  },
  {
    name: 'Geo-Block High-Risk Countries',
    description: 'Block or inspect traffic from high-risk regions',
    template: {
      priority: 900,
      direction: 'inbound',
      geo_block_countries: ['KP', 'IR'],
      geo_block_action: 'block',
      description: 'Geo-block high-risk countries',
    }
  },
  {
    name: 'Prioritize VoIP',
    description: 'Prioritize VoIP traffic with critical QoS',
    template: {
      priority: 2000,
      direction: 'bidirectional',
      app_name: 'VoIP',
      qos_class: 'critical',
      description: 'Ensure low latency for VoIP',
    }
  },
];

const PolicyManager: React.FC = () => {
  const [rules, setRules] = useState<FirewallRule[]>([]);
  const [versions, setVersions] = useState<PolicyVersion[]>([]);
  const [metrics, setMetrics] = useState<PolicyMetrics | null>(null);
  const [activeTab, setActiveTab] = useState<'rules' | 'versions' | 'metrics' | 'templates'>('rules');
  const [selectedRule, setSelectedRule] = useState<FirewallRule | null>(null);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterDirection, setFilterDirection] = useState<string>('all');
  const [filterAction, setFilterAction] = useState<string>('all');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Auto-refresh metrics
  useEffect(() => {
    const refreshMetrics = async () => {
      try {
        const response = await fetch('/policy/firewall/metrics');
        if (response.ok) {
          const data = await response.json();
          setMetrics(data.metrics);
        }
      } catch (err) {
        console.error('Error fetching metrics:', err);
      }
    };

    refreshMetrics();
    const interval = setInterval(refreshMetrics, 5000);
    return () => clearInterval(interval);
  }, []);

  // Load rules on mount
  useEffect(() => {
    loadRules();
    loadVersions();
  }, []);

  const loadRules = async () => {
    try {
      setLoading(true);
      const response = await fetch('/policy/firewall/rules');
      if (response.ok) {
        const data = await response.json();
        setRules(data.rules || []);
        setError(null);
      }
    } catch (err) {
      setError('Failed to load rules');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadVersions = async () => {
    try {
      const response = await fetch('/policy/firewall/versions');
      if (response.ok) {
        const data = await response.json();
        setVersions(data.versions || []);
      }
    } catch (err) {
      console.error('Error loading versions:', err);
    }
  };

  const handleCreateRule = async (formData: Partial<FirewallRule>) => {
    try {
      const response = await fetch('/policy/firewall/rules', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        setIsFormOpen(false);
        setSelectedRule(null);
        await loadRules();
        setError(null);
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to create rule');
      }
    } catch (err) {
      setError('Failed to create rule');
      console.error(err);
    }
  };

  const handleDeleteRule = async (ruleId: string) => {
    if (!confirm('Delete this rule?')) return;

    try {
      const response = await fetch(`/policy/firewall/rules/${ruleId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        await loadRules();
        setError(null);
      } else {
        setError('Failed to delete rule');
      }
    } catch (err) {
      setError('Failed to delete rule');
      console.error(err);
    }
  };

  const handleCreateVersion = async () => {
    const name = prompt('Policy version name:');
    const description = prompt('Description:');

    if (!name || !description) return;

    try {
      const response = await fetch('/policy/firewall/versions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name,
          description,
          parent_version_id: versions[0]?.version_id,
        }),
      });

      if (response.ok) {
        await loadVersions();
        setError(null);
      } else {
        setError('Failed to create version');
      }
    } catch (err) {
      setError('Failed to create version');
      console.error(err);
    }
  };

  const handleStageVersion = async (versionId: string) => {
    const percentage = prompt('Deployment percentage (1-100):', '10');
    if (!percentage) return;

    try {
      const response = await fetch(`/policy/firewall/versions/${versionId}/stage`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          deployment_percentage: parseInt(percentage),
        }),
      });

      if (response.ok) {
        await loadVersions();
        setError(null);
      } else {
        setError('Failed to stage version');
      }
    } catch (err) {
      setError('Failed to stage version');
      console.error(err);
    }
  };

  const handleActivateVersion = async (versionId: string) => {
    if (!confirm('Activate this version? This will apply it to 100% of traffic.')) return;

    try {
      const response = await fetch(`/policy/firewall/versions/${versionId}/activate`, {
        method: 'POST',
      });

      if (response.ok) {
        await loadVersions();
        await loadRules();
        setError(null);
      } else {
        setError('Failed to activate version');
      }
    } catch (err) {
      setError('Failed to activate version');
      console.error(err);
    }
  };

  // Filter rules
  const filteredRules = rules.filter(rule => {
    const matchesSearch = rule.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         (rule.description?.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchesDirection = filterDirection === 'all' || rule.direction === filterDirection;
    const matchesAction = filterAction === 'all' || rule.action === filterAction;
    return matchesSearch && matchesDirection && matchesAction;
  });

  return (
    <div className="space-y-6 p-6 bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 rounded-lg">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold text-white flex items-center gap-2">
            <Lock className="w-8 h-8 text-blue-400" />
            Firewall & Policy Manager
          </h2>
          <p className="text-gray-400 mt-1">Stateful enforcement with versioning and staged rollouts</p>
        </div>
        {metrics && (
          <div className="text-right text-sm">
            <div className="text-gray-300">
              {metrics.active_connections.toLocaleString()} active connections
            </div>
            <div className="text-yellow-400 text-xs mt-1">
              {metrics.connection_capacity_percent.toFixed(1)}% capacity
            </div>
          </div>
        )}
      </div>

      {/* Error Alert */}
      {error && (
        <div className="bg-red-900/20 border border-red-700 rounded-lg p-4 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-red-300 font-semibold">Error</p>
            <p className="text-red-200 text-sm">{error}</p>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-2 border-b border-gray-700">
        {(['rules', 'versions', 'metrics', 'templates'] as const).map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 font-medium text-sm transition-colors ${
              activeTab === tab
                ? 'text-blue-400 border-b-2 border-blue-400'
                : 'text-gray-400 hover:text-gray-300'
            }`}
          >
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </button>
        ))}
      </div>

      {/* Rules Tab */}
      {activeTab === 'rules' && (
        <div className="space-y-4">
          <div className="flex gap-4 justify-between items-center">
            <input
              type="text"
              placeholder="Search rules..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="flex-1 px-3 py-2 bg-gray-700 text-white rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <select
              aria-label="Filter by direction"
              value={filterDirection}
              onChange={(e) => setFilterDirection(e.target.value)}
              className="px-3 py-2 bg-gray-700 text-white rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Directions</option>
              <option value="inbound">Inbound</option>
              <option value="outbound">Outbound</option>
              <option value="bidirectional">Bidirectional</option>
            </select>
            <select
              aria-label="Filter by action"
              value={filterAction}
              onChange={(e) => setFilterAction(e.target.value)}
              className="px-3 py-2 bg-gray-700 text-white rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Actions</option>
              <option value="allow">Allow</option>
              <option value="deny">Deny</option>
              <option value="log">Log</option>
              <option value="alert">Alert</option>
            </select>
            <button
              onClick={() => {
                setSelectedRule(null);
                setIsFormOpen(!isFormOpen);
              }}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm font-medium flex items-center gap-2 transition-colors"
            >
              <Plus className="w-4 h-4" />
              New Rule
            </button>
          </div>

          {/* Rule Form */}
          {isFormOpen && (
            <RuleForm
              rule={selectedRule}
              onSave={handleCreateRule}
              onCancel={() => {
                setIsFormOpen(false);
                setSelectedRule(null);
              }}
            />
          )}

          {/* Rules Table */}
          {loading ? (
            <div className="text-center py-8 text-gray-400">Loading rules...</div>
          ) : (
            <div className="overflow-x-auto border border-gray-700 rounded-lg">
              <table className="w-full text-sm">
                <thead className="bg-gray-800 border-b border-gray-700">
                  <tr>
                    <th className="px-4 py-3 text-left text-gray-300">Name</th>
                    <th className="px-4 py-3 text-left text-gray-300">Priority</th>
                    <th className="px-4 py-3 text-left text-gray-300">Direction</th>
                    <th className="px-4 py-3 text-left text-gray-300">Action</th>
                    <th className="px-4 py-3 text-left text-gray-300">Criteria</th>
                    <th className="px-4 py-3 text-left text-gray-300">Status</th>
                    <th className="px-4 py-3 text-left text-gray-300">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredRules.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="px-4 py-8 text-center text-gray-400">
                        No rules found
                      </td>
                    </tr>
                  ) : (
                    filteredRules.map(rule => (
                      <tr key={rule.rule_id} className="border-b border-gray-700 hover:bg-gray-750">
                        <td className="px-4 py-3 font-medium text-white">{rule.name}</td>
                        <td className="px-4 py-3 text-gray-400">{rule.priority}</td>
                        <td className="px-4 py-3 text-gray-400">
                          <span className="px-2 py-1 bg-gray-700 rounded text-xs">
                            {rule.direction}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          <span className={`px-2 py-1 rounded text-xs font-medium ${
                            rule.action === 'allow' ? 'bg-green-900 text-green-200' :
                            rule.action === 'deny' ? 'bg-red-900 text-red-200' :
                            'bg-yellow-900 text-yellow-200'
                          }`}>
                            {rule.action.toUpperCase()}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-xs text-gray-400">
                          {rule.app_name && `app: ${rule.app_name}`}
                          {rule.dpi_category && `category: ${rule.dpi_category}`}
                          {rule.protocol && `proto: ${rule.protocol}`}
                          {!rule.app_name && !rule.dpi_category && !rule.protocol && '-'}
                        </td>
                        <td className="px-4 py-3">
                          <span className={`px-2 py-1 rounded text-xs ${
                            rule.enabled ? 'bg-green-900 text-green-200' : 'bg-gray-700 text-gray-300'
                          }`}>
                            {rule.enabled ? 'Enabled' : 'Disabled'}
                          </span>
                        </td>
                        <td className="px-4 py-3 flex gap-2">
                          <button
                            onClick={() => {
                              setSelectedRule(rule);
                              setIsFormOpen(true);
                            }}
                            className="text-blue-400 hover:text-blue-300"
                            title="Edit"
                          >
                            <Edit2 className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => handleDeleteRule(rule.rule_id)}
                            className="text-red-400 hover:text-red-300"
                            title="Delete"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          )}

          <div className="text-sm text-gray-400">
            Showing {filteredRules.length} of {rules.length} rules
          </div>
        </div>
      )}

      {/* Versions Tab */}
      {activeTab === 'versions' && (
        <div className="space-y-4">
          <button
            onClick={handleCreateVersion}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm font-medium flex items-center gap-2 transition-colors"
          >
            <Plus className="w-4 h-4" />
            New Version
          </button>

          <div className="grid gap-4">
            {versions.map(version => (
              <div key={version.version_id} className="bg-gray-800 border border-gray-700 rounded-lg p-4">
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <h3 className="text-white font-semibold">{version.name}</h3>
                    <p className="text-gray-400 text-sm">{version.description}</p>
                  </div>
                  <span className={`px-3 py-1 rounded text-sm font-medium ${
                    version.status === 'active' ? 'bg-green-900 text-green-200' :
                    version.status === 'staged' ? 'bg-yellow-900 text-yellow-200' :
                    'bg-gray-700 text-gray-300'
                  }`}>
                    {version.status.toUpperCase()}
                  </span>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4 text-sm">
                  <div>
                    <p className="text-gray-400">Rules</p>
                    <p className="text-white font-semibold">{version.rule_count}</p>
                  </div>
                  <div>
                    <p className="text-gray-400">Deployment</p>
                    <p className="text-white font-semibold">{version.deployment_percentage}%</p>
                  </div>
                  <div>
                    <p className="text-gray-400">Created By</p>
                    <p className="text-white font-semibold">{version.created_by}</p>
                  </div>
                  <div>
                    <p className="text-gray-400">Created</p>
                    <p className="text-white font-semibold text-xs">
                      {new Date(version.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>

                <div className="flex gap-2">
                  {version.status === 'draft' && (
                    <>
                      <button
                        onClick={() => handleStageVersion(version.version_id)}
                        className="flex-1 px-3 py-2 bg-yellow-600 hover:bg-yellow-700 text-white rounded text-sm font-medium flex items-center justify-center gap-2 transition-colors"
                      >
                        <Zap className="w-4 h-4" />
                        Stage for Rollout
                      </button>
                      <button
                        onClick={() => handleActivateVersion(version.version_id)}
                        className="flex-1 px-3 py-2 bg-green-600 hover:bg-green-700 text-white rounded text-sm font-medium flex items-center justify-center gap-2 transition-colors"
                      >
                        <Play className="w-4 h-4" />
                        Activate Now
                      </button>
                    </>
                  )}
                  {version.status === 'staged' && (
                    <button
                      onClick={() => handleActivateVersion(version.version_id)}
                      className="flex-1 px-3 py-2 bg-green-600 hover:bg-green-700 text-white rounded text-sm font-medium flex items-center justify-center gap-2 transition-colors"
                    >
                      <Play className="w-4 h-4" />
                      Complete Rollout
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Metrics Tab */}
      {activeTab === 'metrics' && metrics && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <MetricCard
            title="Packets Passed"
            value={metrics.packets_passed.toLocaleString()}
            icon={<TrendingUp className="w-5 h-5 text-green-400" />}
            color="green"
          />
          <MetricCard
            title="Packets Dropped"
            value={metrics.packets_dropped.toLocaleString()}
            icon={<AlertCircle className="w-5 h-5 text-red-400" />}
            color="red"
          />
          <MetricCard
            title="Policy Violations"
            value={metrics.policy_violations.toLocaleString()}
            icon={<Lock className="w-5 h-5 text-orange-400" />}
            color="orange"
          />
          <MetricCard
            title="Active Connections"
            value={metrics.active_connections.toLocaleString()}
            icon={<Zap className="w-5 h-5 text-blue-400" />}
            color="blue"
          />
          <MetricCard
            title="Bytes Passed"
            value={`${(metrics.bytes_passed / 1e9).toFixed(2)} GB`}
            icon={<TrendingUp className="w-5 h-5 text-green-400" />}
            color="green"
          />
          <MetricCard
            title="Rate Limit Events"
            value={metrics.rate_limit_events.toLocaleString()}
            icon={<AlertCircle className="w-5 h-5 text-yellow-400" />}
            color="yellow"
          />
          <MetricCard
            title="Geo-Block Events"
            value={metrics.geo_block_events.toLocaleString()}
            icon={<Lock className="w-5 h-5 text-purple-400" />}
            color="purple"
          />
          <MetricCard
            title="NAT Translations"
            value={metrics.nat_translations.toLocaleString()}
            icon={<Zap className="w-5 h-5 text-cyan-400" />}
            color="cyan"
          />
          <MetricCard
            title="Capacity Usage"
            value={`${metrics.connection_capacity_percent.toFixed(1)}%`}
            icon={<TrendingUp className="w-5 h-5 text-yellow-400" />}
            color="yellow"
          />
        </div>
      )}

      {/* Templates Tab */}
      {activeTab === 'templates' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {RULE_TEMPLATES.map((template, idx) => (
            <div key={idx} className="bg-gray-800 border border-gray-700 rounded-lg p-4">
              <h3 className="text-white font-semibold mb-2">{template.name}</h3>
              <p className="text-gray-400 text-sm mb-4">{template.description}</p>
              <button
                onClick={() => {
                  setSelectedRule(null);
                  setIsFormOpen(true);
                }}
                className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm font-medium flex items-center justify-center gap-2 transition-colors"
              >
                <Copy className="w-4 h-4" />
                Use Template
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// Sub-component: Rule Form
interface RuleFormProps {
  rule: FirewallRule | null;
  onSave: (data: Partial<FirewallRule>) => void;
  onCancel: () => void;
}

const RuleForm: React.FC<RuleFormProps> = ({ rule, onSave, onCancel }) => {
  const [formData, setFormData] = useState(
    rule || {
      name: '',
      priority: 100,
      direction: 'bidirectional',
      action: 'allow',
      protocol: 'tcp',
      enabled: true,
      description: '',
      geo_block_countries: [],
      geo_block_action: 'allow',
    }
  );

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave(formData);
  };

  return (
    <div className="bg-gray-800 border border-gray-700 rounded-lg p-6 space-y-4">
      <h3 className="text-lg font-semibold text-white">
        {rule ? 'Edit Rule' : 'New Rule'}
      </h3>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <input
            type="text"
            placeholder="Rule name"
            value={formData.name}
            onChange={(e) => setFormData({...formData, name: e.target.value})}
            className="px-3 py-2 bg-gray-700 text-white rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          />
          <input
            type="number"
            placeholder="Priority"
            value={formData.priority}
            onChange={(e) => setFormData({...formData, priority: parseInt(e.target.value)})}
            className="px-3 py-2 bg-gray-700 text-white rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div className="grid grid-cols-3 gap-4">
          <select
            aria-label="Select traffic direction"
            value={formData.direction}
            onChange={(e) => setFormData({...formData, direction: e.target.value})}
            className="px-3 py-2 bg-gray-700 text-white rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="inbound">Inbound</option>
            <option value="outbound">Outbound</option>
            <option value="bidirectional">Bidirectional</option>
          </select>
          <select
            aria-label="Select rule action"
            value={formData.action}
            onChange={(e) => setFormData({...formData, action: e.target.value})}
            className="px-3 py-2 bg-gray-700 text-white rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="allow">Allow</option>
            <option value="deny">Deny</option>
            <option value="log">Log</option>
            <option value="alert">Alert</option>
          </select>
          <select
            aria-label="Select protocol"
            value={formData.protocol || ''}
            onChange={(e) => setFormData({...formData, protocol: e.target.value})}
            className="px-3 py-2 bg-gray-700 text-white rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Any Protocol</option>
            <option value="tcp">TCP</option>
            <option value="udp">UDP</option>
            <option value="icmp">ICMP</option>
          </select>
        </div>

        <textarea
          placeholder="Description"
          value={formData.description}
          onChange={(e) => setFormData({...formData, description: e.target.value})}
          className="w-full px-3 py-2 bg-gray-700 text-white rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          rows={2}
        />

        <div className="flex justify-end gap-3">
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded text-sm font-medium transition-colors"
          >
            Cancel
          </button>
          <button
            type="submit"
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm font-medium transition-colors"
          >
            Save Rule
          </button>
        </div>
      </form>
    </div>
  );
};

// Sub-component: Metric Card
interface MetricCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  color: string;
}

const MetricCard: React.FC<MetricCardProps> = ({ title, value, icon, color }) => {
  const colorClasses = {
    green: 'bg-green-900/20 border-green-700',
    red: 'bg-red-900/20 border-red-700',
    orange: 'bg-orange-900/20 border-orange-700',
    blue: 'bg-blue-900/20 border-blue-700',
    yellow: 'bg-yellow-900/20 border-yellow-700',
    purple: 'bg-purple-900/20 border-purple-700',
    cyan: 'bg-cyan-900/20 border-cyan-700',
  };

  return (
    <div className={`${colorClasses[color as keyof typeof colorClasses]} border rounded-lg p-4`}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-gray-400 text-sm">{title}</p>
          <p className="text-white text-2xl font-bold mt-1">{value}</p>
        </div>
        {icon}
      </div>
    </div>
  );
};

export default PolicyManager;
