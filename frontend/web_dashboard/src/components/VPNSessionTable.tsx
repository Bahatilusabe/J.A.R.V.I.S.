import React, { useState, useMemo } from 'react'
import { Search, Power, Wifi, WifiOff, Globe } from 'lucide-react'
import { VPNSession } from '../types/tds.types'

interface VPNSessionTableProps {
  sessions: VPNSession[]
  onTerminateSession?: (sessionId: string) => void
  onSessionSelect?: (session: VPNSession) => void
}

export const VPNSessionTable: React.FC<VPNSessionTableProps> = ({
  sessions,
  onTerminateSession,
  onSessionSelect,
}) => {
  const [searchQuery, setSearchQuery] = useState('')
  const [filterTrust, setFilterTrust] = useState<string | 'all'>('all')
  const [sortBy, setSortBy] = useState<'lastActivity' | 'bandwidth' | 'latency'>('lastActivity')

  const filteredSessions = useMemo(() => {
    const filtered = sessions.filter((session) => {
      const matchesSearch =
        session.userId.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (session.deviceName?.toLowerCase().includes(searchQuery.toLowerCase()) ?? false) ||
        session.publicIp?.includes(searchQuery) ||
        session.internalIp?.includes(searchQuery)

      const matchesTrust = filterTrust === 'all' || session.trustLevel === filterTrust

      return matchesSearch && matchesTrust
    })

    // Sort
    const sorted = [...filtered]
    sorted.sort((a, b) => {
      switch (sortBy) {
        case 'lastActivity':
          return new Date(b.lastActivity).getTime() - new Date(a.lastActivity).getTime()
        case 'bandwidth':
          return b.bandwidth - a.bandwidth
        case 'latency':
          return a.latencyMs - b.latencyMs
        default:
          return 0
      }
    })

    return sorted
  }, [sessions, searchQuery, filterTrust, sortBy])

  const getTrustBadgeColor = (trust: string): string => {
    switch (trust) {
      case 'trusted':
        return 'bg-green-500/20 text-green-300 border-green-500/40'
      case 'unknown':
        return 'bg-yellow-500/20 text-yellow-300 border-yellow-500/40'
      case 'suspicious':
        return 'bg-red-500/20 text-red-300 border-red-500/40'
      default:
        return 'bg-slate-500/20 text-slate-300 border-slate-500/40'
    }
  }

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
  }

  const formatBandwidth = (bytes: number): string => {
    return formatBytes(bytes) + '/s'
  }

  const getProtocolColor = (protocol: string): string => {
    switch (protocol) {
      case 'wireguard':
        return 'text-blue-400'
      case 'openvpn':
        return 'text-green-400'
      case 'ipsec':
        return 'text-purple-400'
      default:
        return 'text-slate-400'
    }
  }

  const timeAgo = (dateString: string): string => {
    const date = new Date(dateString)
    const now = new Date()
    const seconds = Math.floor((now.getTime() - date.getTime()) / 1000)

    if (seconds < 60) return `${seconds}s ago`
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`
    return `${Math.floor(seconds / 86400)}d ago`
  }

  return (
    <div className="w-full h-full bg-gradient-to-br from-slate-900 to-slate-800 rounded-lg border border-purple-500/20 flex flex-col">
      {/* Header */}
      <div className="flex-shrink-0 p-4 border-b border-slate-700/50">
        <h2 className="text-lg font-bold text-white mb-4">VPN Sessions ({sessions.length})</h2>

        {/* Search bar */}
        <div className="flex gap-2 mb-3">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-500" size={16} />
            <input
              type="text"
              placeholder="Search by user, device, IP..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-3 py-2 bg-slate-800/50 border border-slate-600 rounded text-sm text-white placeholder-slate-500 focus:outline-none focus:border-purple-500 focus:bg-slate-800"
            />
          </div>
        </div>

        {/* Filters and sorts */}
        <div className="flex gap-3">
          <select
            value={filterTrust}
            onChange={(e) => setFilterTrust(e.target.value)}
            title="Filter by trust level"
            className="px-3 py-1.5 bg-slate-800/50 border border-slate-600 rounded text-sm text-white focus:outline-none focus:border-purple-500"
          >
            <option value="all">All Trust Levels</option>
            <option value="trusted">Trusted</option>
            <option value="unknown">Unknown</option>
            <option value="suspicious">Suspicious</option>
          </select>

          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as 'lastActivity' | 'bandwidth' | 'latency')}
            title="Sort by"
            className="px-3 py-1.5 bg-slate-800/50 border border-slate-600 rounded text-sm text-white focus:outline-none focus:border-purple-500"
          >
            <option value="lastActivity">Sort: Last Activity</option>
            <option value="bandwidth">Sort: Bandwidth</option>
            <option value="latency">Sort: Latency</option>
          </select>
        </div>
      </div>

      {/* Sessions table */}
      <div className="flex-1 overflow-x-auto">
        {filteredSessions.length === 0 ? (
          <div className="p-8 text-center text-slate-400">
            <Wifi size={32} className="mx-auto mb-2 text-slate-600" />
            <p>No VPN sessions found</p>
          </div>
        ) : (
          <table className="w-full border-collapse text-sm">
            <thead className="bg-slate-800/50 sticky top-0 border-b border-slate-700">
              <tr>
                <th className="px-4 py-3 text-left font-semibold text-slate-300">User / Device</th>
                <th className="px-4 py-3 text-left font-semibold text-slate-300">Protocol</th>
                <th className="px-4 py-3 text-left font-semibold text-slate-300">Connected</th>
                <th className="px-4 py-3 text-right font-semibold text-slate-300">Bandwidth</th>
                <th className="px-4 py-3 text-center font-semibold text-slate-300">Latency</th>
                <th className="px-4 py-3 text-center font-semibold text-slate-300">Trust</th>
                <th className="px-4 py-3 text-center font-semibold text-slate-300">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/50">
              {filteredSessions.map((session) => (
                <tr
                  key={session.sessionId}
                  onClick={() => onSessionSelect?.(session)}
                  className="hover:bg-slate-800/30 transition cursor-pointer"
                >
                  <td className="px-4 py-3 text-white">
                    <div>
                      <p className="font-medium">{session.userId}</p>
                      {session.deviceName && (
                        <p className="text-xs text-slate-400">{session.deviceName}</p>
                      )}
                      <div className="flex gap-2 mt-1">
                        {session.internalIp && (
                          <span className="text-xs bg-slate-800 px-2 py-0.5 rounded text-slate-300">
                            {session.internalIp}
                          </span>
                        )}
                        {session.publicIp && (
                          <span className="text-xs bg-slate-800 px-2 py-0.5 rounded text-slate-300">
                            {session.publicIp}
                          </span>
                        )}
                      </div>
                    </div>
                  </td>

                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <Globe size={14} className={getProtocolColor(session.protocol)} />
                      <span className="text-white font-medium text-xs">{session.protocol.toUpperCase()}</span>
                    </div>
                    <p className="text-xs text-slate-500 mt-1">{session.encryptionAlgo}</p>
                  </td>

                  <td className="px-4 py-3 text-slate-300 text-xs">
                    <p>{new Date(session.connectedAt).toLocaleString()}</p>
                    <p className="text-slate-500 mt-1">{timeAgo(session.lastActivity)}</p>
                  </td>

                  <td className="px-4 py-3 text-right">
                    <p className="text-white font-mono text-sm">
                      {formatBandwidth(session.bandwidth)}
                    </p>
                    <p className="text-xs text-slate-500 mt-1">
                      ↓ {formatBytes(session.bytesIn)} ↑ {formatBytes(session.bytesOut)}
                    </p>
                  </td>

                  <td className="px-4 py-3 text-center">
                    <div className="flex items-center justify-center gap-2">
                      <span className="text-white font-mono text-sm">{session.latencyMs}ms</span>
                      {session.latencyMs > 100 && (
                        <span className="text-xs text-yellow-400">⚠</span>
                      )}
                    </div>
                  </td>

                  <td className="px-4 py-3 text-center">
                    <span
                      className={`px-2 py-1 rounded text-xs border font-medium inline-flex items-center gap-1 ${getTrustBadgeColor(session.trustLevel)}`}
                    >
                      {session.trustLevel === 'trusted' ? (
                        <Wifi size={12} />
                      ) : session.trustLevel === 'suspicious' ? (
                        <WifiOff size={12} />
                      ) : null}
                      {session.trustLevel.charAt(0).toUpperCase() + session.trustLevel.slice(1)}
                    </span>
                  </td>

                  <td className="px-4 py-3 text-center">
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        onTerminateSession?.(session.sessionId)
                      }}
                      className="p-2 hover:bg-red-600/20 rounded text-slate-400 hover:text-red-400 transition"
                      title="Terminate session"
                    >
                      <Power size={16} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Footer stats */}
      <div className="flex-shrink-0 p-3 border-t border-slate-700/50 bg-slate-800/30 flex gap-4 text-xs text-slate-400">
        <div>
          <span className="font-medium">Active Sessions:</span>
          <span className="ml-2 text-white">{sessions.filter((s) => s.isActive).length}</span>
        </div>
        <div>
          <span className="font-medium">Total Bandwidth:</span>
          <span className="ml-2 text-white">
            {formatBandwidth(sessions.reduce((sum, s) => sum + s.bandwidth, 0))}
          </span>
        </div>
        <div>
          <span className="font-medium">Avg Latency:</span>
          <span className="ml-2 text-white">
            {sessions.length > 0
              ? Math.round(sessions.reduce((sum, s) => sum + s.latencyMs, 0) / sessions.length)
              : 0}
            ms
          </span>
        </div>
      </div>
    </div>
  )
}
