interface ReportListHeaderProps {
  sortBy: 'date' | 'name' | 'status'
  searchTerm: string
  onSortChange: (sort: 'date' | 'name' | 'status') => void
  onSearchChange: (term: string) => void
}

const ReportListHeader = ({ sortBy, searchTerm, onSortChange, onSearchChange }: ReportListHeaderProps) => {
  return (
    <div className="flex items-center justify-between mb-4">
      <h3 className="text-lg font-semibold text-slate-100">📋 Recent Forensics Reports</h3>
      <div className="flex gap-2">
        <select
          value={sortBy}
          onChange={(e) => onSortChange(e.target.value as 'date' | 'name' | 'status')}
          className="px-3 py-2 bg-slate-800 border border-slate-700 rounded text-sm text-slate-200 focus:outline-none focus:border-cyan-500/50"
          title="Sort by"
        >
          <option value="date">Sort by Date</option>
          <option value="name">Sort by Name</option>
        </select>
        <input
          type="text"
          placeholder="Search reports..."
          title="Search reports"
          value={searchTerm}
          onChange={(e) => onSearchChange(e.target.value)}
          className="px-3 py-2 bg-slate-800 border border-slate-700 rounded text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500/50 w-48"
        />
      </div>
    </div>
  )
}

export default ReportListHeader
