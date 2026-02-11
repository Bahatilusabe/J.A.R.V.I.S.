/**
 * EvidenceBrowser
 *
 * Advanced evidence/artifact browser for forensics analysis.
 * Displays collected evidence with:
 * - Cryptographic hash verification
 * - Chain of custody tracking
 * - Evidence type categorization
 * - File size indicators
 * - Source tracking and collection timestamps
 *
 * Features:
 * - Sortable columns
 * - Evidence preview
 * - Hash verification status
 * - Bulk operations support
 */

import React, { useState, useMemo } from 'react'
import type { EvidenceItem } from '../types/forensics.types'

interface EvidenceBrowserProps {
  evidence: EvidenceItem[]
  onSelectEvidence?: (evidence: EvidenceItem) => void
  onExport?: (evidence: EvidenceItem[]) => void
  showChainOfCustody?: boolean
}

export const EvidenceBrowser: React.FC<EvidenceBrowserProps> = ({
  evidence,
  onSelectEvidence,
  onExport,
  showChainOfCustody = true,
}) => {
  const [selectedEvidence, setSelectedEvidence] = useState<Set<string>>(new Set())
  const [sortField, setSortField] = useState<keyof EvidenceItem>('collectedAt')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')
  const [expandedEvidenceId, setExpandedEvidenceId] = useState<string | null>(null)
  const [hoveredRow, setHoveredRow] = useState<string | null>(null)

  // Sort evidence
  const sortedEvidence = useMemo(() => {
    const sorted = [...evidence].sort((a, b) => {
      let aVal = a[sortField]
      let bVal = b[sortField]

      if (typeof aVal === 'string') aVal = aVal.toLowerCase()
      if (typeof bVal === 'string') bVal = bVal.toLowerCase()

      if (aVal < bVal) return sortOrder === 'asc' ? -1 : 1
      if (aVal > bVal) return sortOrder === 'asc' ? 1 : -1
      return 0
    })
    return sorted
  }, [evidence, sortField, sortOrder])

  const handleSort = (field: keyof EvidenceItem) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortOrder('asc')
    }
  }

  const toggleEvidenceSelection = (evidenceId: string) => {
    const newSelected = new Set(selectedEvidence)
    if (newSelected.has(evidenceId)) {
      newSelected.delete(evidenceId)
    } else {
      newSelected.add(evidenceId)
    }
    setSelectedEvidence(newSelected)
  }

  const handleSelectAll = () => {
    if (selectedEvidence.size === sortedEvidence.length) {
      setSelectedEvidence(new Set())
    } else {
      setSelectedEvidence(new Set(sortedEvidence.map((e) => e.id)))
    }
  }

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`
  }

  const getTypeColor = (type: string): string => {
    const colors: Record<string, string> = {
      log: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
      trace: 'bg-purple-500/20 text-purple-300 border-purple-500/30',
      snapshot: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30',
      configuration: 'bg-green-500/20 text-green-300 border-green-500/30',
      traffic: 'bg-indigo-500/20 text-indigo-300 border-indigo-500/30',
      other: 'bg-slate-500/20 text-slate-300 border-slate-500/30',
    }
    return colors[type] || colors.other
  }

  const getHashStatus = (verified: boolean): { icon: string; text: string; color: string } => {
    if (verified) {
      return { icon: '✓', text: 'Verified', color: 'text-emerald-400' }
    } else {
      return { icon: '?', text: 'Unverified', color: 'text-slate-400' }
    }
  }

  if (evidence.length === 0) {
    return (
      <div className="flex items-center justify-center h-32 text-slate-400">
        <p className="text-sm">No evidence artifacts available</p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {/* Toolbar */}
      <div className="flex items-center justify-between bg-slate-800/30 border border-slate-700 rounded-lg p-3">
        <div className="flex items-center gap-3">
          <input
            type="checkbox"
            title="Select all evidence artifacts"
            checked={selectedEvidence.size === sortedEvidence.length && sortedEvidence.length > 0}
            onChange={handleSelectAll}
            className="w-4 h-4 rounded border-slate-600 text-cyan-500 cursor-pointer"
            aria-label="Select all evidence artifacts"
          />
          <span className="text-xs text-slate-400 font-medium">
            {selectedEvidence.size > 0 ? `${selectedEvidence.size} selected` : `${sortedEvidence.length} artifacts`}
          </span>
        </div>
        {selectedEvidence.size > 0 && onExport && (
          <button
            onClick={() => {
              const selected = sortedEvidence.filter((e) => selectedEvidence.has(e.id))
              onExport(selected)
            }}
            className="px-3 py-1.5 text-xs bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 border border-cyan-500/50 rounded transition-colors"
          >
            Export ({selectedEvidence.size})
          </button>
        )}
      </div>

      {/* Evidence table */}
      <div className="border border-slate-700 rounded-lg overflow-hidden bg-slate-900/20 backdrop-blur-sm">
        {/* Header */}
        <div className="grid grid-cols-12 gap-4 bg-slate-800/50 border-b border-slate-700 px-4 py-3 text-xs font-semibold text-slate-400 sticky top-0">
          <div className="col-span-1 flex items-center justify-center">
            <input
              type="checkbox"
              title="Select all evidence items"
              checked={selectedEvidence.size === sortedEvidence.length && sortedEvidence.length > 0}
              onChange={handleSelectAll}
              className="w-4 h-4 rounded border-slate-600 text-cyan-500 cursor-pointer"
              aria-label="Select all evidence items"
            />
          </div>
          <div
            className="col-span-2 cursor-pointer hover:text-slate-300 flex items-center gap-1"
            onClick={() => handleSort('type')}
          >
            Type {sortField === 'type' && <span>{sortOrder === 'asc' ? '↑' : '↓'}</span>}
          </div>
          <div
            className="col-span-2 cursor-pointer hover:text-slate-300 flex items-center gap-1"
            onClick={() => handleSort('source')}
          >
            Source {sortField === 'source' && <span>{sortOrder === 'asc' ? '↑' : '↓'}</span>}
          </div>
          <div
            className="col-span-2 cursor-pointer hover:text-slate-300 flex items-center gap-1"
            onClick={() => handleSort('size')}
          >
            Size {sortField === 'size' && <span>{sortOrder === 'asc' ? '↑' : '↓'}</span>}
          </div>
          <div
            className="col-span-2 cursor-pointer hover:text-slate-300 flex items-center gap-1"
            onClick={() => handleSort('collectedAt')}
          >
            Collected {sortField === 'collectedAt' && <span>{sortOrder === 'asc' ? '↑' : '↓'}</span>}
          </div>
          <div className="col-span-2 flex items-center gap-1">Hash Status</div>
          <div className="col-span-1"></div>
        </div>

        {/* Rows */}
        <div className="divide-y divide-slate-700/50">
          {sortedEvidence.map((item) => {
            const isSelected = selectedEvidence.has(item.id)
            const isExpanded = expandedEvidenceId === item.id
            const isHovered = hoveredRow === item.id
            const hashStatus = getHashStatus(item.integrityVerified)

            return (
              <div key={item.id}>
                {/* Main row */}
                <div
                  className={`grid grid-cols-12 gap-4 px-4 py-3 text-sm transition-colors ${
                    isHovered ? 'bg-slate-800/30' : ''
                  } border-b border-slate-700/30 last:border-b-0 cursor-pointer`}
                  onMouseEnter={() => setHoveredRow(item.id)}
                  onMouseLeave={() => setHoveredRow(null)}
                  onClick={() => {
                    setExpandedEvidenceId(isExpanded ? null : item.id)
                    onSelectEvidence?.(item)
                  }}
                >
                  <div className="col-span-1 flex items-center justify-center">
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => toggleEvidenceSelection(item.id)}
                      onClick={(e) => e.stopPropagation()}
                      className="w-4 h-4 rounded border-slate-600 text-cyan-500 cursor-pointer"
                    />
                  </div>

                  {/* Type */}
                  <div className="col-span-2">
                    <span className={`inline-block px-2 py-1 text-xs font-semibold rounded border ${getTypeColor(item.type)}`}>
                      {item.type}
                    </span>
                  </div>

                  {/* Source */}
                  <div className="col-span-2 text-slate-300 truncate" title={item.source}>
                    {item.source}
                  </div>

                  {/* Size */}
                  <div className="col-span-2 text-slate-300">{formatFileSize(item.size)}</div>

                  {/* Collected At */}
                  <div className="col-span-2 text-slate-400 text-xs">
                    {new Date(item.collectedAt).toLocaleString('en-US', {
                      month: 'short',
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </div>

                  {/* Hash Status */}
                  <div className={`col-span-2 flex items-center gap-1 text-xs font-medium ${hashStatus.color}`}>
                    <span>{hashStatus.icon}</span>
                    <span>{hashStatus.text}</span>
                  </div>

                  {/* Expand indicator */}
                  <div className="col-span-1 flex items-center justify-end text-slate-500">
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

                {/* Expanded details */}
                {isExpanded && (
                  <div className="bg-slate-800/50 border-b border-slate-700/50 px-4 py-4 space-y-3">
                    {/* Hash information */}
                    <div>
                      <h5 className="text-xs font-semibold text-slate-400 mb-2">Cryptographic Hash</h5>
                      <div className="bg-slate-900/50 border border-slate-700/30 rounded p-3 font-mono text-xs text-slate-400 break-all">
                        <p className="text-slate-500 mb-1">{item.hashAlgorithm}:</p>
                        <p>{item.hash}</p>
                      </div>
                    </div>

                    {/* Chain of custody */}
                    {showChainOfCustody && item.chainOfCustodyLog && item.chainOfCustodyLog.length > 0 && (
                      <div>
                        <h5 className="text-xs font-semibold text-slate-400 mb-2">
                          Chain of Custody ({item.chainOfCustodyLog.length})
                        </h5>
                        <div className="space-y-1">
                          {item.chainOfCustodyLog.map((entry, i) => (
                            <div
                              key={i}
                              className="bg-slate-900/30 border border-slate-700/20 rounded px-2 py-1 text-xs text-slate-400"
                            >
                              {i + 1}. {entry}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Evidence ID */}
                    <div>
                      <h5 className="text-xs font-semibold text-slate-400 mb-1">Evidence ID</h5>
                      <p className="text-xs font-mono text-slate-500 bg-slate-900/30 rounded px-2 py-1">{item.id}</p>
                    </div>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

export default EvidenceBrowser
