import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { formatDistanceToNow, format } from 'date-fns'
import { ArrowLeft, AlertTriangle, Target, Server, CheckCircle, Shield, Play } from 'lucide-react'
import { startTransition } from 'react'

import apiClient from '../utils/api'
import { CEDNarrativeCard } from '../components/CEDNarrativeCard'
import StatusChip from '../components/StatusChip'
import AppLayout from '../components/AppLayout'
import { useToast } from '../hooks/use-toast'

interface Incident {
  id: string
  title: string
  description?: string
  severity?: 'critical' | 'high' | 'medium' | 'low' | string
  status?: string
  source?: string
  vector?: string
  createdAt?: string
  updatedAt?: string
  affectedHosts?: string[]
  cedNarrative?: any
  confidence?: number
  predictedImpact?: number
  recommendedAction?: string
}

export default function IncidentDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { toast } = useToast()

  const incidentId = id || ''

  const { data: incident, isLoading } = useQuery<Incident, Error>({
    queryKey: ['incident', incidentId],
    queryFn: async (): Promise<Incident> => {
      const res = await apiClient.get(`/api/incidents/${incidentId}`)
      return res.data as Incident
    },
    enabled: !!incidentId,
  })

  interface AuditLog {
    id?: string
    timestamp?: string
    action?: string
    details?: Record<string, unknown>
  }

  const { data: auditLogs = [] } = useQuery<AuditLog[], Error>({
    queryKey: ['auditLogs', incidentId],
    queryFn: async (): Promise<AuditLog[]> => {
      const res = await apiClient.get('/api/audit-logs', { params: { targetId: incidentId } })
      return (res.data || []) as AuditLog[]
    },
    enabled: !!incidentId,
  })

  const mutation = useMutation({
    mutationFn: async (status: string) => {
      const res = await apiClient.patch(`/api/incidents/${incidentId}`, { status })
      return res.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['incidents'] })
      queryClient.invalidateQueries({ queryKey: ['incident', incidentId] })
      toast({ title: 'Status updated' })
    },
    onError: (err: unknown) => {
      const msg = (err as { message?: string })?.message || String(err)
      toast({ title: 'Failed to update', description: msg, variant: 'destructive' })
    },
  })

  const executeAction = useMutation({
    mutationFn: async (action: string) => {
      // create audit log
      await apiClient.post('/api/audit-logs', {
        action,
        targetId: incidentId,
        targetType: 'incident',
        userId: 'system',
        details: {
          recommendedAction: incident?.recommendedAction,
          executedBy: 'J.A.R.V.I.S',
          timestamp: new Date().toISOString(),
        },
      })
      // mark contained
      const res = await apiClient.patch(`/api/incidents/${incidentId}`, { status: 'contained' })
      return res.data
    },
    onSuccess: (_, action) => {
      queryClient.invalidateQueries({ queryKey: ['incident', incidentId] })
      queryClient.invalidateQueries({ queryKey: ['auditLogs', incidentId] })
      toast({ title: 'Action executed', description: `Executed: ${action}` })
    },
    onError: (err: unknown) => {
      const msg = (err as { message?: string })?.message || String(err)
      toast({ title: 'Action failed', description: msg, variant: 'destructive' })
    },
  })

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="h-24 bg-slate-800 animate-pulse rounded" />
      </div>
    )
  }

  if (!incident) {
    return (
      <div className="p-6">
        <div className="text-center py-12">
          <AlertTriangle className="h-12 w-12 mx-auto mb-3 text-muted-foreground" />
          <h2 className="text-xl font-semibold mb-2">Incident Not Found</h2>
          <p className="text-muted-foreground mb-4">The incident you&apos;re looking for doesn&apos;t exist.</p>
          <button onClick={() => startTransition(() => navigate('/incidents'))} className="px-4 py-2 rounded bg-slate-700 text-slate-200">
            <ArrowLeft className="h-4 w-4 mr-2 inline" /> Back
          </button>
        </div>
      </div>
    )
  }

  const getSeverityColor = (s?: string) => {
    switch (s) {
      case 'critical':
        return 'text-red-400 bg-red-900/10'
      case 'high':
        return 'text-orange-400 bg-orange-900/10'
      case 'medium':
        return 'text-yellow-400 bg-yellow-900/10'
      default:
        return 'text-blue-300 bg-blue-900/10'
    }
  }

  return (
    <AppLayout>
      <div className="p-6 space-y-6" data-testid="page-incident-detail">
        <div className="flex items-start justify-between gap-4">
          <div>
            <button onClick={() => startTransition(() => navigate('/incidents'))} className="text-slate-300 hover:underline mb-2 inline-flex items-center gap-2">
              <ArrowLeft className="h-4 w-4" /> Back
            </button>
            <h1 className="text-2xl font-semibold">{incident.title}</h1>
            <div className="flex items-center gap-3 mt-2">
              <span className={`px-2 py-0.5 rounded text-xs font-semibold border ${getSeverityColor(incident.severity)}`}>{incident.severity || 'low'}</span>
              <StatusChip mode="conscious" threatLevel={incident.severity as 'critical' | 'high' | 'medium' | 'low' | 'none' | undefined} />
              <span className="text-sm text-muted-foreground">ID: {incident.id.slice(0, 8)}</span>
            </div>
          </div>

          <div className="flex gap-2">
            {incident.status === 'open' && (
              <button onClick={() => mutation.mutate('investigating')} className="px-3 py-1 rounded border bg-slate-800"> <Play className="h-4 w-4 mr-2 inline" /> Investigate</button>
            )}
            {incident.status === 'investigating' && (
              <button onClick={() => mutation.mutate('contained')} className="px-3 py-1 rounded border bg-slate-800"> <Shield className="h-4 w-4 mr-2 inline" /> Contain</button>
            )}
            {incident.status !== 'resolved' && (
              <button onClick={() => mutation.mutate('resolved')} className="px-3 py-1 rounded bg-green-700 text-white"> <CheckCircle className="h-4 w-4 mr-2 inline" /> Resolve</button>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-4">
            <div className="rounded border border-slate-700 p-4">
              <h3 className="text-sm text-slate-400 mb-2">Description</h3>
              <p className="text-sm text-slate-200">{incident.description || 'No description provided'}</p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="rounded border border-slate-700 p-3">
                <div className="text-xs text-slate-400">Source</div>
                <div className="mt-1 text-sm">{incident.source || 'Unknown'}</div>
              </div>
              <div className="rounded border border-slate-700 p-3">
                <div className="text-xs text-slate-400">Vector</div>
                <div className="mt-1 text-sm">{incident.vector || 'Unknown'}</div>
              </div>
              <div className="rounded border border-slate-700 p-3">
                <div className="text-xs text-slate-400">Created</div>
                <div className="mt-1 text-sm">{incident.createdAt ? format(new Date(incident.createdAt), 'PPpp') : 'Unknown'}</div>
              </div>
              <div className="rounded border border-slate-700 p-3">
                <div className="text-xs text-slate-400">Last Updated</div>
                <div className="mt-1 text-sm">{incident.updatedAt ? formatDistanceToNow(new Date(incident.updatedAt), { addSuffix: true }) : 'Unknown'}</div>
              </div>
            </div>

            <div>
              {incident.cedNarrative ? (
                <CEDNarrativeCard narrative={incident.cedNarrative} />
              ) : (
                <div className="rounded border border-slate-700 p-6 text-center text-slate-400">
                  <Target className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">No AI analysis available</p>
                </div>
              )}
            </div>
          </div>

          <div className="space-y-4">
            <div className="rounded border border-slate-700 p-4">
              <h4 className="text-sm text-slate-400 mb-2">Recommended Action</h4>
              <div className="text-sm text-slate-200 mb-3">{incident.recommendedAction || 'No recommended action available'}</div>
              {incident.recommendedAction && (
                <div className="flex gap-2">
                  <button onClick={() => executeAction.mutate('execute-recommended')} className="px-3 py-1 rounded bg-cyan-600 text-white">Execute</button>
                  <button onClick={() => startTransition(() => navigate('/incidents'))} className="px-3 py-1 rounded border">Dismiss</button>
                </div>
              )}
            </div>

            <div className="rounded border border-slate-700 p-4">
              <h4 className="text-sm text-slate-400 mb-2">Affected Hosts</h4>
              <div className="flex flex-wrap gap-2">
                {(incident.affectedHosts || []).map((h) => (
                  <div key={h} className="px-2 py-1 rounded bg-slate-800 text-xs font-mono"> <Server className="h-3 w-3 inline mr-1" />{h}</div>
                ))}
                {(incident.affectedHosts || []).length === 0 && <div className="text-sm text-slate-400">None</div>}
              </div>
            </div>

            <div className="rounded border border-slate-700 p-4">
              <h4 className="text-sm text-slate-400 mb-2">Audit Trail</h4>
              <div className="text-sm text-slate-200 max-h-48 overflow-auto">
                {auditLogs.length === 0 && <div className="text-slate-400">No audit logs</div>}
                {auditLogs.map((a: AuditLog) => (
                  <div key={a.id || Math.random()} className="mb-2 text-xs border-b border-slate-700/40 pb-2">
                    <div className="flex items-center justify-between">
                      <div className="font-medium">{a.action}</div>
                      <div className="text-slate-500">{a.timestamp ? new Date(a.timestamp).toLocaleString() : ''}</div>
                    </div>
                    <div className="text-slate-400 text-xs">{a.details && typeof a.details === 'string' ? a.details : JSON.stringify(a.details || {})}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </AppLayout>
  )
}
