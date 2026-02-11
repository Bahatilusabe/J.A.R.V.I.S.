import { useState } from 'react'
import type { ForensicReportSummary } from '../types/forensics.types'
import ReportPreviewModal from './ReportPreviewModal'
import ReportRow from './ReportRow'
import ReportListHeader from './ReportListHeader'

const ReportsList = ({ reports, isLoading }: { reports: ForensicReportSummary[]; isLoading: boolean }) => {
  const [searchTerm, setSearchTerm] = useState('')
  const [sortBy, setSortBy] = useState<'date' | 'name' | 'status'>('date')
  const [showPreview, setShowPreview] = useState<string | null>(null)

  const filteredReports = reports
    .filter((r) => (r.title || r.reportId)?.toLowerCase().includes(searchTerm.toLowerCase()))
    .sort((a, b) => {
      if (sortBy === 'date') {
        const dateA = new Date(a.generatedAt as string).getTime()
        const dateB = new Date(b.generatedAt as string).getTime()
        return dateB - dateA
      } else if (sortBy === 'name') {
        return ((a.title as string) || '').localeCompare((b.title as string) || '')
      }
      return 0
    })

  return (
    <div className="space-y-3 p-6">
      <ReportListHeader
        sortBy={sortBy}
        searchTerm={searchTerm}
        onSortChange={setSortBy}
        onSearchChange={setSearchTerm}
      />
      {isLoading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="bg-slate-800 border border-slate-700 rounded-lg p-4 h-24 animate-pulse" />
          ))}
        </div>
      ) : filteredReports.length > 0 ? (
        filteredReports.map((report: ForensicReportSummary, i: number) => (
          <ReportRow key={report.id || i} report={report} index={i} onPreview={setShowPreview} />
        ))
      ) : (
        <div className="text-center py-8 text-slate-400">
          <p>No reports found. Generate one to get started!</p>
        </div>
      )}

      {/* Report Preview Modal */}
      <ReportPreviewModal reportId={showPreview} onClose={() => setShowPreview(null)} />
    </div>
  )
}

export default ReportsList
