import React from 'react'
import { Shield, CheckCircle } from 'lucide-react'

export const ForensicsHeader: React.FC = () => (
  <div className="relative overflow-hidden border-b border-slate-700/50 bg-gradient-to-r from-slate-900 via-slate-900 to-slate-800">
    {/* Animated background */}
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      <div className="absolute -top-40 -right-40 w-80 h-80 bg-cyan-500/10 rounded-full blur-3xl"></div>
      <div className="absolute -bottom-20 -left-40 w-96 h-96 bg-purple-500/5 rounded-full blur-3xl"></div>
    </div>

    <div className="relative px-6 py-8">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="flex items-center gap-3 text-3xl font-bold bg-gradient-to-r from-slate-100 to-cyan-400 bg-clip-text text-transparent mb-2">
            <Shield className="h-8 w-8 text-cyan-400" />
            Forensics & Reports
          </h1>
          <p className="text-slate-400 text-sm max-w-2xl">
            Advanced blockchain forensics, threat simulation, and immutable evidence management
          </p>
        </div>
        <div className="flex items-center gap-2 bg-emerald-500/10 border border-emerald-500/30 rounded-lg px-3 py-2">
          <CheckCircle className="h-4 w-4 text-emerald-400" />
          <span className="text-xs font-semibold text-emerald-400">All Systems Secure</span>
        </div>
      </div>
    </div>
  </div>
)
