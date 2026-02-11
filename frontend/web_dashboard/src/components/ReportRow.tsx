import { FileText, Download } from 'lucide-react'
import type { ForensicReportSummary } from '../types/forensics.types'

interface ReportRowProps {
  report: ForensicReportSummary
  index: number
  onPreview: (id: string) => void
}

const ReportRow = ({ report, index, onPreview }: ReportRowProps) => {
  const getReportTypeBadge = (name: string) => {
    if (name?.toLowerCase().includes('incident')) return { label: 'Incident', color: 'red', icon: '⚠️' }
    if (name?.toLowerCase().includes('compliance')) return { label: 'Compliance', color: 'blue', icon: '📋' }
    if (name?.toLowerCase().includes('audit')) return { label: 'Audit', color: 'purple', icon: '📝' }
    return { label: 'General', color: 'gray', icon: '📄' }
  }

  const typeBadge = getReportTypeBadge((report.title || report.reportId) as string)

  const getSeverityBgColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'bg-red-500/20 text-red-400 border-red-500/30'
      case 'high':
        return 'bg-orange-500/20 text-orange-400 border-orange-500/30'
      default:
        return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
    }
  }

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-lg p-4 hover:border-cyan-500/50 transition-all hover:shadow-lg hover:shadow-cyan-500/10">
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-lg">{typeBadge.icon}</span>
            <h4 className="font-semibold text-slate-100">{report.title || `Report-${index}`}</h4>
            <span
              className={`px-2 py-1 text-xs font-semibold rounded border ${
                typeBadge.color === 'red'
                  ? 'bg-red-500/20 text-red-400 border-red-500/30'
                  : typeBadge.color === 'blue'
                    ? 'bg-blue-500/20 text-blue-400 border-blue-500/30'
                    : typeBadge.color === 'purple'
                      ? 'bg-purple-500/20 text-purple-400 border-purple-500/30'
                      : 'bg-slate-600/20 text-slate-400 border-slate-500/30'
              }`}
            >
              {typeBadge.label}
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            📅 Created: {report.generatedAt ? new Date(report.generatedAt as string).toLocaleDateString() : 'N/A'}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className={`px-2 py-1 text-xs font-semibold rounded border ${getSeverityBgColor(report.severity)}`}>
            {(report.severity as string)?.toUpperCase() || 'PENDING'}
          </span>
          <button
            onClick={() => onPreview(report.id || index.toString())}
            className="p-2 hover:bg-slate-700 rounded transition-colors text-slate-400 hover:text-slate-200"
            title="Preview report"
          >
            <FileText className="w-4 h-4" />
          </button>
          <button
            className="p-2 hover:bg-slate-700 rounded transition-colors text-slate-400 hover:text-emerald-400"
            title="Download report"
          >
            <Download className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  )
}

export default ReportRow
