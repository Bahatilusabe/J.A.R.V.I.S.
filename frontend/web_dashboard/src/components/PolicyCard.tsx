import { FileCode, CheckCircle, AlertTriangle, Clock } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'

interface Policy {
  id: string
  name: string
  type?: string
  status?: string
  description?: string
  conditions?: unknown
  updatedAt?: string
}

interface PolicyCardProps {
  policy: Policy
  onToggle?: (id: string, enabled: boolean) => void
  onEdit?: (id: string) => void
  onSimulate?: (id: string) => void
}

const getTypeColor = (type?: string) => {
  switch (type) {
    case 'containment':
      return 'bg-red-500/10 text-red-500 border-red-500/20'
    case 'detection':
      return 'bg-blue-500/10 text-blue-500 border-blue-500/20'
    case 'prevention':
      return 'bg-green-500/10 text-green-500 border-green-500/20'
    default:
      return 'bg-gray-500/10 text-gray-500 border-gray-500/20'
  }
}

const getStatusIcon = (status?: string) => {
  switch (status) {
    case 'active':
      return <CheckCircle className="h-4 w-4 text-green-500" />
    case 'draft':
      return <Clock className="h-4 w-4 text-yellow-500" />
    default:
      return <AlertTriangle className="h-4 w-4 text-gray-500" />
  }
}

export default function PolicyCard({ policy, onToggle, onEdit, onSimulate }: PolicyCardProps) {
  const isActive = policy.status === 'active'
  const conditionsText = policy.conditions ? (typeof policy.conditions === 'object' ? JSON.stringify(policy.conditions as unknown as object, null, 2) : String(policy.conditions)) : null

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-lg p-4 hover:shadow-lg transition-shadow">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className={`h-10 w-10 rounded-lg flex items-center justify-center ${isActive ? 'bg-primary/10' : 'bg-slate-700'}`}>
            <FileCode className={`h-5 w-5 ${isActive ? 'text-primary' : 'text-slate-300'}`} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-medium text-slate-100">{policy.name}</h3>
              <span className="text-xs">{getStatusIcon(policy.status)}</span>
            </div>
            {policy.type && (
              <div className={`mt-1 text-xs inline-block px-2 py-0.5 rounded ${getTypeColor(policy.type)}`}>{policy.type}</div>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            className={`px-3 py-1 rounded text-sm ${isActive ? 'bg-green-600 text-white' : 'bg-slate-700 text-slate-200'}`}
            onClick={() => onToggle?.(policy.id, !isActive)}
          >
            {isActive ? 'Enabled' : 'Disabled'}
          </button>
        </div>
      </div>

      {policy.description && (
        <p className="text-sm text-slate-300 mt-3 line-clamp-3">{policy.description}</p>
      )}

      {conditionsText && (
        <div className="mt-3 text-xs">
          <div className="text-slate-400 mb-1">Conditions</div>
          <pre className="bg-slate-900 p-2 rounded text-xs max-h-24 overflow-auto">{conditionsText}</pre>
        </div>
      )}

      <div className="flex items-center justify-between mt-3 text-xs text-slate-400 border-t border-slate-700 pt-3">
        <div>Updated {policy.updatedAt ? formatDistanceToNow(new Date(policy.updatedAt), { addSuffix: true }) : 'Unknown'}</div>
        <div className="flex gap-2">
          <button onClick={() => onSimulate?.(policy.id)} className="px-2 py-1 bg-slate-700 rounded text-xs">Simulate</button>
          <button onClick={() => onEdit?.(policy.id)} className="px-2 py-1 bg-slate-700 rounded text-xs">Edit</button>
        </div>
      </div>
    </div>
  )
}
