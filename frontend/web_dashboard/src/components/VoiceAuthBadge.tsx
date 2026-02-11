import React from 'react'
import { CheckCircle2, AlertCircle, XCircle, Fingerprint, TrendingUp } from 'lucide-react'
import { VoiceprintBadge } from '../types/vocalsoc.types'

interface VoiceAuthBadgeProps {
  badge: VoiceprintBadge | null
  isVerifying: boolean
  error?: string | null
}

/**
 * VoiceAuthBadge Component
 * Displays voiceprint identity verification status and speaker confidence
 * - Shows user identity with verification status
 * - Displays voiceprint match confidence score
 * - Spoofing risk indicator (anti-spoofing detection)
 * - Match quality bar with enrollment information
 * - Last verification timestamp
 */
export const VoiceAuthBadge: React.FC<VoiceAuthBadgeProps> = ({
  badge,
  isVerifying,
  error,
}) => {
  // Spoofing risk color mapping
  const getSpoofingRiskColor = (risk: 'none' | 'low' | 'medium' | 'high') => {
    switch (risk) {
      case 'none':
        return { bg: 'bg-green-500 bg-opacity-10', text: 'text-green-400', border: 'border-green-500' }
      case 'low':
        return { bg: 'bg-blue-500 bg-opacity-10', text: 'text-blue-400', border: 'border-blue-500' }
      case 'medium':
        return { bg: 'bg-yellow-500 bg-opacity-10', text: 'text-yellow-400', border: 'border-yellow-500' }
      case 'high':
        return { bg: 'bg-red-500 bg-opacity-10', text: 'text-red-400', border: 'border-red-500' }
    }
  }

  if (error) {
    return (
      <div className="p-4 bg-red-500 bg-opacity-10 border border-red-500 rounded-lg">
        <div className="flex items-center gap-3">
          <XCircle size={20} className="text-red-400" />
          <div>
            <h4 className="font-semibold text-red-300">Voice Authentication Error</h4>
            <p className="text-sm text-red-200 mt-1">{error}</p>
          </div>
        </div>
      </div>
    )
  }

  if (isVerifying) {
    return (
      <div className="p-6 bg-gradient-to-b from-slate-800 to-slate-900 rounded-lg border border-slate-700 animate-pulse">
        <div className="space-y-3">
          <div className="h-6 bg-slate-700 rounded w-2/3" />
          <div className="h-4 bg-slate-700 rounded w-full" />
          <div className="h-4 bg-slate-700 rounded w-3/4" />
        </div>
      </div>
    )
  }

  if (!badge) {
    return (
      <div className="p-6 bg-gradient-to-b from-slate-800 to-slate-900 rounded-lg border border-slate-700 text-center">
        <Fingerprint size={32} className="text-slate-600 mx-auto mb-3 opacity-50" />
        <p className="text-sm text-gray-500">Waiting for voice verification...</p>
        <p className="text-xs text-gray-600 mt-1">Your voiceprint will be verified</p>
      </div>
    )
  }

  const spoofingColors = getSpoofingRiskColor(badge.spoofingRisk)
  const confidencePercent = Math.round(badge.confidence * 100)
  const matchPercent = Math.round(badge.matchScore * 100)

  return (
    <div className="flex flex-col gap-4 bg-gradient-to-b from-slate-800 to-slate-900 rounded-lg border border-slate-700 p-6 h-full overflow-y-auto">
      {/* User Identity Header */}
      <div className="flex items-start gap-4">
        {/* Avatar placeholder with initial */}
        <div className="flex-shrink-0">
          <div
            className={`w-12 h-12 rounded-full flex items-center justify-center font-bold text-lg ${
              badge.verified
                ? 'bg-gradient-to-br from-green-500 to-emerald-600'
                : 'bg-gradient-to-br from-gray-600 to-gray-700'
            }`}
          >
            {badge.displayName.charAt(0).toUpperCase()}
          </div>
        </div>

        {/* User info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h3 className="font-bold text-white truncate">{badge.displayName}</h3>
            {badge.verified && (
              <CheckCircle2 size={18} className="text-green-400 flex-shrink-0" />
            )}
          </div>
          <p className="text-xs text-gray-400 mt-0.5">
            {badge.verified ? 'Voice Verified' : 'Verification Pending'}
          </p>
        </div>
      </div>

      {/* Verification Status Card */}
      <div
        className={`p-4 rounded-lg border ${
          badge.verified
            ? 'bg-green-500 bg-opacity-10 border-green-600'
            : 'bg-yellow-500 bg-opacity-10 border-yellow-600'
        }`}
      >
        <div className="flex items-center gap-3">
          {badge.verified ? (
            <CheckCircle2 size={20} className="text-green-400" />
          ) : (
            <AlertCircle size={20} className="text-yellow-400" />
          )}
          <div>
            <p className="font-semibold text-white text-sm">
              {badge.verified ? 'Identity Verified' : 'Identity Verification In Progress'}
            </p>
            <p className={`text-xs mt-1 ${badge.verified ? 'text-green-300' : 'text-yellow-300'}`}>
              Voiceprint confidence: {confidencePercent}%
            </p>
          </div>
        </div>
      </div>

      {/* Voiceprint Match Score */}
      <div className="space-y-3">
        <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wide">
          Voiceprint Match Quality
        </h4>

        <div className="space-y-2">
          {/* Match score bar */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-gray-400">Enrollment Match</span>
              <span className="text-sm font-bold text-blue-400">{matchPercent}%</span>
            </div>
            <div className="w-full h-2.5 bg-slate-700 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-blue-500 to-cyan-500 transition-all duration-300"
                style={{ width: `${matchPercent}%` }}
              />
            </div>
          </div>

          {/* Confidence bar */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-gray-400">Speaker Confidence</span>
              <span className="text-sm font-bold text-purple-400">{confidencePercent}%</span>
            </div>
            <div className="w-full h-2.5 bg-slate-700 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-purple-500 to-pink-500 transition-all duration-300"
                style={{ width: `${confidencePercent}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Anti-Spoofing Status */}
      <div className={`p-4 rounded-lg border ${spoofingColors.bg} ${spoofingColors.border}`}>
        <div className="flex items-start gap-3">
          <TrendingUp size={18} className={`flex-shrink-0 ${spoofingColors.text}`} />
          <div className="flex-1 min-w-0">
            <p className="text-xs font-semibold text-gray-300">Anti-Spoofing Detection</p>
            <p className={`text-xs mt-1 font-medium ${spoofingColors.text}`}>
              Spoofing Risk: <span className="uppercase">{badge.spoofingRisk}</span>
            </p>
            <p className="text-xs text-gray-400 mt-2">
              {badge.spoofingRisk === 'none' && 'No spoofing detected. Voice is authentic.'}
              {badge.spoofingRisk === 'low' && 'Low risk. Minor anomalies detected but likely authentic.'}
              {badge.spoofingRisk === 'medium' && 'Medium risk. Potential voice synthesis or replay detected.'}
              {badge.spoofingRisk === 'high' && 'High risk. Possible spoofing attempt detected. Reject command.'}
            </p>
          </div>
        </div>
      </div>

      {/* Enrollment Information */}
      <div className="grid grid-cols-2 gap-3">
        <div className="p-3 bg-slate-800 rounded border border-slate-700">
          <p className="text-xs text-gray-400 font-medium">Enrolled Voiceprints</p>
          <p className="text-lg font-bold text-white mt-1">{badge.enrolledVoiceprints}</p>
        </div>
        <div className="p-3 bg-slate-800 rounded border border-slate-700">
          <p className="text-xs text-gray-400 font-medium">Last Verified</p>
          <p className="text-xs text-gray-300 mt-1 truncate">
            {new Date(badge.lastVerified).toLocaleDateString('en-US', {
              month: 'short',
              day: 'numeric',
              hour: '2-digit',
              minute: '2-digit',
            })}
          </p>
        </div>
      </div>

      {/* Security Notice */}
      <div className="p-3 bg-blue-500 bg-opacity-10 rounded border border-blue-600">
        <p className="text-xs text-blue-300">
          <span className="font-semibold">🔒 Secure:</span> Your voiceprint is encrypted and stored securely. Never shared with third parties.
        </p>
      </div>
    </div>
  )
}
