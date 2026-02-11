/**
 * Advanced Forensics Report List Component
 * Cutting-edge forensics dashboard with multi-view analysis interface
 */

import React, { useState, useMemo } from 'react'
import type {
  ForensicReportSummary,
  IncidentSeverity,
  IncidentStatus,
  ForensicReportFilter,
  ForensicReport,
} from '../types/forensics.types'

// ============================================================================
// TYPES
// ============================================================================

type ViewMode = 'timeline' | 'evidence' | 'findings' | 'verification' | 'list'

interface ForensicReportListProps {
  reports: ForensicReportSummary[]
  isLoading?: boolean
  onSelectReport: (reportId: string) => void
  onDownloadReport?: (reportId: string) => void
  onFilter?: (filter: ForensicReportFilter) => void
}

// ============================================================================
// STYLING HELPERS
// ============================================================================

const getSeverityClass = (severity: IncidentSeverity): string => {
  const map: Record<IncidentSeverity, string> = {
    low: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
    medium: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
    high: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
    critical: 'bg-red-500/20 text-red-400 border-red-500/30',
    catastrophic: 'bg-pink-500/20 text-pink-300 border-pink-500/30',
  }
  return map[severity]
}

const getSeverityLabel = (severity: IncidentSeverity): string => {
  const labels: Record<IncidentSeverity, string> = {
    low: 'Low',
    medium: 'Medium',
    high: 'High',
    critical: 'Critical',
    catastrophic: 'Catastrophic',
  }
  return labels[severity]
}

const getStatusClass = (status: IncidentStatus): string => {
  const map: Record<IncidentStatus, string> = {
    detected: 'bg-blue-500/20 text-blue-400',
    investigating: 'bg-amber-500/20 text-amber-400',
    contained: 'bg-violet-500/20 text-violet-400',
    resolved: 'bg-emerald-500/20 text-emerald-400',
    archived: 'bg-slate-700/50 text-slate-300',
  }
  return map[status]
}

const getStatusLabel = (status: IncidentStatus): string => {
  const labels: Record<IncidentStatus, string> = {
    detected: 'Detected',
    investigating: 'Investigating',
    contained: 'Contained',
    resolved: 'Resolved',
    archived: 'Archived',
  }
  return labels[status]
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export const ForensicReportList: React.FC<ForensicReportListProps> = ({
  reports,
  isLoading = false,
}) => {
  const [viewMode, setViewMode] = useState<ViewMode>('list')
  const [searchText, setSearchText] = useState<string>('')
  const [selectedSeverities, setSelectedSeverities] = useState<IncidentSeverity[]>([])
  const [selectedReport, setSelectedReport] = useState<ForensicReportSummary | null>(null)

  // Filter and sort reports
  const filteredAndSortedReports = useMemo(() => {
    let filtered = [...reports]

    if (searchText) {
      const lower = searchText.toLowerCase()
      filtered = filtered.filter(
        (r) =>
          r.id.toLowerCase().includes(lower) ||
          r.title.toLowerCase().includes(lower) ||
          r.generatedBy.toLowerCase().includes(lower)
      )
    }

    if (selectedSeverities.length > 0) {
      filtered = filtered.filter((r) => selectedSeverities.includes(r.severity))
    }

    filtered.sort((a, b) => {
      const aDate = new Date(a.detectedAt).getTime()
      const bDate = new Date(b.detectedAt).getTime()
      return bDate - aDate
    })

    return filtered
  }, [reports, searchText, selectedSeverities])

  // Convert report to forensic data for analysis views
  const reportAsForensicData = useMemo((): ForensicReport | null => {
    if (!selectedReport) return null

    return {
      id: selectedReport.id,
      reportId: selectedReport.id,
      incidentMetadata: {
        id: selectedReport.incidentId,
        incidentId: selectedReport.incidentId,
        createdAt: new Date().toISOString(),
        detectedAt: selectedReport.detectedAt,
        status: selectedReport.status,
        severity: selectedReport.severity,
        affectedSystems: [],
        affectedAgents: 0,
        rootCauseDescription: '',
      },
      executiveSummary: selectedReport.title,
      timelineOfEvents: [],
      findings: [],
      recommendations: [],
      evidenceInventory: [],
      generatedAt: selectedReport.generatedAt,
      generatedBy: selectedReport.generatedBy,
      version: '1.0',
      classification: 'internal',
    }
  }, [selectedReport])

  // Handle report selection
  const handleSelectReportForAnalysis = (report: ForensicReportSummary) => {
    setSelectedReport(report)
    setViewMode('timeline')
  }

  // Render list view
  const renderListView = () => (
    <div className="flex flex-col gap-4 h-full">
      {/* Filters */}
      <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4 space-y-3">
        <input
          type="text"
          placeholder="Search reports..."
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
          className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-slate-200 placeholder-slate-400"
        />

        <div className="flex flex-wrap gap-4">
          <div className="flex gap-2">
            <span className="text-xs text-slate-400 font-semibold pt-1">Severity:</span>
            {(['low', 'medium', 'high', 'critical', 'catastrophic'] as IncidentSeverity[]).map(
              (sev) => (
                <button
                  key={sev}
                  onClick={() =>
                    setSelectedSeverities((prev) =>
                      prev.includes(sev) ? prev.filter((s) => s !== sev) : [...prev, sev]
                    )
                  }
                  className={`text-xs px-2 py-1 rounded border ${
                    selectedSeverities.includes(sev)
                      ? `${getSeverityClass(sev)}`
                      : 'bg-slate-700/30 border-slate-600 text-slate-400'
                  }`}
                >
                  {getSeverityLabel(sev)}
                </button>
              )
            )}
          </div>
        </div>
      </div>

      {/* Reports List */}
      <div className="flex-1 overflow-y-auto space-y-2">
        {isLoading ? (
          <div className="flex items-center justify-center h-full">
            <p className="text-slate-400">Loading forensic reports...</p>
          </div>
        ) : filteredAndSortedReports.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <p className="text-slate-400">No forensic reports found</p>
          </div>
        ) : (
          filteredAndSortedReports.map((report) => (
            <div
              key={report.id}
              onClick={() => handleSelectReportForAnalysis(report)}
              className="bg-slate-800 border border-slate-700 rounded-lg p-3 cursor-pointer hover:border-cyan-500/50 hover:bg-slate-800/80 transition-all"
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold text-slate-100 truncate">{report.title}</p>
                  <p className="text-xs text-slate-400">ID: {report.id}</p>
                </div>
                <div className="flex gap-1 flex-shrink-0">
                  <span className={`text-xs px-2 py-1 rounded border ${getSeverityClass(report.severity)}`}>
                    {getSeverityLabel(report.severity)}
                  </span>
                  <span className={`text-xs px-2 py-1 rounded ${getStatusClass(report.status)}`}>
                    {getStatusLabel(report.status)}
                  </span>
                </div>
              </div>
              <p className="text-xs text-slate-500 mt-1">
                {new Date(report.detectedAt).toLocaleString()}
              </p>
            </div>
          ))
        )}
      </div>
    </div>
  )

  // Render analysis views
  const renderAnalysisView = () => {
    if (!reportAsForensicData || !selectedReport) {
      return (
        <div className="flex items-center justify-center h-full">
          <p className="text-slate-400">Select a report to analyze</p>
        </div>
      )
    }

    return (
      <div className="flex flex-col gap-4 h-full">
        <div className="flex items-center justify-between p-3 bg-slate-800/50 border border-slate-700 rounded-lg">
          <div>
            <h3 className="text-sm font-semibold text-slate-100">{selectedReport.title}</h3>
            <p className="text-xs text-slate-400">Report ID: {selectedReport.id}</p>
          </div>
          <button
            onClick={() => setViewMode('list')}
            className="px-3 py-1 text-xs bg-slate-700 hover:bg-slate-600 text-slate-200 rounded"
          >
            Back to List
          </button>
        </div>

        <div className="flex gap-2">
          {(['timeline', 'evidence', 'findings', 'verification'] as ViewMode[]).map((mode) => (
            mode !== 'list' && (
              <button
                key={mode}
                onClick={() => setViewMode(mode)}
                className={`px-3 py-1 text-xs rounded border ${
                  viewMode === mode
                    ? 'bg-cyan-500/20 border-cyan-500/50 text-cyan-300'
                    : 'bg-slate-700/30 border-slate-600 text-slate-400 hover:bg-slate-700/50'
                }`}
              >
                {mode.charAt(0).toUpperCase() + mode.slice(1)}
              </button>
            )
          ))}
        </div>

        <div className="flex-1 overflow-hidden">
          {viewMode === 'timeline' && (
            <div className="bg-slate-800/30 border border-slate-700 rounded-lg p-4 h-full overflow-y-auto">
              <p className="text-slate-400 text-sm">Timeline visualization would appear here</p>
            </div>
          )}
          {viewMode === 'evidence' && (
            <div className="bg-slate-800/30 border border-slate-700 rounded-lg p-4 h-full overflow-y-auto">
              <p className="text-slate-400 text-sm">Evidence browser would appear here</p>
            </div>
          )}
          {viewMode === 'findings' && (
            <div className="bg-slate-800/30 border border-slate-700 rounded-lg p-4 h-full overflow-y-auto">
              <p className="text-slate-400 text-sm">Findings analysis would appear here</p>
            </div>
          )}
          {viewMode === 'verification' && (
            <div className="bg-slate-800/30 border border-slate-700 rounded-lg p-4 h-full overflow-y-auto">
              <p className="text-slate-400 text-sm">Signature verification would appear here</p>
            </div>
          )}
        </div>
      </div>
    )
  }

  // Main render
  return (
    <div className="h-full flex flex-col bg-gradient-to-br from-slate-900 via-slate-900 to-slate-800 rounded-lg border border-slate-700 overflow-hidden">
      {/* Header */}
      <div className="border-b border-slate-700 bg-slate-900/50 backdrop-blur-sm p-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-slate-100">
              {viewMode === 'list' ? 'Forensic Reports' : 'Advanced Analysis'}
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              {filteredAndSortedReports.length} reports • Cutting-edge forensics dashboard
            </p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setViewMode('list')}
              className={`px-3 py-2 text-xs rounded border transition-colors ${
                viewMode === 'list'
                  ? 'bg-cyan-500/20 border-cyan-500/50 text-cyan-300'
                  : 'bg-slate-700/30 border-slate-600 text-slate-400 hover:bg-slate-700/50'
              }`}
            >
              📋 List
            </button>
            <button
              onClick={() => viewMode !== 'list' && setViewMode('list')}
              className="px-3 py-2 text-xs bg-slate-700 hover:bg-slate-600 text-slate-200 rounded border border-slate-600"
            >
              🔄 Refresh
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden p-4">
        {viewMode === 'list' ? renderListView() : renderAnalysisView()}
      </div>
    </div>
  )
}

export default ForensicReportList
