import React from 'react'
import { Zap, Shield, AlertTriangle, CheckCircle2, Clock } from 'lucide-react'
import { ParsedIntent } from '../types/vocalsoc.types'

interface IntentCardProps {
  intent: ParsedIntent | null
  isLoading: boolean
  error?: string | null
}

/**
 * IntentCard Component
 * Displays parsed intent with extracted slots, confidence, and security requirements
 * - Shows intent name and description
 * - Lists extracted parameters (slots) with values
 * - Confidence score visualization
 * - Flags 2FA and manual approval requirements
 * - Risk level indicator with color coding
 */
export const IntentCard: React.FC<IntentCardProps> = ({ intent, isLoading, error }) => {
  // Risk level color mapping
  const getRiskColor = (level: 'low' | 'medium' | 'high' | 'critical') => {
    switch (level) {
      case 'low':
        return { bg: 'bg-green-500 bg-opacity-10', text: 'text-green-400', border: 'border-green-500' }
      case 'medium':
        return { bg: 'bg-yellow-500 bg-opacity-10', text: 'text-yellow-400', border: 'border-yellow-500' }
      case 'high':
        return { bg: 'bg-orange-500 bg-opacity-10', text: 'text-orange-400', border: 'border-orange-500' }
      case 'critical':
        return { bg: 'bg-red-500 bg-opacity-10', text: 'text-red-400', border: 'border-red-500' }
    }
  }

  // Intent icon based on intent type
  const getIntentIcon = (intentName: string) => {
    if (intentName.includes('contain') || intentName.includes('isolate')) {
      return <Shield size={20} />
    }
    if (intentName.includes('enable') || intentName.includes('disable')) {
      return <Zap size={20} />
    }
    if (intentName.includes('verify') || intentName.includes('auth')) {
      return <CheckCircle2 size={20} />
    }
    return <Zap size={20} />
  }

  if (error) {
    return (
      <div className="p-4 bg-red-500 bg-opacity-10 border border-red-500 rounded-lg">
        <div className="flex items-center gap-3">
          <AlertTriangle size={20} className="text-red-400" />
          <div>
            <h4 className="font-semibold text-red-300">Intent Recognition Error</h4>
            <p className="text-sm text-red-200 mt-1">{error}</p>
          </div>
        </div>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="p-6 bg-gradient-to-b from-slate-800 to-slate-900 rounded-lg border border-slate-700 animate-pulse">
        <div className="space-y-3">
          <div className="h-6 bg-slate-700 rounded w-1/2" />
          <div className="h-4 bg-slate-700 rounded w-full" />
          <div className="h-4 bg-slate-700 rounded w-3/4" />
        </div>
      </div>
    )
  }

  if (!intent) {
    return (
      <div className="p-6 bg-gradient-to-b from-slate-800 to-slate-900 rounded-lg border border-slate-700 text-center">
        <Clock size={32} className="text-slate-600 mx-auto mb-3 opacity-50" />
        <p className="text-sm text-gray-500">Waiting for intent recognition...</p>
        <p className="text-xs text-gray-600 mt-1">Speech will be processed and intent extracted</p>
      </div>
    )
  }

  const riskColors = getRiskColor(intent.riskLevel)
  const confidencePercent = Math.round(intent.confidence * 100)

  return (
    <div className="flex flex-col gap-4 bg-gradient-to-b from-slate-800 to-slate-900 rounded-lg border border-slate-700 p-6 h-full overflow-y-auto">
      {/* Intent Header */}
      <div className={`p-4 rounded-lg border ${riskColors.border} ${riskColors.bg}`}>
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-3 flex-1">
            <div className={`mt-1 ${riskColors.text}`}>{getIntentIcon(intent.intent)}</div>
            <div className="flex-1 min-w-0">
              <h3 className="font-bold text-lg text-white truncate">{intent.intent}</h3>
              <p className="text-xs text-gray-400 mt-1 capitalize">
                Risk Level: <span className={`font-semibold ${riskColors.text}`}>{intent.riskLevel}</span>
              </p>
            </div>
          </div>

          {/* Confidence Badge */}
          <div className="flex flex-col items-end gap-1 flex-shrink-0">
            <div className="text-2xl font-bold text-blue-400">{confidencePercent}%</div>
            <p className="text-xs text-gray-400">confidence</p>
          </div>
        </div>

        {/* Confidence bar */}
        <div className="mt-3 w-full h-2 bg-slate-700 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-blue-500 to-cyan-500 transition-all duration-300"
            style={{ width: `${confidencePercent}%` }}
          />
        </div>
      </div>

      {/* Action Target */}
      {intent.slots && Object.keys(intent.slots).length > 0 && (
        <div className="space-y-3">
          <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wide">
            Extracted Parameters
          </h4>
          <div className="space-y-2">
            {Object.entries(intent.slots).map(([key, value]) => (
              <div
                key={key}
                className="flex items-start gap-3 p-3 bg-slate-800 rounded border border-slate-700"
              >
                <span className="text-xs font-medium text-gray-500 uppercase min-w-fit">
                  {key}:
                </span>
                <span className="text-sm text-gray-200 font-semibold truncate">
                  {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Security Requirements */}
      <div className="space-y-2">
        <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wide">
          Security Requirements
        </h4>

        <div className="space-y-2">
          {/* 2FA Requirement */}
          <div
            className={`flex items-center gap-3 p-3 rounded border ${
              intent.requires2FA
                ? 'bg-amber-500 bg-opacity-10 border-amber-600'
                : 'bg-green-500 bg-opacity-10 border-green-600'
            }`}
          >
            <Shield
              size={16}
              className={intent.requires2FA ? 'text-amber-400' : 'text-green-400'}
            />
            <div className="flex-1">
              <p className="text-xs font-medium text-gray-300">2FA Verification</p>
              <p className={`text-xs ${intent.requires2FA ? 'text-amber-300' : 'text-green-300'}`}>
                {intent.requires2FA ? 'Required' : 'Not required'}
              </p>
            </div>
          </div>

          {/* Manual Approval Requirement */}
          <div
            className={`flex items-center gap-3 p-3 rounded border ${
              intent.requiresManualApproval
                ? 'bg-red-500 bg-opacity-10 border-red-600'
                : 'bg-green-500 bg-opacity-10 border-green-600'
            }`}
          >
            <CheckCircle2
              size={16}
              className={intent.requiresManualApproval ? 'text-red-400' : 'text-green-400'}
            />
            <div className="flex-1">
              <p className="text-xs font-medium text-gray-300">Manual Approval</p>
              <p
                className={`text-xs ${
                  intent.requiresManualApproval ? 'text-red-300' : 'text-green-300'
                }`}
              >
                {intent.requiresManualApproval ? 'Required' : 'Not required'}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Intent Description */}
    </div>
  )
}
