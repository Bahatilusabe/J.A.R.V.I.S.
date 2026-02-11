import { useState, useMemo } from 'react';
import { ChevronDown } from 'lucide-react';

export interface TimelineStep {
  step: number;
  actions: Record<string, number>;
  rewards: Record<string, number>;
  infos: Record<string, Record<string, unknown>>;
  ts: string;
}

interface PolicyTimelineViewerProps {
  steps: TimelineStep[];
  onStepClick?: (step: TimelineStep) => void;
}

// Map action IDs to readable labels
const ACTION_LABELS: Record<number, string> = {
  0: 'Defend',
  1: 'Attack',
  2: 'Isolate',
  3: 'Recover',
  4: 'Monitor',
  5: 'Deploy',
};

// Get color for action type
const getActionColor = (actionId: number): string => {
  switch (actionId) {
    case 0:
      return 'bg-blue-900 border-blue-500 text-blue-300';
    case 1:
      return 'bg-red-900 border-red-500 text-red-300';
    case 2:
      return 'bg-purple-900 border-purple-500 text-purple-300';
    case 3:
      return 'bg-green-900 border-green-500 text-green-300';
    case 4:
      return 'bg-yellow-900 border-yellow-500 text-yellow-300';
    case 5:
      return 'bg-indigo-900 border-indigo-500 text-indigo-300';
    default:
      return 'bg-gray-900 border-gray-500 text-gray-300';
  }
};

// Get reward styling based on value
const getRewardStyle = (reward: number): string => {
  if (reward > 0.5) return 'text-green-400';
  if (reward > 0) return 'text-cyan-400';
  if (reward < -0.5) return 'text-red-400';
  return 'text-yellow-400';
};

export default function PolicyTimelineViewer({
  steps,
  onStepClick,
}: PolicyTimelineViewerProps) {
  const [expandedSteps, setExpandedSteps] = useState<Set<number>>(new Set());

  const toggleStep = (stepNum: number) => {
    const newSet = new Set(expandedSteps);
    if (newSet.has(stepNum)) {
      newSet.delete(stepNum);
    } else {
      newSet.add(stepNum);
    }
    setExpandedSteps(newSet);
  };

  // Calculate step statistics
  const stepStats = useMemo(() => {
    return steps.map((step) => {
      const totalReward = Object.values(step.rewards).reduce((a, b) => a + b, 0);
      const avgReward = totalReward / Object.keys(step.rewards).length;
      const successfulAgents = Object.values(step.rewards).filter((r) => r > 0).length;

      return {
        totalReward,
        avgReward,
        successfulAgents,
        totalAgents: Object.keys(step.rewards).length,
      };
    });
  }, [steps]);

  if (steps.length === 0) {
    return (
      <div className="text-center py-6 text-gray-400">
        No timeline steps available yet
      </div>
    );
  }

  return (
    <div className="space-y-2 max-h-96 overflow-y-auto pr-2">
      {steps.map((step, index) => {
        const stats = stepStats[index];
        const isExpanded = expandedSteps.has(step.step);

        return (
          <div
            key={`step-${step.step}`}
            className="bg-slate-800 border border-slate-600 rounded-lg overflow-hidden hover:border-cyan-400/50 transition"
          >
            {/* Step header - always visible */}
            <button
              onClick={() => {
                toggleStep(step.step);
                onStepClick?.(step);
              }}
              className="w-full px-4 py-3 flex items-center justify-between hover:bg-slate-700/50 transition text-left"
            >
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-sm font-semibold text-cyan-400">
                    Step {step.step}
                  </span>
                  <span className="text-xs text-gray-400">
                    {new Date(step.ts).toLocaleTimeString()}
                  </span>
                </div>

                {/* Quick stats row */}
                <div className="flex gap-4 text-xs">
                  <span className="text-gray-400">
                    Agents: <span className="text-white">{stats.totalAgents}</span>
                  </span>
                  <span className={getRewardStyle(stats.avgReward)}>
                    Avg Reward: <span className="font-semibold">{stats.avgReward.toFixed(3)}</span>
                  </span>
                  <span className="text-green-400">
                    Success: <span className="font-semibold">{stats.successfulAgents}/{stats.totalAgents}</span>
                  </span>
                </div>
              </div>

              <ChevronDown
                size={18}
                className={`text-gray-400 transition-transform ${
                  isExpanded ? 'rotate-180' : ''
                }`}
              />
            </button>

            {/* Expanded details */}
            {isExpanded && (
              <div className="border-t border-slate-600 bg-slate-900/50 px-4 py-3 space-y-3">
                {/* Actions section */}
                <div>
                  <h4 className="text-xs font-semibold text-gray-300 mb-2 uppercase">
                    Agent Actions
                  </h4>
                  <div className="grid grid-cols-1 gap-2">
                    {Object.entries(step.actions).map(([agentId, actionId]) => (
                      <div
                        key={`action-${agentId}`}
                        className="flex items-center justify-between p-2 bg-slate-800 rounded border border-slate-700"
                      >
                        <span className="text-sm font-medium text-gray-300">
                          {agentId}
                        </span>
                        <span
                          className={`px-2 py-1 rounded border text-xs font-semibold ${getActionColor(
                            actionId
                          )}`}
                        >
                          {ACTION_LABELS[actionId] || `Action ${actionId}`}
                        </span>
                        <span className={`text-sm font-semibold ${getRewardStyle(step.rewards[agentId] ?? 0)}`}>
                          {(step.rewards[agentId] ?? 0).toFixed(3)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Rewards summary */}
                <div className="bg-slate-800 rounded border border-slate-700 p-2">
                  <h4 className="text-xs font-semibold text-gray-300 mb-2 uppercase">
                    Rewards Summary
                  </h4>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div>
                      <span className="text-gray-400">Total Reward:</span>
                      <span className={`block font-semibold ${getRewardStyle(stats.totalReward)}`}>
                        {stats.totalReward.toFixed(3)}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-400">Average Reward:</span>
                      <span className={`block font-semibold ${getRewardStyle(stats.avgReward)}`}>
                        {stats.avgReward.toFixed(3)}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Additional agent info */}
                {Object.keys(step.infos).length > 0 && (
                  <details className="text-xs text-gray-400">
                    <summary className="cursor-pointer font-semibold text-gray-300 mb-1">
                      Agent Info (click to expand)
                    </summary>
                    <div className="ml-2 mt-2 space-y-1 bg-slate-800 p-2 rounded border border-slate-700">
                      {Object.entries(step.infos).map(([agentId, info]) => (
                        <div key={`info-${agentId}`} className="text-xs">
                          <span className="text-cyan-400 font-semibold">{agentId}:</span>
                          <pre className="ml-2 text-gray-400 whitespace-pre-wrap break-words">
                            {JSON.stringify(info, null, 2)}
                          </pre>
                        </div>
                      ))}
                    </div>
                  </details>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
