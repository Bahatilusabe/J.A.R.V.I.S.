export const AuditLogTable = ({ logs, isLoading }: { logs: Record<string, unknown>[]; isLoading: boolean }) => (
  <div className="p-6">
    <h3 className="text-lg font-semibold text-slate-100 mb-4">📜 Audit Log</h3>
    {isLoading ? (
      <div className="space-y-2">
        {[1, 2, 3].map((i) => (
          <div key={i} className="bg-slate-800 rounded p-4 h-12 animate-pulse" />
        ))}
      </div>
    ) : (
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
            {logs.length > 0 ? (
              logs.map((log: Record<string, unknown>, i: number) => (
                <tr key={i} className="border-b border-slate-800 hover:bg-slate-700/30 transition-colors">
                  <td className="py-3 px-4 text-slate-300">
                    {typeof log.timestamp === 'string'
                      ? new Date(log.timestamp).toLocaleTimeString()
                      : 'N/A'}
                  </td>
                  <td className="py-3 px-4 text-slate-300">{(log.action as string) || 'Evidence Collected'}</td>
                  <td className="py-3 px-4 text-slate-300">{(log.actor as string) || 'forensics@system'}</td>
                  <td className="py-3 px-4">
                    <span className="px-2 py-1 text-xs font-semibold rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                      {(log.status as string) || 'SUCCESS'}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-slate-400 text-xs">
                    {((log.details as string)?.substring(0, 40)) || 'Hash: N/A'}
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={5} className="py-8 px-4 text-center text-slate-400">
                  No audit logs found
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    )}
  </div>
)
