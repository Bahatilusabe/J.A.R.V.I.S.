/**
 * Advanced Forensics Dashboard
 * Premium UI with all forensics elements visible and interactive
 */

import { useState } from 'react'

// Placeholder UI Components
const PageHeader = () => (
  <div className="relative overflow-hidden bg-gradient-to-r from-slate-900 via-cyan-900/20 to-slate-900 border-b border-slate-700">
    <div className="absolute inset-0 opacity-30">
      <div className="absolute top-0 left-1/4 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl"></div>
      <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl"></div>
    </div>
    <div className="relative p-8">
      <h1 className="text-4xl font-bold bg-gradient-to-r from-cyan-400 to-emerald-400 bg-clip-text text-transparent">
        🔬 Advanced Forensics Dashboard
      </h1>
      <p className="text-slate-400 mt-2">Real-time incident analysis with blockchain verification</p>
    </div>
  </div>
)

const StatsGrid = () => (
  <div className="grid grid-cols-5 gap-4 p-6 bg-slate-900/50">
    <StatCard label="Reports" value="24" icon="📋" color="cyan" />
    <StatCard label="Blockchain" value="156" icon="⛓️" color="emerald" />
    <StatCard label="Evidence" value="892" icon="🔍" color="orange" />
    <StatCard label="Verified" value="78%" icon="✓" color="emerald" />
    <StatCard label="Retention" value="90d" icon="📅" color="purple" />
  </div>
)

const StatCard = ({ label, value, icon, color }: { label: string; value: string; icon: string; color: string }) => {
  const colorClass: Record<string, string> = {
    cyan: 'from-cyan-500/20 to-cyan-500/5 border-cyan-500/30',
    emerald: 'from-emerald-500/20 to-emerald-500/5 border-emerald-500/30',
    orange: 'from-orange-500/20 to-orange-500/5 border-orange-500/30',
    purple: 'from-purple-500/20 to-purple-500/5 border-purple-500/30',
  }

  return (
    <div className={`bg-gradient-to-br ${colorClass[color] || 'from-slate-700/50 to-slate-800/50 border-slate-600'} border rounded-lg p-4`}>
      <div className="text-2xl mb-2">{icon}</div>
      <p className="text-slate-400 text-xs font-medium uppercase">{label}</p>
      <p className="text-2xl font-bold text-slate-100 mt-1">{value}</p>
    </div>
  )
}

const _ProgressBar = ({ percentage }: { percentage: number }) => (
  <div className="w-full bg-slate-600 rounded-full h-2 mt-2">
    <div
      className="h-2 rounded-full transition-all"
      style={{
        width: `${percentage}%`,
        backgroundColor: percentage > 80 ? '#10b981' : percentage > 50 ? '#f59e0b' : '#06b6d4'
      }}
    />
  </div>
)

void _ProgressBar // intentionally unused placeholder component

const ReportsList = () => (
  <div className="space-y-3 p-6">
    <div className="flex items-center justify-between mb-4">
      <h3 className="text-lg font-semibold text-slate-100">📋 Recent Forensics Reports</h3>
      <input
        type="text"
        placeholder="Search reports..."
        className="px-3 py-2 bg-slate-800 border border-slate-700 rounded text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500/50 w-48"
      />
    </div>
    {[1, 2, 3, 4, 5].map((i) => (
      <div key={i} className="bg-slate-800 border border-slate-700 rounded-lg p-4 hover:border-cyan-500/50 transition-colors cursor-pointer">
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <h4 className="font-semibold text-slate-100">Incident INC-{String(i).padStart(3, '0')}</h4>
            <p className="text-xs text-slate-400 mt-1">Detected: {new Date(Date.now() - i * 86400000).toLocaleDateString()}</p>
          </div>
          <div className="flex items-center gap-2">
            <span className={`px-2 py-1 text-xs font-semibold rounded border ${i % 3 === 0 ? 'bg-red-500/20 text-red-400 border-red-500/30' :
                i % 2 === 0 ? 'bg-orange-500/20 text-orange-400 border-orange-500/30' :
                  'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
              }`}>
              {i % 3 === 0 ? 'CRITICAL' : i % 2 === 0 ? 'HIGH' : 'MEDIUM'}
            </span>
          </div>
        </div>
      </div>
    ))}
  </div>
)

const ThreatSimulation = () => (
  <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 m-6">
    <h3 className="text-lg font-semibold text-slate-100 mb-4">⚡ Threat Simulation Metrics</h3>
    <div className="grid grid-cols-3 gap-4">
      <div className="bg-slate-700/50 rounded p-4">
        <p className="text-slate-400 text-sm">Attack Surface</p>
        <p className="text-emerald-400 font-bold text-2xl mt-2">3.2K</p>
        <div className="w-full bg-slate-600 rounded-full h-2 mt-2">
          <div className="bg-emerald-500 h-2 rounded-full" style={{ width: '45%' }}></div>
        </div>
      </div>
      <div className="bg-slate-700/50 rounded p-4">
        <p className="text-slate-400 text-sm">Vulnerabilities Found</p>
        <p className="text-orange-400 font-bold text-2xl mt-2">18</p>
        <div className="w-full bg-slate-600 rounded-full h-2 mt-2">
          <div className="bg-orange-500 h-2 rounded-full" style={{ width: '72%' }}></div>
        </div>
      </div>
      <div className="bg-slate-700/50 rounded p-4">
        <p className="text-slate-400 text-sm">Detection Rate</p>
        <p className="text-cyan-400 font-bold text-2xl mt-2">94%</p>
        <div className="w-full bg-slate-600 rounded-full h-2 mt-2">
          <div className="bg-cyan-500 h-2 rounded-full" style={{ width: '94%' }}></div>
        </div>
      </div>
    </div>
  </div>
)

const AuditLogTable = () => (
  <div className="p-6">
    <h3 className="text-lg font-semibold text-slate-100 mb-4">📜 Audit Log</h3>
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-slate-700">
            <th className="text-left py-3 px-4 text-slate-400 font-semibold">Timestamp</th>
            <th className="text-left py-3 px-4 text-slate-400 font-semibold">Action</th>
            <th className="text-left py-3 px-4 text-slate-400 font-semibold">User</th>
            <th className="text-left py-3 px-4 text-slate-400 font-semibold">Status</th>
            <th className="text-left py-3 px-4 text-slate-400 font-semibold">Details</th>
          </tr>
        </thead>
        <tbody>
          {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
            <tr key={i} className="border-b border-slate-800 hover:bg-slate-700/30 transition-colors">
              <td className="py-3 px-4 text-slate-300">{new Date(Date.now() - i * 3600000).toLocaleTimeString()}</td>
              <td className="py-3 px-4 text-slate-300">Evidence Collected</td>
              <td className="py-3 px-4 text-slate-300">forensics@system</td>
              <td className="py-3 px-4">
                <span className="px-2 py-1 text-xs font-semibold rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                  SUCCESS
                </span>
              </td>
              <td className="py-3 px-4 text-slate-400 text-xs">Hash: {Math.random().toString(36).substring(7).toUpperCase()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  </div>
)

const BlockchainForensics = () => (
  <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 m-6">
    <h3 className="text-lg font-semibold text-slate-100 mb-4">⛓️ Blockchain Forensics</h3>
    <div className="space-y-3">
      {[1, 2, 3].map((i) => (
        <div key={i} className="bg-slate-700/50 rounded p-4 border border-slate-600">
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <p className="font-semibold text-cyan-400">Transaction {i}</p>
              <p className="text-xs text-slate-400 mt-1">Tx ID: 0x{Math.random().toString(16).substring(2, 18).toUpperCase()}</p>
              <p className="text-xs text-slate-400">Dilithium Signature: VERIFIED ✓</p>
            </div>
            <div className="text-right">
              <p className="text-emerald-400 font-bold">Block #{892341 + i}</p>
              <p className="text-xs text-slate-400">{new Date(Date.now() - i * 3600000).toLocaleTimeString()}</p>
            </div>
          </div>
        </div>
      ))}
    </div>
  </div>
)

const EvidenceBrowserUI = () => (
  <div className="space-y-3 p-6">
    <h3 className="text-lg font-semibold text-slate-100 mb-4">🔍 Evidence Inventory</h3>
    {['System Logs', 'Network Traffic', 'Memory Dumps', 'Disk Snapshots', 'Registry Hives'].map((type, i) => (
      <div key={i} className="bg-slate-800 border border-slate-700 rounded-lg p-4 hover:border-emerald-500/50 transition-colors">
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <h4 className="font-semibold text-slate-100">{type}</h4>
            <p className="text-xs text-slate-400 mt-1">Size: {Math.floor(Math.random() * 5000) + 100} MB</p>
            <p className="text-xs text-slate-400">Hash: SHA256-{Math.random().toString(36).substring(2, 12).toUpperCase()}</p>
          </div>
          <span className="px-2 py-1 text-xs font-semibold rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
            ✓ VERIFIED
          </span>
        </div>
      </div>
    ))}
  </div>
)

export default function ForensicsAdvancedPage() {
  const [activeTab, setActiveTab] = useState('overview')

  return (
    <div className="h-full flex flex-col bg-gradient-to-br from-slate-900 via-slate-900 to-slate-800 overflow-y-auto">
      {/* Header */}
      <PageHeader />

      {/* Tabs */}
      <div className="border-b border-slate-700 bg-slate-900/30 px-6 flex gap-8 sticky top-0 z-10">
        {[
          { id: 'overview', label: '📊 Overview' },
          { id: 'reports', label: '📋 Reports' },
          { id: 'threat', label: '⚡ Threats' },
          { id: 'audit', label: '📜 Audit' },
          { id: 'blockchain', label: '⛓️ Blockchain' },
          { id: 'evidence', label: '🔍 Evidence' },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-4 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${activeTab === tab.id
                ? 'border-cyan-500 text-cyan-400'
                : 'border-transparent text-slate-400 hover:text-slate-300'
              }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        {activeTab === 'overview' && (
          <>
            <StatsGrid />
            <ReportsList />
          </>
        )}
        {activeTab === 'reports' && <ReportsList />}
        {activeTab === 'threat' && <ThreatSimulation />}
        {activeTab === 'audit' && <AuditLogTable />}
        {activeTab === 'blockchain' && <BlockchainForensics />}
        {activeTab === 'evidence' && <EvidenceBrowserUI />}
      </div>

      {/* Footer */}
      <div className="border-t border-slate-700 bg-slate-900/50 backdrop-blur-sm px-6 py-3 grid grid-cols-5 gap-4 text-center text-xs sticky bottom-0">
        <div>
          <p className="text-slate-400 font-medium">Total Incidents</p>
          <p className="text-cyan-400 font-bold text-sm">24</p>
        </div>
        <div>
          <p className="text-slate-400 font-medium">Critical</p>
          <p className="text-red-400 font-bold text-sm">3</p>
        </div>
        <div>
          <p className="text-slate-400 font-medium">Resolved</p>
          <p className="text-emerald-400 font-bold text-sm">18</p>
        </div>
        <div>
          <p className="text-slate-400 font-medium">Pending</p>
          <p className="text-orange-400 font-bold text-sm">6</p>
        </div>
        <div>
          <p className="text-slate-400 font-medium">Last Update</p>
          <p className="text-purple-400 font-bold text-sm">Just now</p>
        </div>
      </div>
    </div>
  )
}
