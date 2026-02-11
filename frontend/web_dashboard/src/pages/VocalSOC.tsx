import React, { useState, useEffect } from 'react'
import { useVocalSOC } from '../hooks/useVocalSOC'
import { LiveTranscript } from '../components/LiveTranscript'
import { IntentCard } from '../components/IntentCard'
import { VoiceAuthBadge } from '../components/VoiceAuthBadge'
import { AlertCircle, Send, X } from 'lucide-react'

/**
 * VocalSOC Main Page
 * Integrated voice command center with all components
 * Features:
 * - Live microphone recording with waveform
 * - Real-time transcription display
 * - Intent recognition with confidence
 * - Voice authentication badge
 * - Command verification dialogue
 * - Offline cache fallback
 */
export const VocalSOC: React.FC = () => {
  const {
    isRecording,
    finalTranscript,
    liveTranscript,
    recognizedIntent,
    voiceAuth,
    isLoading,
    error,
    recognizeIntent,
    authenticateVoice,
  } = useVocalSOC()

  const [showConfirmation, setShowConfirmation] = useState(false)
  const [confirmationMessage, setConfirmationMessage] = useState('')
  const [isExecuting, setIsExecuting] = useState(false)

  // Auto-recognize intent when transcript is finalized
  useEffect(() => {
    if (finalTranscript && !recognizedIntent && !isLoading) {
      recognizeIntent(finalTranscript)
    }
  }, [finalTranscript, recognizedIntent, isLoading, recognizeIntent])

  // Auto-authenticate when recording stops
  useEffect(() => {
    if (!isRecording && finalTranscript && !voiceAuth && !isLoading) {
      authenticateVoice('')
    }
  }, [isRecording, finalTranscript, voiceAuth, isLoading, authenticateVoice])

  /**
   * Build confirmation message for destructive actions
   */
  const buildConfirmationMessage = () => {
    if (!recognizedIntent) return ''

    const { intent, riskLevel, slots } = recognizedIntent
    let message = `Are you sure you want to execute: **${intent}**?`

    if (slots && Object.keys(slots).length > 0) {
      message += `\n\nParameters:\n`
      Object.entries(slots).forEach(([key, value]) => {
        message += `- ${key}: ${value}\n`
      })
    }

    if (riskLevel === 'critical' || riskLevel === 'high') {
      message += `\n⚠️ **Warning**: This is a high-risk action.`
    }

    if (recognizedIntent.requires2FA) {
      message += `\n🔐 **2FA Required**: You will need to verify your identity.`
    }

    return message
  }

  /**
   * Execute the voice command
   */
  const handleExecuteCommand = async () => {
    if (!recognizedIntent || !voiceAuth?.verified) {
      return
    }

    setIsExecuting(true)

    try {
      // TODO: Call /policy/enforce endpoint with command details
      console.log('Executing command:', {
        intent: recognizedIntent.intent,
        slots: recognizedIntent.slots,
        voiceAuthConfidence: voiceAuth.confidence,
      })

      // Simulate execution delay
      await new Promise((resolve) => setTimeout(resolve, 1000))

      // Success message
      setConfirmationMessage(`✅ Command "${recognizedIntent.intent}" executed successfully!`)
      setTimeout(() => {
        setShowConfirmation(false)
        setConfirmationMessage('')
      }, 2000)
    } catch (err) {
      setConfirmationMessage(
        `❌ Command execution failed: ${err instanceof Error ? err.message : 'Unknown error'}`
      )
    } finally {
      setIsExecuting(false)
    }
  }

  return (
    <div className="flex flex-col h-full bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 gap-4 p-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-white">Voice Command Center (VocalSOC)</h1>
        {error && (
          <div className="flex items-center gap-2 px-4 py-2 bg-red-500 bg-opacity-10 border border-red-500 rounded">
            <AlertCircle size={18} className="text-red-400" />
            <span className="text-sm text-red-300">{error}</span>
          </div>
        )}
      </div>

      {/* Main layout: 2 columns (mic moved to topbar; removed left panel) */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-2 gap-4 overflow-hidden">
        {/* Center: Transcript & Intent */}
        <div className="lg:col-span-1 flex flex-col gap-4 overflow-y-auto">
          <LiveTranscript
            finalTranscript={finalTranscript}
            liveTranscript={liveTranscript}
            confidence={recognizedIntent?.confidence || 0}
            isRecording={isRecording}
          />

          <IntentCard
            intent={recognizedIntent}
            isLoading={isLoading}
            error={error}
          />
        </div>

        {/* Right: Voice Auth & Confirmation */}
        <div className="lg:col-span-1 flex flex-col gap-4 overflow-y-auto">
          <VoiceAuthBadge
            badge={voiceAuth}
            isVerifying={isLoading}
            error={error}
          />

          {/* Action Button */}
          {recognizedIntent && voiceAuth?.verified && (
            <button
              onClick={() => {
                setConfirmationMessage(buildConfirmationMessage())
                setShowConfirmation(true)
              }}
              disabled={isExecuting || !recognizedIntent.intent}
              className="w-full px-6 py-3 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white font-semibold rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              title="Execute recognized voice command"
            >
              <Send size={18} />
              Execute Command
            </button>
          )}

          {/* Offline Cache Info */}
          {!navigator.onLine && (
            <div className="p-4 bg-amber-500 bg-opacity-10 border border-amber-600 rounded-lg">
              <p className="text-xs text-amber-300">
                🔌 <span className="font-semibold">Offline Mode</span> - Using cached intents
              </p>
            </div>
          )}

          {/* Safety Notice */}
          <div className="p-4 bg-blue-500 bg-opacity-10 border border-blue-600 rounded-lg">
            <p className="text-xs text-blue-300 leading-relaxed">
              <span className="font-semibold">🔒 Security:</span> All voice commands require explicit confirmation. Destructive actions require 2FA.
            </p>
          </div>
        </div>
      </div>

      {/* Confirmation Dialog */}
      {showConfirmation && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-lg max-w-md w-full shadow-xl">
            {/* Header */}
            <div className="flex items-center justify-between p-6 border-b border-slate-700">
              <h2 className="text-lg font-bold text-white">Command Confirmation</h2>
              <button
                onClick={() => setShowConfirmation(false)}
                className="text-gray-400 hover:text-gray-200"
                title="Close confirmation dialog"
              >
                <X size={20} />
              </button>
            </div>

            {/* Body */}
            <div className="p-6 space-y-4">
              <div className="prose prose-invert max-w-none text-sm text-gray-300">
                {confirmationMessage.split('\n').map((line, idx) => {
                  if (line.startsWith('**') && line.endsWith('**')) {
                    return (
                      <p key={idx} className="font-semibold text-white">
                        {line.replace(/\*\*/g, '')}
                      </p>
                    )
                  }
                  if (line.startsWith('- ')) {
                    return (
                      <p key={idx} className="ml-4">
                        • {line.substring(2)}
                      </p>
                    )
                  }
                  if (line.startsWith('⚠️') || line.startsWith('🔐')) {
                    return (
                      <p key={idx} className="text-amber-300 font-semibold">
                        {line}
                      </p>
                    )
                  }
                  return line.trim() && <p key={idx}>{line}</p>
                })}
              </div>

              {/* Risk Warning */}
              {recognizedIntent && recognizedIntent.riskLevel === 'critical' && (
                <div className="p-3 bg-red-500 bg-opacity-20 border border-red-500 rounded text-red-300 text-xs font-semibold">
                  🚨 CRITICAL ACTION - Requires Manual Admin Approval
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="flex gap-3 p-6 border-t border-slate-700">
              <button
                onClick={() => setShowConfirmation(false)}
                disabled={isExecuting}
                className="flex-1 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white font-semibold rounded transition-colors disabled:opacity-50"
                title="Cancel command execution"
              >
                Cancel
              </button>
              <button
                onClick={handleExecuteCommand}
                disabled={isExecuting || !voiceAuth?.verified}
                className={`flex-1 px-4 py-2 font-semibold rounded transition-colors ${recognizedIntent?.riskLevel === 'critical'
                    ? 'bg-red-600 hover:bg-red-700 text-white disabled:opacity-50'
                    : 'bg-green-600 hover:bg-green-700 text-white disabled:opacity-50'
                  }`}
                title={isExecuting ? 'Executing...' : 'Confirm and execute command'}
              >
                {isExecuting ? 'Executing...' : 'Confirm & Execute'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
