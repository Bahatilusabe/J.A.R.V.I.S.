import { useState } from 'react'
import { ChevronDown, AlertCircle, TrendingDown, CheckCircle } from 'lucide-react'

export interface TimelineEvent {
  id: string
  timestamp: string
  step: number
  phase: 'reconnaissance' | 'weaponization' | 'delivery' | 'exploitation' | 'installation' | 'command' | 'exfiltration'
  severity: 'critical' | 'high' | 'medium' | 'low'
  description: string
  probability: number
  indicators: string[]
  mitigations?: string[]
  expandable?: boolean
}

export interface ExplanationTimelineProps {
  events: TimelineEvent[]
  onEventClick?: (eventId: string) => void
  className?: string
}

const PhaseColors: Record<TimelineEvent['phase'], string> = {
  reconnaissance: 'bg-blue-500',
  weaponization: 'bg-purple-500',
  delivery: 'bg-pink-500',
  exploitation: 'bg-red-500',
  installation: 'bg-orange-500',
  command: 'bg-yellow-500',
  exfiltration: 'bg-red-600',
}

const SeverityColors: Record<TimelineEvent['severity'], string> = {
  critical: 'text-red-600 bg-red-50',
  high: 'text-orange-600 bg-orange-50',
  medium: 'text-yellow-600 bg-yellow-50',
  low: 'text-blue-600 bg-blue-50',
}

const SeverityIcons: Record<TimelineEvent['severity'], React.ReactNode> = {
  critical: <AlertCircle className="w-4 h-4" />,
  high: <TrendingDown className="w-4 h-4" />,
  medium: <AlertCircle className="w-4 h-4" />,
  low: <CheckCircle className="w-4 h-4" />,
}

export function ExplanationTimeline({ events, onEventClick, className = '' }: ExplanationTimelineProps) {
  const [expandedEvents, setExpandedEvents] = useState<Set<string>>(new Set())

  const toggleExpanded = (eventId: string) => {
    const newExpanded = new Set(expandedEvents)
    if (newExpanded.has(eventId)) {
      newExpanded.delete(eventId)
    } else {
      newExpanded.add(eventId)
    }
    setExpandedEvents(newExpanded)
  }

  return (
    <div className={`space-y-4 ${className}`}>
      {events.map((event, index) => (
        <div key={event.id} className="relative">
          {/* Timeline connector */}
          {index < events.length - 1 && (
            <div className="absolute left-6 top-20 bottom-0 w-0.5 bg-slate-200" />
          )}

          {/* Timeline event */}
          <div
            className="relative bg-white rounded-lg border border-slate-200 hover:border-slate-300 transition-colors cursor-pointer"
            onClick={() => {
              if (event.expandable !== false) toggleExpanded(event.id)
              onEventClick?.(event.id)
            }}
          >
            {/* Main event header */}
            <div className="p-4 flex items-start gap-4">
              {/* Timeline dot */}
              <div className="flex-shrink-0 mt-1">
                <div className={`w-4 h-4 rounded-full border-2 border-white shadow-md ${PhaseColors[event.phase]}`} />
              </div>

              {/* Event content */}
              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-sm font-medium text-slate-600">
                        {event.phase.charAt(0).toUpperCase() + event.phase.slice(1)}
                      </span>
                      <span className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium ${SeverityColors[event.severity]}`}>
                        {SeverityIcons[event.severity]}
                        {event.severity.charAt(0).toUpperCase() + event.severity.slice(1)}
                      </span>
                    </div>
                    <p className="text-sm text-slate-900 font-medium">{event.description}</p>
                    <p className="text-xs text-slate-500 mt-1">{event.timestamp}</p>
                  </div>

                  {/* Probability indicator */}
                  {event.expandable !== false && (
                    <div className="flex items-center gap-3 flex-shrink-0">
                      <div className="flex items-center gap-2">
                        <div className="flex-1 h-2 bg-slate-700 rounded overflow-hidden">
                          <div
                            className={`h-full ${
                              event.probability > 0.7
                                ? 'bg-red-600'
                                : event.probability > 0.5
                                  ? 'bg-orange-600'
                                  : 'bg-yellow-600'
                            }`}
                            style={{ width: `${event.probability * 100}%` }}
                          />
                        </div>
                        <span className="text-xs font-medium text-slate-600 w-8 text-right">
                          {Math.round(event.probability * 100)}%
                        </span>
                      </div>
                      <ChevronDown
                        className={`w-4 h-4 text-slate-400 transition-transform ${
                          expandedEvents.has(event.id) ? 'rotate-180' : ''
                        }`}
                      />
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Expanded content */}
            {expandedEvents.has(event.id) && event.expandable !== false && (
              <div className="px-4 pb-4 pt-2 border-t border-slate-200 bg-slate-50/50">
                {/* Indicators */}
                {event.indicators.length > 0 && (
                  <div className="mb-4">
                    <h4 className="text-xs font-semibold text-slate-700 mb-2">Indicators of Compromise:</h4>
                    <ul className="space-y-1">
                      {event.indicators.map((indicator, idx) => (
                        <li key={idx} className="text-xs text-slate-600 flex items-start gap-2">
                          <span className="text-slate-400 flex-shrink-0">•</span>
                          <span className="break-words">{indicator}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Mitigations */}
                {event.mitigations && event.mitigations.length > 0 && (
                  <div>
                    <h4 className="text-xs font-semibold text-slate-700 mb-2">Recommended Mitigations:</h4>
                    <ul className="space-y-1">
                      {event.mitigations.map((mitigation, idx) => (
                        <li key={idx} className="text-xs text-slate-600 flex items-start gap-2">
                          <span className="text-green-600 flex-shrink-0">✓</span>
                          <span className="break-words">{mitigation}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}
