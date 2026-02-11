export const ThreatSimulation = ({
  stats,
}: {
  stats: { attackSurface: number; vulnerabilities: number; detectionRate: number }
}) => (
  <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 m-6">
    <h3 className="text-lg font-semibold text-slate-100 mb-4">⚡ Threat Simulation Metrics</h3>
    <div className="grid grid-cols-3 gap-4">
      <div className="bg-slate-700/50 rounded p-4">
        <p className="text-slate-400 text-sm">Attack Surface</p>
        <p className="text-emerald-400 font-bold text-2xl mt-2">{stats.attackSurface.toLocaleString()}</p>
        <div className="w-full bg-slate-600 rounded-full h-2 mt-2 overflow-hidden">
          <div className="bg-emerald-500 h-2 rounded-full w-[45%]"></div>
        </div>
      </div>
      <div className="bg-slate-700/50 rounded p-4">
        <p className="text-slate-400 text-sm">Vulnerabilities Found</p>
        <p className="text-orange-400 font-bold text-2xl mt-2">{stats.vulnerabilities}</p>
        <div className="w-full bg-slate-600 rounded-full h-2 mt-2 overflow-hidden">
          <div className="bg-orange-500 h-2 rounded-full w-[72%]"></div>
        </div>
      </div>
      <div className="bg-slate-700/50 rounded p-4">
        <p className="text-slate-400 text-sm">Detection Rate</p>
        <p className="text-cyan-400 font-bold text-2xl mt-2">{stats.detectionRate}%</p>
        <div className="w-full bg-slate-600 rounded-full h-2 mt-2 overflow-hidden">
          <div className="bg-cyan-500 h-2 rounded-full w-[94%]"></div>
        </div>
      </div>
    </div>
  </div>
)
