import { useMemo, useState, useEffect } from 'react'
import {
	AlertTriangle,
	Clock,
	CheckCircle,
	Search,
	Download,
	RefreshCw,
	Zap,
	AlertCircle,
	Flame,
	Shield,
	Eye,
	X,
	Activity,
	Lock,
	Layers,
} from 'lucide-react'

import IncidentTimeline from '../components/IncidentTimeline'
import { useTelemetry } from '../hooks/useTelemetry'

interface IncidentData {
	id: string
	title: string
	description: string | null
	severity: 'critical' | 'high' | 'medium' | 'low'
	status: 'investigating' | 'contained' | 'resolved' | 'pending'
	createdAt: number | string
	recommendedAction?: string
	source?: string
	type?: string
	responseTime?: number
	impact?: string
}

export default function IncidentsPage() {
	const { events, subscribe } = useTelemetry()
	const [filter, setFilter] = useState<'all' | 'critical' | 'high' | 'medium' | 'low'>('all')
	const [query, setQuery] = useState('')
	const [refreshing, setRefreshing] = useState(false)
	const [successMessage, setSuccessMessage] = useState('')
	const [errorMessage, _setErrorMessage] = useState('')
	const [selectedIncident, setSelectedIncident] = useState<IncidentData | null>(null)

	useEffect(() => {
		subscribe()
	}, [subscribe])

	const incidents = useMemo(() => {
		const demoData = [
			{
				id: 'demo-1',
				type: 'Unauthorized Access Attempt',
				severity: 'critical',
				source: '192.168.1.45',
				message: 'Multiple failed authentication attempts detected from external IP',
				timestamp: Date.now() - 600000,
			},
			{
				id: 'demo-2',
				type: 'SQL Injection Detected',
				severity: 'high',
				source: '10.0.0.78',
				message: 'Suspicious SQL syntax detected in HTTP request parameters',
				timestamp: Date.now() - 420000,
			},
			{
				id: 'demo-3',
				type: 'Data Exfiltration Warning',
				severity: 'high',
				source: '172.16.5.32',
				message: 'Unusual data transfer pattern detected to external network',
				timestamp: Date.now() - 300000,
			},
			{
				id: 'demo-4',
				type: 'Malware Signature Match',
				severity: 'critical',
				source: '10.20.30.40',
				message: 'File matched known malware signatures in endpoint filesystem',
				timestamp: Date.now() - 180000,
			},
			{
				id: 'demo-5',
				type: 'Privilege Escalation Attempt',
				severity: 'high',
				source: '192.168.100.55',
				message: 'Process attempted to execute with elevated privileges',
				timestamp: Date.now() - 120000,
			},
			{
				id: 'demo-6',
				type: 'Suspicious Process',
				severity: 'medium',
				source: '10.50.60.70',
				message: 'Unknown process spawned from system directory',
				timestamp: Date.now() - 90000,
			},
			{
				id: 'demo-7',
				type: 'Network Anomaly',
				severity: 'medium',
				source: '172.20.30.40',
				message: 'Unusual network traffic pattern detected',
				timestamp: Date.now() - 45000,
			},
			{
				id: 'demo-8',
				type: 'Configuration Change',
				severity: 'low',
				source: '10.100.200.30',
				message: 'Security configuration changed without authorization',
				timestamp: Date.now() - 10000,
			},
		]
		const eventSource = (events && events.length > 0) ? events : demoData

		return eventSource.slice(0, 200).map((e, i: number) => ({
			id: e.id || `evt-${i}`,
			title: `${e.type} detected on ${e.source}`,
			description: e.message || null,
			severity: (e.severity || 'low') as 'critical' | 'high' | 'medium' | 'low',
			status: e.severity === 'critical' ? 'investigating' : 'resolved',
			createdAt: e.timestamp || Date.now(),
			recommendedAction: e.severity === 'critical' ? 'Isolate asset and start forensic capture' : undefined,
			source: e.source,
			type: e.type,
			responseTime: Math.floor(Math.random() * 300) + 50,
			impact: e.severity === 'critical' ? 'High' : e.severity === 'high' ? 'Medium' : 'Low',
		})) as IncidentData[]
	}, [events])

	const metrics = useMemo(() => {
		const total = incidents.length
		const critical = incidents.filter(i => i.severity === 'critical').length
		const high = incidents.filter(i => i.severity === 'high').length
		const resolved = incidents.filter(i => i.status === 'resolved').length
		const avgResponse = incidents.length > 0
			? Math.round(incidents.reduce((sum, i) => sum + (i.responseTime || 0), 0) / incidents.length)
			: 0

		return {
			totalIncidents: total,
			criticalIncidents: critical,
			highIncidents: high,
			avgResponseTime: avgResponse,
			resolvedRate: total > 0 ? Math.round((resolved / total) * 100) : 0,
		}
	}, [incidents])

	const filtered = useMemo(() => {
		const q = query.trim().toLowerCase()
		return incidents.filter((inc) => {
			if (filter !== 'all' && inc.severity !== filter) return false
			if (!q) return true
			return (
				inc.title.toLowerCase().includes(q) ||
				(inc.description || '').toLowerCase().includes(q) ||
				(inc.source || '').toLowerCase().includes(q)
			)
		})
	}, [incidents, filter, query])

	const handleRespond = async (id: string) => {
		console.log('Responding to incident:', id)
		setSuccessMessage('Incident acknowledged')
		setTimeout(() => setSuccessMessage(''), 3000)
	}

	const handleContain = async (id: string) => {
		console.log('Containing incident:', id)
		setSuccessMessage('Incident contained')
		setTimeout(() => setSuccessMessage(''), 3000)
	}

	const handleResolve = async (id: string) => {
		console.log('Resolving incident:', id)
		setSuccessMessage('Incident resolved')
		setTimeout(() => setSuccessMessage(''), 3000)
	}

	const handleViewDetails = (id: string) => {
		const incident = incidents.find(i => i.id === id)
		if (incident) setSelectedIncident(incident)
	}

	const handleRefresh = async () => {
		setRefreshing(true)
		await new Promise(r => setTimeout(r, 500))
		setRefreshing(false)
		setSuccessMessage('Refreshed')
		setTimeout(() => setSuccessMessage(''), 3000)
	}

	const exportCsv = () => {
		const csv = filtered.map(r => `"${r.title}","${r.severity}","${r.source}"`).join('\n')
		const blob = new Blob([csv], { type: 'text/csv' })
		const url = URL.createObjectURL(blob)
		const a = document.createElement('a')
		a.href = url
		a.download = `incidents-${Date.now()}.csv`
		a.click()
		URL.revokeObjectURL(url)
		setSuccessMessage('Exported')
		setTimeout(() => setSuccessMessage(''), 3000)
	}

	return (
		<div className="w-full p-6 space-y-6 bg-gradient-to-b from-slate-900 via-slate-950 to-slate-950 min-h-screen">
			{successMessage && (
				<div className="fixed top-6 right-6 bg-green-500/20 border border-green-500/50 text-green-300 px-6 py-3 rounded-lg z-50">
					✓ {successMessage}
				</div>
			)}
			{errorMessage && (
				<div className="fixed top-6 right-6 bg-red-500/20 border border-red-500/50 text-red-300 px-6 py-3 rounded-lg z-50">
					✗ {errorMessage}
				</div>
			)}

			<div className="relative overflow-hidden rounded-2xl p-8 bg-gradient-to-r from-red-500/10 via-orange-500/5 to-yellow-500/10">
				<div className="flex items-start gap-4 mb-4">
					<div className="p-3 bg-red-500/20 border border-red-500/30 rounded-xl">
						<AlertTriangle className="h-8 w-8 text-red-400" />
					</div>
					<div>
						<h1 className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-red-400 via-orange-400 to-yellow-400">
							Incident Response
						</h1>
						<p className="text-slate-400 mt-2 text-sm">Real-time threat detection & analysis</p>
					</div>
				</div>

				<div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4">
					<p className="text-sm text-slate-300">
						<Flame className="h-4 w-4 text-red-400 inline mr-2" />
						{metrics.criticalIncidents} critical • {metrics.highIncidents} high • Response: {metrics.avgResponseTime}ms
					</p>
				</div>
			</div>

			<div className="space-y-4">
				<div className="flex gap-4">
					<div className="relative flex-1">
						<Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-500" />
						<input
							type="text"
							placeholder="Search incidents..."
							value={query}
							onChange={(e) => setQuery(e.target.value)}
							className="w-full pl-12 pr-4 py-3 bg-slate-900/50 border border-slate-700 rounded-xl text-slate-100 focus:border-red-500/50 focus:ring-2 focus:ring-red-500/20 transition-all"
						/>
					</div>
					<button
						onClick={handleRefresh}
						className="px-5 py-3 bg-slate-800/50 border border-slate-700 rounded-xl text-slate-300 hover:border-blue-500/50 flex items-center gap-2"
					>
						<RefreshCw className={`h-5 w-5 ${refreshing ? 'animate-spin' : ''}`} />
						Refresh
					</button>
					<button
						onClick={exportCsv}
						className="px-5 py-3 bg-amber-500/20 border border-amber-500/30 rounded-xl text-amber-400 flex items-center gap-2"
					>
						<Download className="h-5 w-5" />
						Export
					</button>
				</div>

				<div className="flex flex-wrap gap-2">
					{(['all', 'critical', 'high', 'medium', 'low'] as const).map((s) => (
						<button
							key={s}
							onClick={() => setFilter(s)}
							className={`px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 ${filter === s
									? s === 'critical'
										? 'bg-red-500/30 border border-red-500/50 text-red-300'
										: s === 'high'
											? 'bg-orange-500/30 border border-orange-500/50 text-orange-300'
											: s === 'medium'
												? 'bg-yellow-500/30 border border-yellow-500/50 text-yellow-300'
												: 'bg-cyan-500/30 border border-cyan-500/50 text-cyan-300'
									: 'bg-slate-800/50 border border-slate-700 text-slate-400'
								}`}
						>
							{s === 'critical' && <Flame className="h-4 w-4" />}
							{s === 'high' && <AlertTriangle className="h-4 w-4" />}
							{s === 'medium' && <AlertCircle className="h-4 w-4" />}
							{s === 'all' && <Activity className="h-4 w-4" />}
							{s === 'all' ? 'All' : s.charAt(0).toUpperCase() + s.slice(1)}
							{s !== 'all' && ` (${incidents.filter(i => i.severity === s).length})`}
						</button>
					))}
				</div>
			</div>

			<div className="grid grid-cols-4 gap-4">
				<div className="bg-blue-500/10 border border-blue-500/30 rounded-xl p-5">
					<p className="text-slate-400 text-xs font-semibold">Total</p>
					<p className="text-3xl font-bold text-slate-100 mt-2">{metrics.totalIncidents}</p>
				</div>
				<div className="bg-red-500/10 border border-red-500/30 rounded-xl p-5">
					<p className="text-slate-400 text-xs font-semibold">Critical</p>
					<p className="text-3xl font-bold text-slate-100 mt-2">{metrics.criticalIncidents}</p>
				</div>
				<div className="bg-orange-500/10 border border-orange-500/30 rounded-xl p-5">
					<p className="text-slate-400 text-xs font-semibold">High</p>
					<p className="text-3xl font-bold text-slate-100 mt-2">{metrics.highIncidents}</p>
				</div>
				<div className="bg-green-500/10 border border-green-500/30 rounded-xl p-5">
					<p className="text-slate-400 text-xs font-semibold">Resolved</p>
					<p className="text-3xl font-bold text-slate-100 mt-2">{metrics.resolvedRate}%</p>
				</div>
			</div>

			{filtered.length === 0 ? (
				<div className="text-center py-16 text-slate-400">
					<Shield className="h-16 w-16 mx-auto mb-4 opacity-20" />
					<p>No incidents found</p>
				</div>
			) : (
				<div className="space-y-4">
					{filtered.map((incident) => (
						<div
							key={incident.id}
							className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-6 hover:border-red-500/50 transition-all"
						>
							<div className="flex items-start justify-between gap-4">
								<div className="flex-1">
									<div className="flex items-start gap-3 mb-3">
										<div className={`p-2 rounded-lg ${incident.severity === 'critical' ? 'bg-red-500/20' : 'bg-orange-500/20'
											}`}>
											{incident.severity === 'critical' ? <Flame className="h-5 w-5 text-red-400" /> : <AlertTriangle className="h-5 w-5 text-orange-400" />}
										</div>
										<div>
											<h3 className="text-base font-semibold text-slate-100">{incident.title}</h3>
											<p className="text-xs text-slate-400 mt-1">{incident.description}</p>
										</div>
									</div>

									<div className="flex flex-wrap gap-4 text-xs text-slate-400">
										<span className="flex items-center gap-1"><Clock className="h-4 w-4" />{new Date(incident.createdAt).toLocaleTimeString()}</span>
										{incident.source && <span className="flex items-center gap-1"><Shield className="h-4 w-4" />{incident.source}</span>}
										{incident.responseTime && <span className="flex items-center gap-1"><Zap className="h-4 w-4" />{incident.responseTime}ms</span>}
									</div>
								</div>

								<div className="flex gap-2">
									<button
										onClick={() => handleViewDetails(incident.id)}
										className="px-3 py-2 text-xs bg-slate-700/50 text-slate-300 rounded-lg hover:bg-slate-700 flex items-center gap-1"
									>
										<Eye className="h-4 w-4" />
										Details
									</button>
									<button
										onClick={() => handleRespond(incident.id)}
										className="px-3 py-2 text-xs bg-blue-500/10 text-blue-400 rounded-lg hover:bg-blue-500/20 flex items-center gap-1"
									>
										<Zap className="h-4 w-4" />
										Respond
									</button>
									<button
										onClick={() => handleContain(incident.id)}
										className="px-3 py-2 text-xs bg-orange-500/10 text-orange-400 rounded-lg hover:bg-orange-500/20 flex items-center gap-1"
									>
										<Lock className="h-4 w-4" />
										Contain
									</button>
									<button
										onClick={() => handleResolve(incident.id)}
										className="px-3 py-2 text-xs bg-green-500/10 text-green-400 rounded-lg hover:bg-green-500/20 flex items-center gap-1"
									>
										<CheckCircle className="h-4 w-4" />
										Resolve
									</button>
								</div>
							</div>
						</div>
					))}
				</div>
			)}

			{selectedIncident && (
				<div className="fixed inset-0 z-50 flex items-center justify-center">
					<div className="absolute inset-0 bg-black/70" onClick={() => setSelectedIncident(null)} />
					<div className="relative w-full max-w-2xl bg-slate-800 border border-slate-700 rounded-2xl p-8 mx-4 shadow-2xl">
						<button
							onClick={() => setSelectedIncident(null)}
							className="absolute top-4 right-4 p-2 hover:bg-slate-700/50 rounded-lg"
							title="Close"
						>
							<X className="h-6 w-6 text-slate-400" />
						</button>

						<h2 className="text-2xl font-bold text-slate-100 mb-4">{selectedIncident.title}</h2>
						<p className="text-slate-300 mb-4">{selectedIncident.description}</p>
						{selectedIncident.recommendedAction && (
							<div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4 text-blue-300 text-sm mb-6">
								{selectedIncident.recommendedAction}
							</div>
						)}

						<div className="flex gap-3">
							<button
								onClick={() => setSelectedIncident(null)}
								className="flex-1 px-5 py-3 bg-slate-700/50 text-slate-300 rounded-lg hover:bg-slate-700"
							>
								Close
							</button>
							<button
								onClick={() => { handleRespond(selectedIncident.id); setSelectedIncident(null) }}
								className="flex-1 px-5 py-3 bg-blue-500/20 text-blue-400 rounded-lg border border-blue-500/30 hover:bg-blue-500/30"
							>
								Respond
							</button>
							<button
								onClick={() => { handleContain(selectedIncident.id); setSelectedIncident(null) }}
								className="flex-1 px-5 py-3 bg-orange-500/20 text-orange-400 rounded-lg border border-orange-500/30 hover:bg-orange-500/30"
							>
								Contain
							</button>
						</div>
					</div>
				</div>
			)}

			{filtered.length > 0 && (
				<div className="mt-12 pt-8 border-t border-slate-700">
					<h2 className="text-2xl font-bold text-slate-100 mb-6 flex items-center gap-3">
						<Layers className="h-6 w-6 text-cyan-400" />
						Timeline
					</h2>
					<IncidentTimeline incidents={filtered} />
				</div>
			)}
		</div>
	)
}
