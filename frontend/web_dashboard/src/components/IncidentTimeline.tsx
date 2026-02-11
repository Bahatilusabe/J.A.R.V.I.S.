import { formatDistanceToNow } from 'date-fns'
import { AlertTriangle, Shield, CheckCircle, Clock, ArrowRight } from 'lucide-react'
import { Link } from 'react-router-dom'

type Incident = {
  id: string
  title: string
  description?: string | null
  cedNarrative?: string | null
  severity?: 'critical' | 'high' | 'medium' | 'low' | string
  status?: 'resolved' | 'contained' | 'investigating' | string
  createdAt?: string | number | Date | null
  recommendedAction?: string | null
}

interface IncidentTimelineProps {
  incidents: Incident[]
  className?: string
}

const severityColor = (severity?: string) => {
  switch (severity) {
    case 'critical':
      return 'bg-red-600'
    case 'high':
      return 'bg-orange-500'
    case 'medium':
      return 'bg-yellow-500'
    default:
      return 'bg-blue-500'
  }
}

const severityBadge = (severity?: string) => {
  switch (severity) {
    case 'critical':
      return 'text-red-600 bg-red-50 border-red-100'
    case 'high':
      return 'text-orange-600 bg-orange-50 border-orange-100'
    case 'medium':
      return 'text-yellow-600 bg-yellow-50 border-yellow-100'
    default:
      return 'text-blue-600 bg-blue-50 border-blue-100'
  }
}

const statusIcon = (status?: string) => {
  switch (status) {
    case 'resolved':
      return <CheckCircle className="h-4 w-4 text-green-500" />
    case 'contained':
      return <Shield className="h-4 w-4 text-blue-500" />
    case 'investigating':
      return <Clock className="h-4 w-4 text-yellow-500" />
    default:
      return <AlertTriangle className="h-4 w-4 text-red-500" />
  }
}

export function IncidentTimeline({ incidents, className = '' }: IncidentTimelineProps) {
  return (
    <div className={`bg-slate-800 rounded-lg shadow-sm overflow-hidden ${className}`} data-testid="incident-timeline">
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-700/40">
        <h3 className="text-lg font-medium">Incident Timeline</h3>
        <Link to="/incidents" className="text-sm text-slate-300 hover:text-cyan-300 flex items-center gap-2">
          View all
          <ArrowRight className="h-4 w-4" />
        </Link>
      </div>

      <div className="max-h-[420px] overflow-y-auto">
        {incidents.length === 0 ? (
          <div className="p-8 text-center text-slate-400">
            <Shield className="h-12 w-12 mx-auto mb-3 opacity-50" />
            <p>No active incidents</p>
          </div>
        ) : (
          <div className="divide-y divide-slate-700/40">
            {incidents.map((inc) => (
              <article key={inc.id} className="p-4 hover:bg-slate-900/40 transition-colors">
                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0 pt-1">
                    <div className={`h-3 w-3 rounded-full ${severityColor(inc.severity)} border-2 border-slate-900/40`} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-center gap-2 min-w-0">
                        {statusIcon(inc.status)}
                        <h4 className="font-semibold truncate">{inc.title}</h4>
                      </div>
                      <div className="flex flex-col items-end shrink-0">
                        <span className={`px-2 py-0.5 rounded text-xs font-semibold border ${severityBadge(inc.severity)}`}>{inc.severity || 'low'}</span>
                        <time className="text-xs text-slate-400">
                          {inc.createdAt ? formatDistanceToNow(new Date(inc.createdAt), { addSuffix: true }) : 'Unknown'}
                        </time>
                      </div>
                    </div>

                    <p className="text-sm text-slate-300 mt-2 line-clamp-2">{inc.description || inc.cedNarrative || 'No description available'}</p>

                    {inc.recommendedAction && (
                      <div className="mt-3 pt-3 border-t border-slate-700/30 flex items-center gap-2">
                        <span className="text-xs text-slate-400">Recommended:</span>
                        <span className="text-xs bg-slate-700/30 px-2 py-1 rounded font-medium">{inc.recommendedAction}</span>
                      </div>
                    )}
                  </div>
                </div>
              </article>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default IncidentTimeline
