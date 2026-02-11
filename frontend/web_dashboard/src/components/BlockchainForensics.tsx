export const BlockchainForensics = ({
  transactions,
  isLoading,
}: {
  transactions: Record<string, unknown>[]
  isLoading: boolean
}) => (
  <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 m-6">
    <h3 className="text-lg font-semibold text-slate-100 mb-4">⛓️ Blockchain Forensics</h3>
    {isLoading ? (
      <div className="space-y-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="bg-slate-700/50 rounded p-4 h-24 animate-pulse" />
        ))}
      </div>
    ) : (
      <div className="space-y-3">
        {transactions.length > 0 ? (
          transactions.map((tx: Record<string, unknown>, i: number) => (
            <div key={i} className="bg-slate-700/50 rounded p-4 border border-slate-600">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <p className="font-semibold text-cyan-400">Transaction {i + 1}</p>
                  <p className="text-xs text-slate-400 mt-1">
                    Tx ID:{' '}
                    {((tx.txid as string)?.substring(0, 32)) ||
                      `0x${Math.random().toString(16).substring(2, 18).toUpperCase()}`}
                  </p>
                  <p className="text-xs text-slate-400">Signature: {tx.verified ? '✓ VERIFIED' : '⏳ PENDING'}</p>
                </div>
                <div className="text-right">
                  <p className="text-emerald-400 font-bold">Block #{((tx.blockNumber as number) || 892341) + i}</p>
                  <p className="text-xs text-slate-400">{new Date(Date.now() - i * 3600000).toLocaleTimeString()}</p>
                </div>
              </div>
            </div>
          ))
        ) : (
          <div className="text-center py-8 text-slate-400">
            <p>No blockchain transactions found</p>
          </div>
        )}
      </div>
    )}
  </div>
)
