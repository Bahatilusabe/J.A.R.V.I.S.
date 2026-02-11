import React, { useState } from 'react'
import { Shield, CheckCircle, XCircle, AlertTriangle, Loader } from 'lucide-react'
import { ZeroTrustAttestation } from '../types/tds.types'

interface AttestationModalProps {
  isOpen: boolean
  attestation: ZeroTrustAttestation | null
  isLoading: boolean
  onSubmit?: () => void
  onClose?: () => void
  onApprove?: () => void
  onDeny?: () => void
}

export const AttestationModal: React.FC<AttestationModalProps> = ({
  isOpen,
  attestation,
  isLoading,
  // onSubmit, // Removed unused prop to fix lint warning
  onClose,
  onApprove,
  onDeny,
}) => {
  const [_showChallenge, _setShowChallenge] = useState(false)

  if (!isOpen || !attestation) return null

  const getComplianceColor = (status: string): string => {
    switch (status) {
      case 'compliant':
        return 'text-green-400'
      case 'non_compliant':
        return 'text-red-400'
      default:
        return 'text-yellow-400'
    }
  }

  const getTrustColor = (score: number): string => {
    if (score >= 0.9) return 'text-green-400'
    if (score >= 0.7) return 'text-yellow-400'
    return 'text-red-400'
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-lg border border-blue-500/50 w-full max-w-2xl max-h-96 overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 p-6 border-b border-slate-700 bg-slate-900/80 backdrop-blur">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Shield size={24} className="text-blue-400" />
              <div>
                <h2 className="text-xl font-bold text-white">Device Attestation</h2>
                <p className="text-sm text-slate-400">Zero-Trust Verification Required</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-slate-700 rounded text-slate-400 hover:text-white transition"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Device Info */}
          <div className="bg-slate-800/50 border border-slate-700 rounded p-4">
            <h3 className="font-semibold text-white mb-3">Device Information</h3>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-slate-500">Device Name</p>
                <p className="text-white font-mono">{attestation.deviceName}</p>
              </div>
              <div>
                <p className="text-slate-500">Device ID</p>
                <p className="text-white font-mono text-xs">{attestation.deviceId.substring(0, 16)}...</p>
              </div>
              <div>
                <p className="text-slate-500">Operating System</p>
                <p className="text-white">
                  {attestation.osType.charAt(0).toUpperCase() + attestation.osType.slice(1)} {attestation.osVersion}
                </p>
              </div>
              <div>
                <p className="text-slate-500">Last Activity</p>
                <p className="text-white">{new Date(attestation.lastActivity).toLocaleString()}</p>
              </div>
            </div>
          </div>

          {/* Compliance Status */}
          <div className="bg-slate-800/50 border border-slate-700 rounded p-4">
            <h3 className="font-semibold text-white mb-3">Compliance Status</h3>
            <div className="flex items-center justify-between mb-4">
              <div>
                <p className="text-slate-400 text-sm">Overall Compliance</p>
                <p className={`text-2xl font-bold ${getComplianceColor(attestation.complianceStatus)}`}>
                  {attestation.complianceStatus.replace('_', ' ').toUpperCase()}
                </p>
              </div>
              <div className="text-center">
                <p className="text-slate-400 text-sm">Trust Score</p>
                <p className={`text-3xl font-bold ${getTrustColor(attestation.trustScore)}`}>
                  {(attestation.trustScore * 100).toFixed(0)}%
                </p>
              </div>
            </div>
          </div>

          {/* Attestation Claims */}
          <div className="bg-slate-800/50 border border-slate-700 rounded p-4">
            <h3 className="font-semibold text-white mb-3">Attestation Claims</h3>
            <div className="space-y-2">
              {/* TPM */}
              <div className="flex items-center justify-between p-2 hover:bg-slate-700/30 rounded">
                <div className="flex items-center gap-2">
                  <Shield size={16} className="text-blue-400" />
                  <span className="text-sm text-slate-300">TPM Enabled</span>
                </div>
                {attestation.claimStatuses['tpm'] ? (
                  <CheckCircle size={16} className="text-green-400" />
                ) : (
                  <XCircle size={16} className="text-red-400" />
                )}
              </div>

              {/* Secure Boot */}
              <div className="flex items-center justify-between p-2 hover:bg-slate-700/30 rounded">
                <div className="flex items-center gap-2">
                  <Shield size={16} className="text-blue-400" />
                  <span className="text-sm text-slate-300">Secure Boot</span>
                </div>
                {attestation.secureBoot ? (
                  <CheckCircle size={16} className="text-green-400" />
                ) : (
                  <XCircle size={16} className="text-red-400" />
                )}
              </div>

              {/* Disk Encryption */}
              <div className="flex items-center justify-between p-2 hover:bg-slate-700/30 rounded">
                <div className="flex items-center gap-2">
                  <Shield size={16} className="text-blue-400" />
                  <span className="text-sm text-slate-300">Disk Encryption</span>
                </div>
                {attestation.diskEncryption.enabled ? (
                  <CheckCircle size={16} className="text-green-400" />
                ) : (
                  <XCircle size={16} className="text-red-400" />
                )}
              </div>

              {/* Firewall */}
              <div className="flex items-center justify-between p-2 hover:bg-slate-700/30 rounded">
                <div className="flex items-center gap-2">
                  <Shield size={16} className="text-blue-400" />
                  <span className="text-sm text-slate-300">Firewall Enabled</span>
                </div>
                {attestation.firewall.enabled ? (
                  <CheckCircle size={16} className="text-green-400" />
                ) : (
                  <XCircle size={16} className="text-red-400" />
                )}
              </div>

              {/* Antivirus */}
              <div className="flex items-center justify-between p-2 hover:bg-slate-700/30 rounded">
                <div className="flex items-center gap-2">
                  <Shield size={16} className="text-blue-400" />
                  <span className="text-sm text-slate-300">Antivirus Installed & Enabled</span>
                </div>
                {attestation.antivirus.installed && attestation.antivirus.enabled ? (
                  <CheckCircle size={16} className="text-green-400" />
                ) : (
                  <XCircle size={16} className="text-red-400" />
                )}
              </div>

              {/* Patch Status */}
              <div className="flex items-center justify-between p-2 hover:bg-slate-700/30 rounded">
                <div className="flex items-center gap-2">
                  <Shield size={16} className="text-blue-400" />
                  <span className="text-sm text-slate-300">Patch Status</span>
                </div>
                <span
                  className={`text-xs px-2 py-1 rounded ${
                    attestation.patchStatus === 'up_to_date'
                      ? 'bg-green-500/20 text-green-300'
                      : 'bg-yellow-500/20 text-yellow-300'
                  }`}
                >
                  {attestation.patchStatus.replace('_', ' ')}
                </span>
              </div>
            </div>
          </div>

          {/* Vulnerabilities */}
          {attestation.vulnerabilities.count > 0 && (
            <div className="bg-red-500/10 border border-red-500/30 rounded p-4">
              <div className="flex items-center gap-2 mb-2">
                <AlertTriangle size={16} className="text-red-400" />
                <h3 className="font-semibold text-white">Found Vulnerabilities</h3>
              </div>
              <p className="text-sm text-red-300">
                {attestation.vulnerabilities.critical} critical, {attestation.vulnerabilities.high} high,{' '}
                {attestation.vulnerabilities.medium} medium, {attestation.vulnerabilities.count - attestation.vulnerabilities.critical - attestation.vulnerabilities.high - attestation.vulnerabilities.medium}{' '}
                other
              </p>
            </div>
          )}

          {/* Approval Required */}
          {attestation.approvalRequired && (
            <div className="bg-yellow-500/10 border border-yellow-500/30 rounded p-4">
              <div className="flex items-center gap-2">
                <AlertTriangle size={16} className="text-yellow-400" />
                <p className="text-sm text-yellow-300">
                  This device requires approval before network access can be granted.
                </p>
              </div>
            </div>
          )}

          {attestation.blockedReason && (
            <div className="bg-red-500/10 border border-red-500/30 rounded p-4">
              <div className="flex items-center gap-2">
                <XCircle size={16} className="text-red-400" />
                <p className="text-sm text-red-300">{attestation.blockedReason}</p>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="sticky bottom-0 p-6 border-t border-slate-700 bg-slate-900/80 backdrop-blur flex gap-3 justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-700/50 hover:bg-slate-700 text-slate-300 rounded font-medium transition"
          >
            Cancel
          </button>
          {attestation.approvalRequired && (
            <>
              <button
                onClick={onDeny}
                disabled={isLoading}
                className="px-4 py-2 bg-red-600/20 hover:bg-red-600/40 text-red-300 rounded font-medium transition disabled:opacity-50"
              >
                {isLoading ? <Loader size={16} className="animate-spin" /> : 'Deny'}
              </button>
              <button
                onClick={onApprove}
                disabled={isLoading}
                className="px-4 py-2 bg-green-600/20 hover:bg-green-600/40 text-green-300 rounded font-medium transition disabled:opacity-50 flex items-center gap-2"
              >
                {isLoading ? (
                  <>
                    <Loader size={16} className="animate-spin" />
                    Approving...
                  </>
                ) : (
                  'Approve'
                )}
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
