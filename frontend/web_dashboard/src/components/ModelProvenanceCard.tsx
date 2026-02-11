import React, { useState } from 'react';
import {
  ChevronDown,
  ChevronUp,
  GitBranch,
  Check,
  X,
  AlertTriangle,
  Zap,
  Shield,
  Copy,
} from 'lucide-react';
import { ModelProvenanceCard, ModelHashVerification } from '../types/xdr.types';

interface ModelProvenanceProps {
  model: ModelProvenanceCard;
  verification?: ModelHashVerification;
  onHashVerify?: (modelId: string) => void;
  isExpanded?: boolean;
  onToggleExpand?: () => void;
}

/**
 * ModelProvenanceCard - Model training history and hash verification
 * Shows model lineage, parent relationships, hash verification, and audit trail
 */
const ModelProvenance: React.FC<ModelProvenanceProps> = ({
  model,
  verification,
  onHashVerify = () => {},
  isExpanded = false,
  onToggleExpand = () => {},
}) => {
  const [copiedHash, setCopiedHash] = useState<string | null>(null);

  // Get status color
  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'training':
        return 'bg-blue-900 text-blue-200';
      case 'validation':
        return 'bg-purple-900 text-purple-200';
      case 'deployed':
        return 'bg-green-900 text-green-200';
      case 'archived':
        return 'bg-gray-700 text-gray-200';
      case 'failed':
        return 'bg-red-900 text-red-200';
      default:
        return 'bg-gray-700 text-gray-200';
    }
  };

  // Format number with commas
  const formatNumber = (num: number): string => {
    return num.toLocaleString();
  };

  // Copy to clipboard
  const copyToClipboard = (text: string, field: string) => {
    navigator.clipboard.writeText(text);
    setCopiedHash(field);
    setTimeout(() => setCopiedHash(null), 2000);
  };

  // Format training duration
  const formatDuration = (seconds: number): string => {
    if (seconds < 60) return `${seconds}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
    return `${Math.floor(seconds / 3600)}h`;
  };

  // Format byte size
  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
  };

  return (
    <div className="w-full bg-gray-900 rounded-lg border border-gray-700 p-4 space-y-3">
      {/* Header */}
      <button
        onClick={onToggleExpand}
        className="w-full text-left p-3 bg-gray-800 hover:bg-gray-750 rounded border border-gray-700 transition"
      >
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <span className={`px-2 py-1 rounded text-xs font-semibold ${getStatusColor(model.status)}`}>
                {model.status.replace(/_/g, ' ')}
              </span>
              <span className="px-2 py-1 rounded text-xs font-semibold bg-indigo-900 text-indigo-200">
                {model.framework}
              </span>
            </div>

            <div className="flex items-center gap-3 mb-2">
              <h3 className="text-sm font-bold text-white">{model.modelName}</h3>
              <span className="text-xs text-gray-400">v{model.version}</span>
              <span className="text-xs text-gray-500">Owner: {model.ownerName}</span>
            </div>

            <div className="text-xs text-gray-300 line-clamp-2">{model.description}</div>
          </div>

          <div className="text-right">
            <div className="text-xs text-gray-400 mb-2">
              <div>Accuracy: {(model.performance.accuracy * 100).toFixed(1)}%</div>
              <div>F1: {model.performance.f1Score.toFixed(3)}</div>
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
        <div className="space-y-3 p-3 bg-gray-800 rounded border border-gray-700">
          {/* Basic Info */}
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div>
              <span className="text-gray-500">Model ID:</span>
              <div className="font-mono text-gray-300 break-all">{model.modelId}</div>
            </div>
            <div>
              <span className="text-gray-500">Purpose:</span>
              <div className="text-gray-300">{model.purpose}</div>
            </div>
            <div>
              <span className="text-gray-500">Training Duration:</span>
              <div className="text-gray-300">{formatDuration(model.trainingDuration)}</div>
            </div>
            <div>
              <span className="text-gray-500">Model Size:</span>
              <div className="text-gray-300">{formatBytes(model.modelSize)}</div>
            </div>
          </div>

          {/* Hash Verification */}
          <div className="p-2 bg-gray-900 rounded border border-gray-700">
            <div className="flex items-center justify-between mb-2">
              <div className="font-semibold text-white flex items-center gap-2">
                <Shield className="w-4 h-4" />
                Model Hash Verification
              </div>
              <button
                onClick={() => onHashVerify(model.modelId)}
                className="text-xs px-2 py-1 bg-blue-900 hover:bg-blue-800 rounded text-blue-200 transition"
              >
                Verify
              </button>
            </div>

            <div className="space-y-2 text-xs">
              <div className="flex items-center gap-2">
                <span className="text-gray-500 flex-shrink-0">Original Hash:</span>
                <code className="font-mono text-gray-300 break-all flex-1 bg-gray-950 px-2 py-1 rounded">
                  {model.modelHash.hashValue.substring(0, 40)}...
                </code>
                <button
                  onClick={() => copyToClipboard(model.modelHash.hashValue, 'original')}
                  className="p-1 hover:bg-gray-700 rounded transition"
                  title="Copy hash"
                >
                  {copiedHash === 'original' ? (
                    <Check className="w-3 h-3 text-green-500" />
                  ) : (
                    <Copy className="w-3 h-3 text-gray-400" />
                  )}
                </button>
              </div>

              {verification && (
                <div className="border-t border-gray-700 pt-2 mt-2">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-gray-500">Verification Status:</span>
                    {verification.verified ? (
                      <div className="flex items-center gap-1 text-green-400">
                        <Check className="w-3 h-3" />
                        Verified
                      </div>
                    ) : (
                      <div className="flex items-center gap-1 text-red-400">
                        <X className="w-3 h-3" />
                        Mismatch
                      </div>
                    )}
                  </div>
                  <div className="text-gray-400 text-xs">
                    Score: {(verification.verificationScore * 100).toFixed(1)}% | Last verified:{' '}
                    {new Date(verification.lastVerified).toLocaleDateString()}
                  </div>

                  {verification.issues.length > 0 && (
                    <div className="mt-2 p-1 bg-red-950 rounded border border-red-800">
                      {verification.issues.map((issue, idx) => (
                        <div key={idx} className="text-red-400 text-xs flex gap-2">
                          <AlertTriangle className="w-3 h-3 flex-shrink-0 mt-0.5" />
                          <span>{issue}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Model Lineage */}
          {(model.parentModelId || model.childModelIds.length > 0) && (
            <div className="p-2 bg-gray-900 rounded border border-gray-700">
              <div className="font-semibold text-white flex items-center gap-2 mb-2">
                <GitBranch className="w-4 h-4" />
                Model Lineage
              </div>

              <div className="space-y-2 text-xs">
                {model.parentModelId && (
                  <div className="flex items-center gap-2 text-gray-400">
                    <div className="text-gray-600">Parent:</div>
                    <code className="font-mono bg-gray-950 px-2 py-1 rounded text-gray-300">
                      {model.parentModelId.substring(0, 20)}...
                    </code>
                  </div>
                )}

                {model.childModelIds.length > 0 && (
                  <div>
                    <div className="text-gray-600 mb-1">Derived Versions ({model.childModelIds.length}):</div>
                    <div className="space-y-1">
                      {model.childModelIds.map((childId) => (
                        <code key={childId} className="font-mono bg-gray-950 px-2 py-1 rounded text-gray-300 block">
                          {childId.substring(0, 25)}...
                        </code>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Performance Metrics */}
          <div className="p-2 bg-gray-900 rounded border border-gray-700">
            <div className="font-semibold text-white flex items-center gap-2 mb-2">
              <Zap className="w-4 h-4" />
              Performance Metrics
            </div>

            <div className="grid grid-cols-3 gap-2 text-xs">
              <div>
                <span className="text-gray-500">Accuracy</span>
                <div className="text-lg font-bold text-green-500">
                  {(model.performance.accuracy * 100).toFixed(1)}%
                </div>
              </div>
              <div>
                <span className="text-gray-500">Precision</span>
                <div className="text-lg font-bold text-blue-500">
                  {(model.performance.precision * 100).toFixed(1)}%
                </div>
              </div>
              <div>
                <span className="text-gray-500">Recall</span>
                <div className="text-lg font-bold text-purple-500">
                  {(model.performance.recall * 100).toFixed(1)}%
                </div>
              </div>
              <div>
                <span className="text-gray-500">F1 Score</span>
                <div className="text-lg font-bold text-orange-500">{model.performance.f1Score.toFixed(3)}</div>
              </div>
              <div>
                <span className="text-gray-500">ROC AUC</span>
                <div className="text-lg font-bold text-indigo-500">{model.performance.rocAuc.toFixed(3)}</div>
              </div>
              <div>
                <span className="text-gray-500">Latency</span>
                <div className="text-lg font-bold text-cyan-500">{model.performance.inferenceLatency}ms</div>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2 text-xs mt-2 border-t border-gray-700 pt-2">
              <div>
                <span className="text-gray-500">Training Loss:</span>
                <div className="text-gray-300">{model.performance.trainingLoss.toFixed(4)}</div>
              </div>
              <div>
                <span className="text-gray-500">Validation Loss:</span>
                <div className="text-gray-300">{model.performance.validationLoss.toFixed(4)}</div>
              </div>
              <div>
                <span className="text-gray-500">Throughput:</span>
                <div className="text-gray-300">{formatNumber(Math.round(model.performance.throughput))} samples/s</div>
              </div>
              <div>
                <span className="text-gray-500">Compute Time:</span>
                <div className="text-gray-300">{formatDuration(model.performance.computeTime)}</div>
              </div>
            </div>
          </div>

          {/* Training Config */}
          <div className="p-2 bg-gray-900 rounded border border-gray-700">
            <div className="font-semibold text-white mb-2">Training Configuration</div>

            <div className="grid grid-cols-2 gap-2 text-xs text-gray-400">
              <div>
                <span className="text-gray-500">Algorithm:</span> {model.trainingConfig.algorithm}
              </div>
              <div>
                <span className="text-gray-500">Epochs:</span> {model.trainingConfig.epochs}
              </div>
              <div>
                <span className="text-gray-500">Batch Size:</span> {model.trainingConfig.batchSize}
              </div>
              <div>
                <span className="text-gray-500">Learning Rate:</span> {model.trainingConfig.learningRate}
              </div>
              <div>
                <span className="text-gray-500">Optimizer:</span> {model.trainingConfig.optimizer}
              </div>
              <div>
                <span className="text-gray-500">Regularization:</span> {model.trainingConfig.regularization}
              </div>
              <div className="col-span-2">
                <span className="text-gray-500">Data Samples:</span> {formatNumber(model.trainingConfig.dataSamples)}
              </div>
            </div>
          </div>

          {/* Contributing Nodes */}
          {model.contributingNodes.length > 0 && (
            <div className="p-2 bg-gray-900 rounded border border-gray-700">
              <div className="font-semibold text-white mb-2 text-xs">Contributing Nodes</div>
              <div className="flex flex-wrap gap-2">
                {model.contributingNodes.map((nodeId) => (
                  <span key={nodeId} className="text-xs px-2 py-1 bg-indigo-900 text-indigo-200 rounded">
                    {nodeId}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Audit Trail */}
          {model.auditTrail.length > 0 && (
            <div className="p-2 bg-gray-900 rounded border border-gray-700">
              <div className="font-semibold text-white mb-2 text-xs">Audit Trail</div>
              <div className="space-y-1 max-h-32 overflow-y-auto">
                {model.auditTrail.map((entry) => (
                  <div key={entry.entryId} className="text-xs text-gray-400 border-l-2 border-gray-700 pl-2">
                    <div className="text-gray-300">
                      <span className="font-semibold">{entry.action}</span> by {entry.actor}
                    </div>
                    <div className="text-gray-500 text-xs">
                      {new Date(entry.timestamp).toLocaleDateString()}
                    </div>
                    <div className="text-gray-600">{entry.details}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ModelProvenance;
