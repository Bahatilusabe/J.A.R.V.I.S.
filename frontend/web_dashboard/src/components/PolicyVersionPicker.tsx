import React, { useMemo, useState } from 'react';
import { ChevronDown, CheckCircle, Clock, AlertCircle, Archive } from 'lucide-react';
import type { PolicyVersion, PolicyTimeline } from '@/types/self_healing.types';

interface PolicyVersionPickerProps {
  policyTimeline: PolicyTimeline;
  selectedVersion: PolicyVersion | null;
  onVersionSelect: (version: PolicyVersion) => void;
  onCompare: (v1: PolicyVersion, v2: PolicyVersion) => void;
}

export const PolicyVersionPicker: React.FC<PolicyVersionPickerProps> = ({
  policyTimeline,
  selectedVersion,
  onVersionSelect,
  onCompare,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [compareMode, setCompareMode] = useState(false);
  const [compareWith, _setCompareWith] = useState<PolicyVersion | null>(null);

  const getStatusIcon = (status: PolicyVersion['status']) => {
    switch (status) {
      case 'deployed':
        return <CheckCircle className="text-green-600" size={16} />;
      case 'training':
        return <Clock className="text-blue-600" size={16} />;
      case 'validating':
        return <Clock className="text-amber-600" size={16} />;
      case 'archived':
        return <Archive className="text-gray-600" size={16} />;
      case 'failed':
        return <AlertCircle className="text-red-600" size={16} />;
      default:
        return null;
    }
  };

  const getStatusColor = (status: PolicyVersion['status']) => {
    switch (status) {
      case 'deployed':
        return 'bg-green-50 border-green-200 text-green-900';
      case 'training':
        return 'bg-blue-50 border-blue-200 text-blue-900';
      case 'validating':
        return 'bg-amber-50 border-amber-200 text-amber-900';
      case 'archived':
        return 'bg-gray-50 border-gray-200 text-gray-900';
      case 'failed':
        return 'bg-red-50 border-red-200 text-red-900';
      default:
        return 'bg-gray-50 border-gray-200 text-gray-900';
    }
  };

  const handleCompare = (version: PolicyVersion) => {
    if (!selectedVersion) return;
    onCompare(selectedVersion, version);
    setCompareMode(false);
  };

  const comparisonData = useMemo(() => {
    if (!selectedVersion || !compareWith) return null;

    return {
      versionDiff: compareWith.performanceScore - selectedVersion.performanceScore,
      defenseAccuracyDiff:
        (compareWith.accuracyMetrics.defenseAccuracy || 0) -
        (selectedVersion.accuracyMetrics.defenseAccuracy || 0),
      attackDiff:
        (compareWith.accuracyMetrics.attackSuccessRate || 0) -
        (selectedVersion.accuracyMetrics.attackSuccessRate || 0),
      recoveryDiff:
        (compareWith.accuracyMetrics.recoverySuccess || 0) -
        (selectedVersion.accuracyMetrics.recoverySuccess || 0),
    };
  }, [selectedVersion, compareWith]);

  return (
    <div className="flex flex-col gap-4 p-4 bg-white rounded-lg border border-gray-200">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-semibold text-gray-900">Policy Versions</h3>
          <p className="text-xs text-gray-600">
            {policyTimeline.versions.length} versions available
          </p>
        </div>

        <button
          onClick={() => setCompareMode(!compareMode)}
          className="px-3 py-1.5 text-sm font-medium bg-gray-100 text-gray-700 rounded hover:bg-gray-200 transition"
        >
          {compareMode ? 'Cancel Compare' : 'Compare'}
        </button>
      </div>

      {/* Current Version Display */}
      {selectedVersion && (
        <div className={`p-3 rounded border-2 ${getStatusColor(selectedVersion.status)}`}>
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3 flex-1">
              {getStatusIcon(selectedVersion.status)}
              <div>
                <div className="font-semibold">{selectedVersion.semanticVersion}</div>
                <div className="text-xs opacity-75">
                  {selectedVersion.type} • {selectedVersion.status}
                </div>
              </div>
            </div>
            <div className="text-right">
              <div className="text-sm font-semibold">{selectedVersion.performanceScore.toFixed(2)}</div>
              <div className="text-xs opacity-75">score</div>
            </div>
          </div>

          <div className="mt-3 grid grid-cols-3 gap-2 text-xs">
            <div className="bg-white bg-opacity-50 p-2 rounded">
              <div className="opacity-75">Defense</div>
              <div className="font-semibold">
                {((selectedVersion.accuracyMetrics.defenseAccuracy || 0) * 100).toFixed(1)}%
              </div>
            </div>
            <div className="bg-white bg-opacity-50 p-2 rounded">
              <div className="opacity-75">Attack Success</div>
              <div className="font-semibold">
                {((selectedVersion.accuracyMetrics.attackSuccessRate || 0) * 100).toFixed(1)}%
              </div>
            </div>
            <div className="bg-white bg-opacity-50 p-2 rounded">
              <div className="opacity-75">Recovery</div>
              <div className="font-semibold">
                {((selectedVersion.accuracyMetrics.recoverySuccess || 0) * 100).toFixed(1)}%
              </div>
            </div>
          </div>

          <div className="mt-2 text-xs text-gray-600">
            {selectedVersion.trainingEpochs} epochs • Converged:{' '}
            {selectedVersion.convergenceAchieved ? 'Yes' : 'No'}
            {selectedVersion.lastDeployed && (
              <span>
                {' '}
                • Last deployed: {new Date(selectedVersion.lastDeployed).toLocaleDateString()}
              </span>
            )}
          </div>
        </div>
      )}

      {/* Version Dropdown */}
      <div className="relative">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="w-full px-3 py-2 flex items-center justify-between bg-gray-50 border border-gray-300 rounded hover:bg-gray-100 transition"
        >
          <span className="text-sm font-medium text-gray-700">
            {selectedVersion ? 'Switch Version' : 'Select a version'}
          </span>
          <ChevronDown
            size={16}
            className={`text-gray-600 transition ${isOpen ? 'rotate-180' : ''}`}
          />
        </button>

        {isOpen && (
          <div className="absolute top-full mt-2 w-full bg-white border border-gray-200 rounded shadow-lg z-10 max-h-64 overflow-y-auto">
            {policyTimeline.versions.map((version, idx) => (
              <button
                key={idx}
                onClick={() => {
                  if (compareMode && selectedVersion) {
                    handleCompare(version);
                  } else {
                    onVersionSelect(version);
                    setIsOpen(false);
                  }
                }}
                className={`w-full px-4 py-3 text-left border-b last:border-b-0 hover:bg-gray-50 transition ${
                  selectedVersion?.version === version.version ? 'bg-blue-50' : ''
                } ${compareMode && compareWith?.version === version.version ? 'bg-amber-50' : ''}`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {getStatusIcon(version.status)}
                    <div>
                      <div className="text-sm font-semibold text-gray-900">
                        {version.semanticVersion}
                      </div>
                      <div className="text-xs text-gray-600">
                        {version.type} • {version.trainingEpochs} epochs
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-semibold text-gray-900">
                      {version.performanceScore.toFixed(2)}
                    </div>
                    <div className="text-xs text-gray-600">score</div>
                  </div>
                </div>

                {compareMode && (
                  <div className="mt-2 text-xs text-gray-600">
                    {compareWith?.version === version.version && (
                      <span className="inline-block px-2 py-1 bg-amber-100 text-amber-800 rounded">
                        Compare target
                      </span>
                    )}
                  </div>
                )}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Comparison Results */}
      {compareMode && selectedVersion && compareWith && comparisonData && (
        <div className="p-3 bg-amber-50 border border-amber-200 rounded">
          <h4 className="text-sm font-semibold text-amber-900 mb-3">
            {selectedVersion.semanticVersion} vs {compareWith.semanticVersion}
          </h4>

          <div className="space-y-2 text-xs">
            <div className="flex items-center justify-between">
              <span className="text-gray-700">Performance Score</span>
              <div className="flex items-center gap-2">
                <span className="font-semibold">
                  {comparisonData.versionDiff > 0 ? '+' : ''}{comparisonData.versionDiff.toFixed(2)}
                </span>
                <span
                  className={
                    comparisonData.versionDiff > 0 ? 'text-green-600' : 'text-red-600'
                  }
                >
                  ({((comparisonData.versionDiff / selectedVersion.performanceScore) * 100).toFixed(1)}%)
                </span>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-gray-700">Defense Accuracy</span>
              <div className="flex items-center gap-2">
                <span className="font-semibold">
                  {comparisonData.defenseAccuracyDiff > 0 ? '+' : ''}
                  {(comparisonData.defenseAccuracyDiff * 100).toFixed(1)}%
                </span>
                <span
                  className={
                    comparisonData.defenseAccuracyDiff > 0 ? 'text-green-600' : 'text-red-600'
                  }
                >
                  {comparisonData.defenseAccuracyDiff > 0 ? '↑' : '↓'}
                </span>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-gray-700">Attack Success Rate</span>
              <div className="flex items-center gap-2">
                <span className="font-semibold">
                  {comparisonData.attackDiff > 0 ? '+' : ''}
                  {(comparisonData.attackDiff * 100).toFixed(1)}%
                </span>
                <span
                  className={comparisonData.attackDiff < 0 ? 'text-green-600' : 'text-red-600'}
                >
                  {comparisonData.attackDiff < 0 ? '↓' : '↑'}
                </span>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-gray-700">Recovery Success</span>
              <div className="flex items-center gap-2">
                <span className="font-semibold">
                  {comparisonData.recoveryDiff > 0 ? '+' : ''}
                  {(comparisonData.recoveryDiff * 100).toFixed(1)}%
                </span>
                <span
                  className={
                    comparisonData.recoveryDiff > 0 ? 'text-green-600' : 'text-red-600'
                  }
                >
                  {comparisonData.recoveryDiff > 0 ? '↑' : '↓'}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Deployment Timeline */}
      <div className="text-xs text-gray-600">
        <div className="font-semibold text-gray-900 mb-2">Deployment History</div>
        {policyTimeline.deploymentHistory.slice(-3).map((deployment, idx) => (
          <div
            key={idx}
            className="flex items-center justify-between py-1 border-b last:border-b-0"
          >
            <span>{deployment.version}</span>
            <span className="text-gray-500">
              {new Date(deployment.deployedAt).toLocaleDateString()}
            </span>
          </div>
        ))}
      </div>

      {policyTimeline.versions.length === 0 && (
        <div className="text-center py-4 text-gray-500 text-sm">
          No policy versions available yet
        </div>
      )}
    </div>
  );
};
