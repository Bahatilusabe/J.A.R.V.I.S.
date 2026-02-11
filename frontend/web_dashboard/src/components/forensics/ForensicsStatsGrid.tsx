import React from 'react'
import { FileText, Lock, Package, CheckCircle, Calendar } from 'lucide-react'

interface ForensicReport {
  signed: boolean
}

interface EvidenceItem {
  status: 'verified' | 'pending' | 'failed'
}

interface StatsGridProps {
  reports: ForensicReport[]
  evidence: EvidenceItem[]
}

export const ForensicsStatsGrid: React.FC<StatsGridProps> = ({ reports, evidence }) => (
  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
    {/* Total Reports */}
    <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-4 hover:border-slate-600/50 transition-all">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-semibold text-slate-400 uppercase">Reports</span>
        <FileText className="h-4 w-4 text-blue-400" />
      </div>
      <div className="text-3xl font-bold text-slate-100">{reports.length}</div>
      <p className="text-xs text-slate-500 mt-1">Total generated</p>
    </div>

    {/* Signed Reports */}
    <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-lg p-4 hover:border-emerald-500/50 transition-all">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-semibold text-emerald-400 uppercase">Blockchain</span>
        <Lock className="h-4 w-4 text-emerald-400" />
      </div>
      <div className="text-3xl font-bold text-emerald-400">
        {reports.filter((r) => r.signed).length}
      </div>
      <p className="text-xs text-slate-400 mt-1">Signed & verified</p>
    </div>

    {/* Evidence Items */}
    <div className="bg-purple-500/10 border border-purple-500/30 rounded-lg p-4 hover:border-purple-500/50 transition-all">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-semibold text-purple-400 uppercase">Evidence</span>
        <Package className="h-4 w-4 text-purple-400" />
      </div>
      <div className="text-3xl font-bold text-purple-400">{evidence.length}</div>
      <p className="text-xs text-slate-400 mt-1">Artifacts collected</p>
    </div>

    {/* Verified Items */}
    <div className="bg-orange-500/10 border border-orange-500/30 rounded-lg p-4 hover:border-orange-500/50 transition-all">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-semibold text-orange-400 uppercase">Verified</span>
        <CheckCircle className="h-4 w-4 text-orange-400" />
      </div>
      <div className="text-3xl font-bold text-orange-400">
        {evidence.filter((e) => e.status === 'verified').length}
      </div>
      <p className="text-xs text-slate-400 mt-1">Chain of custody</p>
    </div>

    {/* Retention Days */}
    <div className="bg-cyan-500/10 border border-cyan-500/30 rounded-lg p-4 hover:border-cyan-500/50 transition-all">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-semibold text-cyan-400 uppercase">Retention</span>
        <Calendar className="h-4 w-4 text-cyan-400" />
      </div>
      <div className="text-3xl font-bold text-cyan-400">7 days</div>
      <p className="text-xs text-slate-400 mt-1">Evidence stored</p>
    </div>
  </div>
)
