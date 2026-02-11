import React, { useState } from 'react'

interface CEDNarrative {
  id: string
  narrative: string
  probability: number
  confidence: number
  counterfactuals: string[]
  factors: string[]
  timestamp: string
}

interface CEDNarrativeCardProps {
  narrative: CEDNarrative
  isExpanded?: boolean
  onCopy?: (text: string) => void
  className?: string
}

/**
 * CED Narrative Card Component
 * Displays causal explanations with expandable details
 * Shows probability, confidence, and counterfactual suggestions
 */
export const CEDNarrativeCard: React.FC<CEDNarrativeCardProps> = ({
  narrative,
  isExpanded = false,
  onCopy,
  className = '',
}) => {
  const [expanded, setExpanded] = useState(isExpanded)
  const [copied, setCopied] = useState(false)

  const handleCopy = () => {
    const text = `${narrative.narrative}\n\nProbability: ${(narrative.probability * 100).toFixed(1)}%\nConfidence: ${(narrative.confidence * 100).toFixed(1)}%`
    if (onCopy) {
      onCopy(text)
    } else {
      navigator.clipboard.writeText(text)
    }
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const probabilityColor =
    narrative.probability > 0.7 ? 'text-red-400' : narrative.probability > 0.4 ? 'text-yellow-400' : 'text-green-400'

  const confidenceColor =
    narrative.confidence > 0.8 ? 'bg-green-500' : narrative.confidence > 0.6 ? 'bg-yellow-500' : 'bg-orange-500'

  return (
    <div className={`rounded-lg border border-slate-700 bg-slate-800/50 overflow-hidden ${className}`}>
      {/* Header */}
      <div className="p-4 border-b border-slate-700 cursor-pointer hover:bg-slate-700/30 transition-colors">
        <div className="flex items-start justify-between mb-2">
          <button
            onClick={() => setExpanded(!expanded)}
            className="flex items-start gap-3 flex-1 text-left"
          >
            <div className="mt-1">
              <div className={`w-6 h-6 rounded border-2 border-slate-600 flex items-center justify-center transition-transform ${expanded ? 'rotate-90' : ''}`}>
                <span className="text-slate-400">›</span>
              </div>
            </div>
            <div className="flex-1">
              <p className="text-slate-200 text-sm line-clamp-2 font-medium">{narrative.narrative}</p>
            </div>
          </button>

          <button
            onClick={handleCopy}
            className="ml-2 p-1 rounded hover:bg-slate-700 text-slate-400 hover:text-slate-300 transition-colors"
            title="Copy to clipboard"
          >
            {copied ? (
              <span className="text-green-400 text-sm font-medium">✓</span>
            ) : (
              <span className="text-lg">📋</span>
            )}
          </button>
        </div>

        {/* Inline metrics */}
        <div className="flex items-center gap-4 ml-9">
          <div>
            <span className="text-xs text-slate-400">Probability: </span>
            <span className={`text-sm font-bold ${probabilityColor}`}>{(narrative.probability * 100).toFixed(1)}%</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400">Confidence:</span>
            <div className="w-20 h-2 rounded-full bg-slate-700 overflow-hidden">
              <div
                className={`h-full transition-all ${confidenceColor}`}
              />
            </div>
            <span className="text-xs text-slate-400">{(narrative.confidence * 100).toFixed(0)}%</span>
          </div>
        </div>
      </div>

      {/* Expanded content */}
      {expanded && (
        <div className="p-4 space-y-4 bg-slate-900/30 border-t border-slate-700">
          {/* Contributing factors */}
          {narrative.factors.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wide mb-2">
                Contributing Factors
              </h4>
              <div className="space-y-1">
                {narrative.factors.map((factor, idx) => (
                  <div key={idx} className="flex items-start gap-2 text-xs text-slate-400">
                    <span className="text-slate-600 mt-1">▸</span>
                    <span>{factor}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Counterfactual suggestions */}
          {narrative.counterfactuals.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wide mb-2">
                Counterfactual Suggestions
              </h4>
              <div className="space-y-2">
                {narrative.counterfactuals.map((suggestion, idx) => (
                  <div key={idx} className="p-2 rounded bg-slate-800/50 border border-slate-700/50">
                    <p className="text-xs text-slate-300">{suggestion}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Timestamp */}
          <div className="pt-2 border-t border-slate-700">
            <span className="text-xs text-slate-500">Analyzed: {new Date(narrative.timestamp).toLocaleString()}</span>
          </div>
        </div>
      )}
    </div>
  )
}
