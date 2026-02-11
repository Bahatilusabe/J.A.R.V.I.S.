import React, { useEffect, useRef } from 'react'
import { MessageCircle, Copy, CheckCircle } from 'lucide-react'

interface LiveTranscriptProps {
  finalTranscript: string
  liveTranscript: string
  confidence: number // 0-1
  isRecording: boolean
  alternatives?: Array<{
    text: string
    confidence: number
  }>
}

/**
 * LiveTranscript Component
 * Displays real-time speech transcription with streaming text updates
 * - Shows final (committed) transcript in larger text
 * - Displays interim (streaming) text in dimmed/italicized style
 * - Confidence score with visual indicator
 * - Copy-to-clipboard functionality
 * - Alternative transcription suggestions
 */
export const LiveTranscript: React.FC<LiveTranscriptProps> = ({
  finalTranscript,
  liveTranscript,
  confidence,
  isRecording,
  alternatives = [],
}) => {
  const transcriptEndRef = useRef<HTMLDivElement>(null)
  const [copied, setCopied] = React.useState(false)

  // Auto-scroll to bottom when transcript updates
  useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [finalTranscript, liveTranscript])

  const handleCopy = () => {
    const text = finalTranscript || liveTranscript
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  // Format confidence as percentage
  const confidencePercent = Math.round(confidence * 100)

  // Determine confidence color
  const getConfidenceColor = () => {
    if (confidence >= 0.9) return 'text-green-400'
    if (confidence >= 0.7) return 'text-blue-400'
    if (confidence >= 0.5) return 'text-yellow-400'
    return 'text-red-400'
  }

  return (
    <div className="flex flex-col h-full bg-gradient-to-b from-slate-800 to-slate-900 rounded-lg border border-slate-700 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-slate-700">
        <div className="flex items-center gap-2">
          <MessageCircle size={18} className="text-blue-400" />
          <h3 className="text-sm font-semibold text-gray-200">Live Transcript</h3>
        </div>
        <div className="flex items-center gap-3">
          {/* Confidence indicator */}
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-400">Confidence:</span>
            <div className="flex items-center gap-1">
              <div className="w-16 h-2 bg-slate-700 rounded-full overflow-hidden">
                <div
                  className={`h-full bg-gradient-to-r from-blue-500 to-cyan-500 transition-all duration-300`}
                  style={{ width: `${confidencePercent}%` }}
                />
              </div>
              <span className={`text-xs font-semibold ${getConfidenceColor()}`}>
                {confidencePercent}%
              </span>
            </div>
          </div>

          {/* Copy button */}
          <button
            onClick={handleCopy}
            disabled={!finalTranscript && !liveTranscript}
            className="p-1.5 hover:bg-slate-700 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            title="Copy transcript"
          >
            {copied ? (
              <CheckCircle size={18} className="text-green-400" />
            ) : (
              <Copy size={18} className="text-gray-400 hover:text-gray-200" />
            )}
          </button>
        </div>
      </div>

      {/* Transcript content */}
      <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-4">
        {/* Final transcript */}
        {finalTranscript && (
          <div className="space-y-2">
            <div className="text-xs font-medium text-gray-500 uppercase tracking-wide">
              Final Text
            </div>
            <p className="text-base leading-relaxed text-gray-100 break-words">
              {finalTranscript}
            </p>
          </div>
        )}

        {/* Live/interim transcript */}
        {liveTranscript && (
          <div className="space-y-2">
            <div className="text-xs font-medium text-gray-600 uppercase tracking-wide">
              {isRecording ? 'Interim' : 'Finalized'}
            </div>
            <p
              className={`text-sm leading-relaxed break-words ${
                isRecording
                  ? 'text-gray-400 italic opacity-70 animate-pulse'
                  : 'text-gray-200'
              }`}
            >
              {liveTranscript}
            </p>
          </div>
        )}

        {/* Empty state */}
        {!finalTranscript && !liveTranscript && (
          <div className="flex-1 flex items-center justify-center text-center py-8">
            <div>
              <MessageCircle
                size={32}
                className="text-slate-600 mx-auto mb-3 opacity-50"
              />
              <p className="text-sm text-gray-500">
                {isRecording ? 'Listening for speech...' : 'No transcript yet'}
              </p>
              <p className="text-xs text-gray-600 mt-1">
                {isRecording ? 'Speak into your microphone' : 'Click to start recording'}
              </p>
            </div>
          </div>
        )}

        {/* Scroll anchor */}
        <div ref={transcriptEndRef} />
      </div>

      {/* Alternatives section */}
      {alternatives.length > 0 && (
        <div className="border-t border-slate-700 p-4 bg-slate-950 bg-opacity-50">
          <div className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-3">
            Alternative Interpretations
          </div>
          <div className="space-y-2">
            {alternatives.slice(0, 3).map((alt, idx) => (
              <div
                key={idx}
                className="flex items-start gap-2 p-2 bg-slate-800 rounded text-xs"
              >
                <span className="text-gray-600 font-medium">{idx + 1}.</span>
                <div className="flex-1">
                  <p className="text-gray-300">{alt.text}</p>
                  <div className="flex items-center gap-1 mt-1">
                    <div className="w-10 h-1 bg-slate-700 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-cyan-500 transition-all duration-300"
                        style={{ width: `${alt.confidence * 100}%` }}
                      />
                    </div>
                    <span className="text-gray-500">
                      {Math.round(alt.confidence * 100)}%
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recording indicator */}
      {isRecording && (
        <div className="px-4 py-2 bg-red-500 bg-opacity-10 border-t border-red-500 border-opacity-30 flex items-center gap-2">
          <div className="w-1.5 h-1.5 bg-red-500 rounded-full animate-pulse" />
          <span className="text-xs text-red-400 font-medium">Recording in progress...</span>
        </div>
      )}
    </div>
  )
}
