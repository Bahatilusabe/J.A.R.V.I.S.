/**
 * ForensicsTimeline
 *
 * Interactive vertical timeline visualization for forensics events.
 * Displays incident events chronologically with severity indicators,
 * actor information, and supporting evidence references.
 *
 * Features:
 * - Chronological event sequencing
 * - Severity-based color coding
 * - Evidence reference display
 * - Interactive event expansion
 * - Timestamp precision indicators
 */

import React, { useState } from 'react'
import type { TimelineEntry } from '../types/forensics.types'

interface ForensicsTimelineProps {
  events: TimelineEntry[]
  onSelectEvent?: (event: TimelineEntry) => void
  compact?: boolean
}

export const ForensicsTimeline: React.FC<ForensicsTimelineProps> = ({
  events,
  onSelectEvent,
  compact = false,
}) => {
  const [expandedEventId, setExpandedEventId] = useState<string | null>(null)

  const getSeverityColor = (severity: string): { bg: string; dot: string; text: string } => {
    const colors: Record<string, { bg: string; dot: string; text: string }> = {
      low: { bg: 'bg-emerald-500/10', dot: 'bg-emerald-400', text: 'text-emerald-300' },
      medium: { bg: 'bg-amber-500/10', dot: 'bg-amber-400', text: 'text-amber-300' },
      high: { bg: 'bg-orange-500/10', dot: 'bg-orange-400', text: 'text-orange-300' },
      critical: { bg: 'bg-red-500/10', dot: 'bg-red-400', text: 'text-red-300' },
      catastrophic: { bg: 'bg-pink-500/10', dot: 'bg-pink-500', text: 'text-pink-200' },
    }
    return colors[severity] || colors.medium
  }

  const formatTimestamp = (timestamp: string): { date: string; time: string; iso: string } => {
    const date = new Date(timestamp)
    return {
      date: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }),
      time: date.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: true,
      }),
      iso: date.toISOString(),
    }
  }

  if (events.length === 0) {
    return (
      <div className="flex items-center justify-center h-32 text-slate-400">
        <p className="text-sm">No timeline events available</p>
      </div>
    )
  }

  return (
    <div className="space-y-0">
      {events.map((event, index) => {
        const colors = getSeverityColor(event.severity)
        const timestamp = formatTimestamp(event.timestamp)
        const isExpanded = expandedEventId === `${index}-${event.timestamp}`
        const eventId = `${index}-${event.timestamp}`

        return (
          <div key={eventId} className="relative">
            {/* Timeline connector line */}
            {index < events.length - 1 && (
              <div className={`absolute left-[15px] top-[40px] w-0.5 h-12 ${colors.dot} opacity-30`}></div>
            )}

            {/* Event card */}
            <div
              className={`relative pl-12 pb-4 cursor-pointer transition-all ${isExpanded ? 'mb-4' : ''}`}
              onClick={() => {
                setExpandedEventId(isExpanded ? null : eventId)
                onSelectEvent?.(event)
              }}
            >
              {/* Timeline dot */}
              <div className={`absolute left-0 top-1 w-8 h-8 rounded-full border-2 border-slate-800 flex items-center justify-center ${colors.bg}`}>
                <div className={`w-3 h-3 rounded-full ${colors.dot}`}></div>
              </div>

              {/* Event content */}
              <div className={`${colors.bg} border border-slate-700 rounded-lg p-3 transition-all ${
                isExpanded ? 'border-slate-600 shadow-lg shadow-slate-900/50' : 'hover:border-slate-600'
              }`}>
                {/* Header */}
                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1">
                    <h4 className="text-sm font-semibold text-slate-100 line-clamp-2">
                      {event.event}
                    </h4>
                    <p className="text-xs text-slate-400 mt-1">
                      <span className="font-medium">{event.actor}</span>
                      {event.tick !== undefined && <span> • Tick {event.tick}</span>}
                    </p>
                  </div>
                  <div className="ml-2 flex-shrink-0">
                    <span
                      className={`inline-block px-2 py-1 text-xs font-semibold rounded-full border ${
                        event.severity === 'low'
                          ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30'
                          : event.severity === 'medium'
                            ? 'bg-amber-500/20 text-amber-300 border-amber-500/30'
                            : event.severity === 'high'
                              ? 'bg-orange-500/20 text-orange-300 border-orange-500/30'
                              : event.severity === 'critical'
                                ? 'bg-red-500/20 text-red-300 border-red-500/30'
                                : 'bg-pink-500/20 text-pink-300 border-pink-500/30'
                      }`}
                    >
                      {event.severity}
                    </span>
                  </div>
                </div>

                {/* Timestamp */}
                <div className="text-xs text-slate-500 mb-2">
                  <span className="font-mono">
                    {timestamp.date} {timestamp.time}
                  </span>
                </div>

                {/* Evidence references */}
                {event.evidence && event.evidence.length > 0 && (
                  <div className="mb-2 flex flex-wrap gap-1">
                    {event.evidence.slice(0, compact ? 2 : 5).map((_evRef, i) => (
                      <span
                        key={i}
                        className="inline-block px-2 py-1 text-xs bg-slate-700/50 text-slate-300 rounded border border-slate-600"
                      >
                        #{i + 1}
                      </span>
                    ))}
                    {event.evidence.length > (compact ? 2 : 5) && (
                      <span className="inline-block px-2 py-1 text-xs text-slate-400">
                        +{event.evidence.length - (compact ? 2 : 5)} more
                      </span>
                    )}
                  </div>
                )}

                {/* Expanded content */}
                {isExpanded && (
                  <div className="mt-3 pt-3 border-t border-slate-700/50 space-y-2">
                    {/* Full timestamp */}
                    <div className="text-xs">
                      <p className="text-slate-400 font-medium">Full Timestamp</p>
                      <p className="text-slate-300 font-mono mt-1 break-all">{timestamp.iso}</p>
                    </div>

                    {/* Evidence inventory */}
                    {event.evidence && event.evidence.length > 0 && (
                      <div className="text-xs">
                        <p className="text-slate-400 font-medium mb-2">Evidence ({event.evidence.length})</p>
                        <div className="space-y-1">
                          {event.evidence.map((evRef, i) => (
                            <div key={i} className="p-1.5 bg-slate-900/50 rounded border border-slate-700/30 font-mono text-slate-400 truncate">
                              {evRef}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Action details if present */}
                    {event.action && (
                      <div className="text-xs">
                        <p className="text-slate-400 font-medium mb-1">Action Taken</p>
                        <div className="space-y-1 bg-slate-900/30 p-2 rounded border border-slate-700/30">
                          <p className="text-slate-300">
                            <strong>Type:</strong> {event.action.actionType}
                          </p>
                          <p className="text-slate-300">
                            <strong>Performed by:</strong> {event.action.performedBy}
                          </p>
                          <p className="text-slate-300">
                            <strong>Result:</strong>{' '}
                            <span
                              className={
                                event.action.result === 'success'
                                  ? 'text-emerald-400'
                                  : event.action.result === 'partial'
                                    ? 'text-amber-400'
                                    : 'text-red-400'
                              }
                            >
                              {event.action.result}
                            </span>
                          </p>
                          {event.action.description && (
                            <p className="text-slate-400 mt-1 italic">{event.action.description}</p>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Expand indicator */}
                <div className="absolute top-3 right-3 text-slate-500">
                  <svg
                    className={`w-4 h-4 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
                  </svg>
                </div>
              </div>
            </div>
          </div>
        )
      })}

      {/* Timeline end marker */}
      <div className="relative pl-12 pb-4">
        <div className="absolute left-0 top-1 w-8 h-8 rounded-full border-2 border-slate-800 bg-slate-800 flex items-center justify-center">
          <div className="w-2 h-2 rounded-full bg-slate-600"></div>
        </div>
        <div className="text-xs text-slate-500 pt-1">End of timeline</div>
      </div>
    </div>
  )
}

export default ForensicsTimeline
