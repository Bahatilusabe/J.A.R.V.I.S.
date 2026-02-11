import React, { useState } from 'react'
import { Shield, AlertCircle, RefreshCw } from 'lucide-react'
import { useTDS } from '../hooks/useTDS'
import { PacketStreamCanvas } from '../components/PacketStreamCanvas'
import { RuleList } from '../components/RuleList'
import { VPNSessionTable } from '../components/VPNSessionTable'
import { MicroSegmentationMap } from '../components/MicroSegmentationMap'
import { AttestationModal } from '../components/AttestationModal'
import { DPIRule } from '../types/tds.types' // Removed unused import to fix lint warning

export const TDS: React.FC = () => {
  const tds = useTDS()

  const [_selectedPacket, _setSelectedPacket] = useState<DPIRule | null>(null)
  const [_selectedRule, _setSelectedRule] = useState<DPIRule | null>(null)
  const [attestationOpen, setAttestationOpen] = useState(false)

  return (
    <div className="w-full h-full bg-gradient-to-br from-slate-900 to-slate-950 flex flex-col overflow-hidden">
      {/* Header */}
      <div className="flex-shrink-0 px-6 py-4 border-b border-slate-700/50 bg-slate-900/50 backdrop-blur">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-blue-600/20 rounded-lg border border-blue-500/50">
              <Shield size={24} className="text-blue-400" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">Tactical Defense Shield</h1>
              <p className="text-sm text-slate-400">Real-time threat detection and network security</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Connection Status */}
            <div className={`flex items-center gap-2 px-4 py-2 rounded-lg border ${
              tds.isConnected
                ? 'bg-green-500/10 border-green-500/40 text-green-300'
                : 'bg-red-500/10 border-red-500/40 text-red-300'
            }`}>
              <div className={`w-2 h-2 rounded-full ${tds.isConnected ? 'bg-green-500' : 'bg-red-500'} animate-pulse`} />
              {tds.isConnected ? 'Connected' : 'Disconnected'}
            </div>

            {/* Threat level */}
            {tds.anomalyRate > 0.05 && (
              <div className="flex items-center gap-2 px-4 py-2 bg-yellow-500/10 border border-yellow-500/40 rounded-lg text-yellow-300">
                <AlertCircle size={16} />
                <span className="text-sm font-medium">
                  {Math.round(tds.anomalyRate * 100)}% Anomalies
                </span>
              </div>
            )}

            {/* Refresh */}
            <button
              onClick={() => {
                tds.fetchRules()
                tds.fetchVPNSessions()
              }}
              className="p-2 hover:bg-slate-700 rounded text-slate-400 hover:text-white transition"
              title="Refresh data"
            >
              <RefreshCw size={18} />
            </button>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 overflow-hidden flex flex-col">
        {/* Packet stream - top */}
        <div className="flex-1 min-h-0 px-6 py-4">
          <div className="h-full rounded-lg overflow-hidden">
            <PacketStreamCanvas
              packets={tds.packetStream}
              blockingRate={tds.blockingRate}
              anomalyRate={tds.anomalyRate}
              isActive={tds.isConnected}
              onPacketClick={() => {
                // Handle packet click
              }}
            />
          </div>
        </div>

        {/* Middle section - Rules and VPN */}
        <div className="flex-1 min-h-0 px-6 py-4 gap-4 grid grid-cols-2">
          {/* Rules list */}
          <RuleList
            rules={tds.rules}
            signatures={tds.signatures}
            onSelectRule={(_rule) => {
              // Handle rule select
            }}
            onToggleRule={(_ruleId, _enabled) => {
              // Handle toggle
            }}
            onBlockSignature={(_sig) => {
              // Handle signature blocking
            }}
          />

          {/* VPN sessions */}
          <VPNSessionTable
            sessions={tds.vpnSessions}
            onTerminateSession={(sessionId) => tds.terminateVPNSession(sessionId)}
            onSessionSelect={() => {}}
          />
        </div>

        {/* Bottom section - Topology and selected details */}
        <div className="flex-1 min-h-0 px-6 py-4 gap-4 grid grid-cols-3">
          {/* Micro-segmentation map */}
          <div className="col-span-2">
            <MicroSegmentationMap
              nodes={tds.isConnected ? [] : []} // Would come from Redux
              flows={[]}
              zones={[]}
              onIsolateEndpoint={(nodeId) => tds.isolateEndpoint(nodeId, 'User initiated isolation')}
            />
          </div>

          {/* Alerts and quick actions */}
          <div className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-lg border border-slate-700/50 flex flex-col overflow-hidden">
            <div className="flex-shrink-0 px-4 py-3 border-b border-slate-700/50">
              <h3 className="font-bold text-white">Recent Alerts</h3>
            </div>

            <div className="flex-1 overflow-y-auto divide-y divide-slate-700/50">
              {tds.alerts.length === 0 ? (
                <div className="p-4 text-center text-slate-500">
                  <p className="text-sm">No recent alerts</p>
                </div>
              ) : (
                tds.alerts.slice(0, 8).map((alert) => (
                  <div key={alert.alertId} className="p-3 hover:bg-slate-700/30 transition">
                    <div className="flex items-start gap-2">
                      <div
                        className={`w-2 h-2 rounded-full mt-1 flex-shrink-0 ${
                          alert.severity === 'critical'
                            ? 'bg-red-500'
                            : alert.severity === 'high'
                              ? 'bg-orange-500'
                              : 'bg-yellow-500'
                        }`}
                      />
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-semibold text-white truncate">{alert.title}</p>
                        <p className="text-xs text-slate-400 mt-1 truncate">{alert.description}</p>
                        <p className="text-xs text-slate-500 mt-1">
                          {new Date(alert.timestamp).toLocaleTimeString()}
                        </p>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>

            {/* Quick actions */}
            <div className="flex-shrink-0 p-4 border-t border-slate-700/50 space-y-2">
              <button
                onClick={() => setAttestationOpen(true)}
                className="w-full px-4 py-2 bg-blue-600/20 hover:bg-blue-600/40 text-blue-300 rounded font-medium text-sm transition"
              >
                Device Attestation
              </button>
              <button
                onClick={() => {
                  // Block IP action
                  const ip = '0.0.0.0'
                  tds.blockIP(ip, 'User initiated block', 3600)
                }}
                className="w-full px-4 py-2 bg-red-600/20 hover:bg-red-600/40 text-red-300 rounded font-medium text-sm transition"
              >
                Block IP
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Attestation Modal */}
      <AttestationModal
        isOpen={attestationOpen}
        attestation={tds.currentAttestation}
        isLoading={false}
        onClose={() => setAttestationOpen(false)}
        onApprove={() => {
          setAttestationOpen(false)
        }}
        onDeny={() => {
          setAttestationOpen(false)
        }}
      />
    </div>
  )
}

export default TDS
