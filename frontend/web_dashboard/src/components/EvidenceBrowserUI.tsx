export const EvidenceBrowserUI = () => (
  <div className="space-y-3 p-6">
    <h3 className="text-lg font-semibold text-slate-100 mb-4">🔍 Evidence Inventory</h3>
    {['System Logs', 'Network Traffic', 'Memory Dumps', 'Disk Snapshots', 'Registry Hives'].map((type, i) => (
      <div
        key={i}
        className="bg-slate-800 border border-slate-700 rounded-lg p-4 hover:border-emerald-500/50 transition-colors"
      >
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
