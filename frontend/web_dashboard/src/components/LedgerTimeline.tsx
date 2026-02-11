import React, { useState } from 'react';
import {
  ChevronDown,
  ChevronUp,
  Download,
  Check,
  X,
  AlertTriangle,
  Clock,
  FileText,
  Shield,
  Search,
  Filter,
  Copy,
} from 'lucide-react';
import { BlockchainLedgerEntry, LedgerEntryType } from '../types/xdr.types';

interface LedgerTimelineProps {
  entries: BlockchainLedgerEntry[];
  onForensicsDownload?: (txId: string, forensicsId: string) => void;
  expandedEntryIds?: string[];
  onEntryToggle?: (txId: string) => void;
}

/**
 * LedgerTimeline - Chronological blockchain ledger visualization
 * Shows signed immutable entries with expandable details, forensics, and verification
 */
const LedgerTimeline: React.FC<LedgerTimelineProps> = ({
  entries,
  onForensicsDownload = () => {},
  expandedEntryIds = [],
  onEntryToggle = () => {},
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedEntryType, setSelectedEntryType] = useState<LedgerEntryType | 'all'>('all');
  const [selectedSeverity, setSelectedSeverity] = useState<string>('all');
  const [copiedTxId, setCopiedTxId] = useState<string | null>(null);

  // Filter entries based on search and filters
  const filteredEntries = entries.filter((entry) => {
    const matchesSearch =
      searchQuery === '' ||
      entry.txId.includes(searchQuery) ||
      entry.actor.includes(searchQuery) ||
      entry.target.includes(searchQuery) ||
      entry.description.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesType = selectedEntryType === 'all' || entry.type === selectedEntryType;
    const matchesSeverity = selectedSeverity === 'all' || entry.severity === selectedSeverity;

    return matchesSearch && matchesType && matchesSeverity;
  });

  // Entry type badge color
  const getTypeColor = (type: LedgerEntryType): string => {
    switch (type) {
      case 'containment':
        return 'bg-red-900 text-red-200';
      case 'response':
        return 'bg-orange-900 text-orange-200';
      case 'forensics':
        return 'bg-purple-900 text-purple-200';
      case 'model_update':
        return 'bg-blue-900 text-blue-200';
      case 'audit':
        return 'bg-cyan-900 text-cyan-200';
      case 'threat_report':
        return 'bg-pink-900 text-pink-200';
      case 'training_complete':
        return 'bg-green-900 text-green-200';
      case 'policy_change':
        return 'bg-indigo-900 text-indigo-200';
      case 'attestation':
        return 'bg-emerald-900 text-emerald-200';
      default:
        return 'bg-gray-700 text-gray-200';
    }
  };

  // Severity color
  const getSeverityColor = (severity: string): string => {
    switch (severity) {
      case 'critical':
        return 'text-red-500';
      case 'high':
        return 'text-orange-500';
      case 'medium':
        return 'text-yellow-500';
      case 'low':
        return 'text-blue-500';
      case 'info':
        return 'text-gray-400';
      default:
        return 'text-gray-300';
    }
  };

  // Verification badge
  const getVerificationBadge = (entry: BlockchainLedgerEntry) => {
    if (entry.signature.verificationStatus === 'verified') {
      return (
        <div className="flex items-center gap-1 text-green-400 text-xs">
          <Check className="w-3 h-3" />
          Verified
        </div>
      );
    } else if (entry.signature.verificationStatus === 'unverified') {
      return (
        <div className="flex items-center gap-1 text-yellow-400 text-xs">
          <Clock className="w-3 h-3" />
          Unverified
        </div>
      );
    } else {
      return (
        <div className="flex items-center gap-1 text-red-400 text-xs">
          <X className="w-3 h-3" />
          Invalid
        </div>
      );
    }
  };

  // Format timestamp
  const formatTime = (isoString: string): string => {
    const date = new Date(isoString);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  // Copy to clipboard
  const copyToClipboard = (text: string, txId: string) => {
    navigator.clipboard.writeText(text);
    setCopiedTxId(txId);
    setTimeout(() => setCopiedTxId(null), 2000);
  };

  return (
    <div className="w-full bg-gray-900 rounded-lg border border-gray-700 p-4 space-y-4">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h2 className="text-lg font-bold text-white flex items-center gap-2">
          <FileText className="w-5 h-5 text-cyan-500" />
          Blockchain Ledger Timeline
        </h2>
        <div className="text-sm text-gray-400">
          {filteredEntries.length} / {entries.length} entries
        </div>
      </div>

      {/* Search and Filters */}
      <div className="space-y-3">
        <div className="flex gap-2">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-2.5 w-4 h-4 text-gray-500" />
            <input
              type="text"
              placeholder="Search by tx ID, actor, target..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-gray-800 border border-gray-700 rounded text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
            />
          </div>
          <button
            className="px-3 py-2 bg-gray-800 border border-gray-700 rounded text-gray-300 hover:bg-gray-700 transition flex items-center gap-1"
            title="Filter entries"
          >
            <Filter className="w-4 h-4" />
          </button>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-semibold text-gray-400 mb-1">Entry Type</label>
            <select
              value={selectedEntryType}
              onChange={(e) => setSelectedEntryType(e.target.value as LedgerEntryType | 'all')}
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-sm text-white focus:outline-none focus:border-blue-500"
              title="Filter by entry type"
            >
              <option value="all">All Types</option>
              <option value="containment">Containment</option>
              <option value="response">Response</option>
              <option value="forensics">Forensics</option>
              <option value="model_update">Model Update</option>
              <option value="audit">Audit</option>
              <option value="threat_report">Threat Report</option>
              <option value="training_complete">Training Complete</option>
              <option value="policy_change">Policy Change</option>
              <option value="attestation">Attestation</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-semibold text-gray-400 mb-1">Severity</label>
            <select
              value={selectedSeverity}
              onChange={(e) => setSelectedSeverity(e.target.value)}
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-sm text-white focus:outline-none focus:border-blue-500"
              title="Filter by severity level"
            >
              <option value="all">All Severities</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
              <option value="info">Info</option>
            </select>
          </div>
        </div>
      </div>

      {/* Timeline */}
      <div className="space-y-3 max-h-96 overflow-y-auto">
        {filteredEntries.length === 0 ? (
          <div className="flex items-center justify-center py-8 text-gray-400">
            <AlertTriangle className="w-5 h-5 mr-2" />
            No ledger entries match your filters
          </div>
        ) : (
          filteredEntries.map((entry) => {
            const isExpanded = expandedEntryIds.includes(entry.txId);
            return (
              <div key={entry.txId} className="border-l-2 border-blue-600 pl-4 pb-4">
                {/* Entry Header */}
                <button
                  onClick={() => onEntryToggle(entry.txId)}
                  className="w-full text-left p-3 bg-gray-800 hover:bg-gray-750 rounded border border-gray-700 transition"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span className={`px-2 py-1 rounded text-xs font-semibold ${getTypeColor(entry.type)}`}>
                          {entry.type.replace(/_/g, ' ')}
                        </span>
                        <span className={`text-xs font-bold uppercase ${getSeverityColor(entry.severity)}`}>
                          {entry.severity}
                        </span>
                        {getVerificationBadge(entry)}
                      </div>

                      <div className="text-sm text-white font-mono">
                        TX: {entry.txId} (Block {entry.blockHeight})
                      </div>

                      <div className="text-xs text-gray-400 mt-1 space-y-1">
                        <div>
                          <span className="text-gray-500">Actor:</span> {entry.actor}
                        </div>
                        <div>
                          <span className="text-gray-500">Action:</span> {entry.action} on{' '}
                          <span className="text-orange-400">{entry.target}</span>
                        </div>
                        <div>
                          <span className="text-gray-500">Time:</span> {formatTime(entry.timestamp)}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <div className="text-right">
                        <div className="text-xs text-gray-400">
                          {entry.confirmations} confirmations
                        </div>
                        <div className="text-xs text-gray-500">{entry.status}</div>
                      </div>
                      {isExpanded ? (
                        <ChevronUp className="w-5 h-5 text-blue-500" />
                      ) : (
                        <ChevronDown className="w-5 h-5 text-gray-500" />
                      )}
                    </div>
                  </div>
                </button>

                {/* Expanded Details */}
                {isExpanded && (
                  <div className="mt-2 p-3 bg-gray-800 rounded border border-gray-700 text-xs space-y-2">
                    <div className="text-gray-300">
                      <div className="font-semibold text-white mb-2">Description</div>
                      {entry.description}
                    </div>

                    <div className="grid grid-cols-2 gap-3 text-gray-400">
                      <div>
                        <span className="text-gray-500">Block Hash:</span>
                        <div className="font-mono text-xs mt-1 break-all text-gray-300">
                          {entry.blockHash.substring(0, 32)}...
                        </div>
                      </div>
                      <div>
                        <span className="text-gray-500">Algorithm:</span>
                        <div className="mt-1 text-gray-300">{entry.signature.algorithm}</div>
                      </div>
                    </div>

                    {entry.parentTxId && (
                      <div className="text-gray-400">
                        <span className="text-gray-500">Parent TX:</span>
                        <div className="font-mono text-xs mt-1 text-gray-300">{entry.parentTxId}</div>
                      </div>
                    )}

                    {Object.keys(entry.metadata).length > 0 && (
                      <div>
                        <div className="font-semibold text-white mb-1">Metadata</div>
                        <div className="space-y-1">
                          {Object.entries(entry.metadata).map(([key, value]) => (
                            <div key={key} className="flex justify-between">
                              <span className="text-gray-500">{key}:</span>
                              <span className="text-gray-300">{String(value)}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Signature Details */}
                    <div className="bg-gray-900 p-2 rounded border border-gray-600">
                      <div className="font-semibold text-white mb-2 flex items-center gap-1">
                        <Shield className="w-4 h-4" />
                        Signature
                      </div>
                      <div className="space-y-1 text-gray-400">
                        <div>
                          <span className="text-gray-500">Signature:</span>
                          <div className="font-mono text-xs mt-1 break-all text-gray-300 flex items-center justify-between">
                            <span>{entry.signature.signature.substring(0, 40)}...</span>
                            <button
                              onClick={() => copyToClipboard(entry.signature.signature, entry.txId)}
                              className="p-1 hover:bg-gray-700 rounded"
                              title="Copy signature"
                            >
                              {copiedTxId === entry.txId ? (
                                <Check className="w-3 h-3 text-green-500" />
                              ) : (
                                <Copy className="w-3 h-3" />
                              )}
                            </button>
                          </div>
                        </div>
                        <div className="text-xs">Verified at: {formatTime(entry.signature.timestamp)}</div>
                      </div>
                    </div>

                    {/* Forensics */}
                    {entry.forensicsId && (
                      <button
                        onClick={() => onForensicsDownload(entry.txId, entry.forensicsId!)}
                        className="w-full mt-2 px-3 py-2 bg-blue-900 hover:bg-blue-800 rounded border border-blue-700 text-blue-200 text-xs font-semibold flex items-center justify-center gap-2 transition"
                      >
                        <Download className="w-4 h-4" />
                        Download Forensics Evidence
                      </button>
                    )}

                    {/* Related Entries */}
                    {entry.children.length > 0 && (
                      <div className="text-gray-400">
                        <span className="text-gray-500">Related Entries:</span>
                        <div className="font-mono text-xs mt-1 space-y-1">
                          {entry.children.map((childId) => (
                            <div key={childId} className="text-gray-300">
                              ↓ {childId}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      {/* Footer Stats */}
      <div className="grid grid-cols-4 gap-3 pt-4 border-t border-gray-700 text-xs">
        <div className="bg-gray-800 p-2 rounded">
          <div className="text-gray-400">Total Entries</div>
          <div className="text-lg font-bold text-white">{entries.length}</div>
        </div>
        <div className="bg-gray-800 p-2 rounded">
          <div className="text-gray-400">Critical</div>
          <div className="text-lg font-bold text-red-500">
            {entries.filter((e) => e.severity === 'critical').length}
          </div>
        </div>
        <div className="bg-gray-800 p-2 rounded">
          <div className="text-gray-400">Verified</div>
          <div className="text-lg font-bold text-green-500">
            {entries.filter((e) => e.signature.verificationStatus === 'verified').length}
          </div>
        </div>
        <div className="bg-gray-800 p-2 rounded">
          <div className="text-gray-400">Finalized</div>
          <div className="text-lg font-bold text-blue-500">
            {entries.filter((e) => e.status === 'finalized').length}
          </div>
        </div>
      </div>
    </div>
  );
};

export default LedgerTimeline;
