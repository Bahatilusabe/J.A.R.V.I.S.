import { ChevronDown, ChevronUp, AlertCircle, Lightbulb, Target } from 'lucide-react'
import { useState } from 'react'
import type { CEDExplanation } from '../types/ced.types'

export interface ExplanationPanelProps {
  explanation: CEDExplanation | null
  loading?: boolean
  className?: string
}

export function ExplanationPanel({ explanation, loading = false, className = '' }: ExplanationPanelProps) {
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['summary']))

  const toggleSection = (section: string) => {
    const newExpanded = new Set(expandedSections)
    if (newExpanded.has(section)) {
      newExpanded.delete(section)
    } else {
      newExpanded.add(section)
    }
    setExpandedSections(newExpanded)
  }

  if (loading) {
    return (
      <div className={`rounded-lg border border-slate-200 p-6 bg-white ${className}`}>
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
        </div>
      </div>
    )
  }

  if (!explanation) {
    return (
      <div className={`rounded-lg border border-slate-200 p-6 bg-slate-50 text-center ${className}`}>
        <p className="text-slate-600 text-sm">Select a prediction to view causal explanation</p>
      </div>
    )
  }

  const { naturalLanguage, minimalInterventions, confidence, baselineProbability } = explanation

  const sections = [
    {
      id: 'summary',
      title: 'Summary',
      icon: <AlertCircle className="w-4 h-4" />,
      content: naturalLanguage.summary,
    },
    {
      id: 'why',
      title: 'Why Chain Exists',
      icon: <Lightbulb className="w-4 h-4" />,
      content: naturalLanguage.whyChainExists,
    },
    {
      id: 'impact',
      title: 'Impact Assessment',
      icon: <Target className="w-4 h-4" />,
      content: naturalLanguage.impactAssessment,
    },
  ]

  return (
    <div className={`flex flex-col gap-4 rounded-lg border border-slate-200 p-4 bg-white ${className}`}>
      {/* Header with metadata */}
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-slate-900">Causal Explanation</h3>
        <div className="flex items-center gap-4 text-sm">
          <div className="flex flex-col items-end">
            <span className="text-slate-600">Baseline Risk</span>
            <span className="font-bold text-lg text-slate-900">{Math.round(baselineProbability * 100)}%</span>
          </div>
          <div className="flex flex-col items-end">
            <span className="text-slate-600">Confidence</span>
            <span className="font-bold text-lg text-blue-600">{Math.round(confidence * 100)}%</span>
          </div>
        </div>
      </div>

      {/* Key factors */}
      {naturalLanguage.keyFactors.length > 0 && (
        <div className="rounded-lg bg-blue-50 border border-blue-200 p-3">
          <h4 className="text-xs font-semibold text-blue-900 mb-2">Key Contributing Factors</h4>
          <ul className="space-y-1">
            {naturalLanguage.keyFactors.map((factor, idx) => (
              <li key={idx} className="text-sm text-blue-800 flex items-start gap-2">
                <span className="text-blue-600 flex-shrink-0">→</span>
                <span>{factor}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Sections */}
      <div className="space-y-3">
        {sections.map((section) => {
          const isExpanded = expandedSections.has(section.id)
          return (
            <div key={section.id} className="rounded-lg border border-slate-200 overflow-hidden">
              {/* Section header */}
              <button
                onClick={() => toggleSection(section.id)}
                className="w-full flex items-center justify-between p-3 hover:bg-slate-50 transition-colors"
              >
                <div className="flex items-center gap-2 text-slate-900 font-medium">
                  {section.icon}
                  {section.title}
                </div>
                {isExpanded ? (
                  <ChevronUp className="w-4 h-4 text-slate-400" />
                ) : (
                  <ChevronDown className="w-4 h-4 text-slate-400" />
                )}
              </button>

              {/* Section content */}
              {isExpanded && (
                <div className="px-3 pb-3 pt-0 border-t border-slate-200 bg-slate-50">
                  <p className="text-sm text-slate-700 leading-relaxed">{section.content}</p>
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* Minimal interventions */}
      {minimalInterventions.length > 0 && (
        <div className="rounded-lg bg-amber-50 border border-amber-200 p-4">
          <h4 className="font-semibold text-amber-900 mb-3 flex items-center gap-2">
            <Target className="w-4 h-4" />
            Recommended Minimal Interventions
          </h4>

          <div className="space-y-2">
            {minimalInterventions.map((intervention, idx) => (
              <div key={idx} className="rounded-lg bg-white border border-amber-100 p-3">
                <div className="flex items-start justify-between mb-1">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold text-amber-900">{intervention.target}</span>
                    <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-amber-100 text-amber-700">
                      {intervention.type}
                    </span>
                  </div>
                  <span className="text-xs font-bold text-green-600">
                    -{Math.round(intervention.expectedImpact * 100)}%
                  </span>
                </div>
                <p className="text-xs text-slate-600 mb-1">{intervention.description}</p>
                <div className="flex items-center gap-3 text-xs text-slate-500">
                  <span>Effort: <span className="font-semibold capitalize text-slate-700">{intervention.effort}</span></span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Confidence note */}
      <div className="rounded-lg bg-slate-50 border border-slate-200 p-3">
        <p className="text-xs text-slate-600">
          <span className="font-semibold text-slate-700">Confidence Level:</span> This explanation has {Math.round(confidence * 100)}% confidence based on the causal analysis model.
        </p>
      </div>
    </div>
  )
}

export default ExplanationPanel
