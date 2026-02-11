import { Download } from 'lucide-react'

const ReportPreviewModal = ({ reportId, onClose }: { reportId: string | null; onClose: () => void }) => {
  if (!reportId) return null

  return (
    <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center z-50 rounded-lg">
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-8 max-w-2xl w-full mx-4 max-h-96 overflow-y-auto">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-xl font-semibold text-slate-100">📄 Report Preview</h3>
          <button onClick={onClose} className="text-2xl text-slate-400 hover:text-slate-200 font-bold">
            ×
          </button>
        </div>
        <div className="space-y-4 text-slate-300 text-sm">
          <p>
            <strong>Report ID:</strong> {reportId}
          </p>
          <p>
            <strong>Status:</strong> <span className="text-emerald-400">✓ Ready</span>
          </p>
          <p>
            <strong>Generated:</strong> {new Date().toLocaleString()}
          </p>
          <div className="bg-slate-700/30 rounded p-4 max-h-48 overflow-y-auto">
            <p className="text-xs text-slate-400 mb-2">Preview Content:</p>
            <p className="text-xs leading-relaxed">This report contains detailed forensics analysis including incident timeline, affected assets, digital evidence chain, cryptographic verification, and remediation recommendations...</p>
          </div>
          <div className="flex gap-3 pt-4">
            <button
              onClick={onClose}
              className="flex-1 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-200 rounded-lg font-medium transition-colors"
            >
              Close
            </button>
            <button className="flex-1 px-4 py-2 bg-cyan-600 hover:bg-cyan-700 text-white rounded-lg font-medium transition-colors flex items-center justify-center gap-2">
              <Download className="w-4 h-4" />
              Download Full Report
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ReportPreviewModal
