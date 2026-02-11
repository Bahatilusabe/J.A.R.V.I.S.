import React, { useMemo } from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import type { RewardFunction, RewardMetric } from '@/types/self_healing.types';

interface RewardChartProps {
  rewardFunction: RewardFunction;
  selectedMetric: RewardMetric;
  onMetricChange: (metric: RewardMetric) => void;
  isLiveMode: boolean;
}

interface ChartPoint {
  tick: number;
  value: number;
  x: number;
  y: number;
}

export const RewardChart: React.FC<RewardChartProps> = ({
  rewardFunction,
  selectedMetric,
  onMetricChange,
  isLiveMode,
}) => {
  const CHART_WIDTH = 800;
  const CHART_HEIGHT = 300;
  const PADDING = 40;
  const SVG_WIDTH = CHART_WIDTH + PADDING * 2;
  const SVG_HEIGHT = CHART_HEIGHT + PADDING * 2;

  // Calculate metrics
  const stats = useMemo(() => {
    const data = rewardFunction.rewardHistory;
    if (data.length === 0) {
      return {
        min: 0,
        max: 0,
        avg: 0,
        current: 0,
        trend: 'stable' as const,
        trendPercent: 0,
      };
    }

    const values = data.map((d) => d.totalReward);
    const min = Math.min(...values);
    const max = Math.max(...values);
    const avg = values.reduce((a, b) => a + b, 0) / values.length;
    const current = values[values.length - 1];

    let trend: 'improving' | 'stable' | 'declining' = 'stable';
    let trendPercent = 0;

    if (data.length >= 2) {
      const prev = values[values.length - 2];
      const delta = current - prev;
      trendPercent = Math.abs((delta / Math.abs(prev)) * 100);
      
      if (delta > 0.001) trend = 'improving';
      else if (delta < -0.001) trend = 'declining';
    }

    return { min, max, avg, current, trend, trendPercent };
  }, [rewardFunction.rewardHistory]);

  // Prepare chart data
  const chartData = useMemo((): ChartPoint[] => {
    const data = rewardFunction.rewardHistory;
    if (data.length === 0) return [];

    const values = data.map((d) => d.totalReward);
    const minValue = Math.min(...values);
    const maxValue = Math.max(...values);
    const range = maxValue - minValue || 1;

    return data.map((point, idx) => {
      const x = PADDING + (idx / (data.length - 1 || 1)) * CHART_WIDTH;
      const normalized = (point.totalReward - minValue) / range;
      const y = PADDING + CHART_HEIGHT - normalized * CHART_HEIGHT;

      return {
        tick: point.tick,
        value: point.totalReward,
        x,
        y,
      };
    });
  }, [rewardFunction.rewardHistory]);

  // Draw trend line
  const trendPath = useMemo(() => {
    if (chartData.length < 2) return '';

    return (
      'M ' +
      chartData
        .map((p) => `${p.x},${p.y}`)
        .join(' L ')
    );
  }, [chartData]);

  // Draw gradient area
  const areaPath = useMemo(() => {
    if (chartData.length === 0) return '';

    const pathData = [
      `M ${chartData[0].x},${PADDING + CHART_HEIGHT}`,
      ...chartData.map((p) => `L ${p.x},${p.y}`),
      `L ${chartData[chartData.length - 1].x},${PADDING + CHART_HEIGHT}`,
      'Z',
    ];

    return pathData.join(' ');
  }, [chartData]);

  const getTrendIcon = () => {
    if (stats.trend === 'improving') {
      return <TrendingUp className="text-green-600" size={16} />;
    } else if (stats.trend === 'declining') {
      return <TrendingDown className="text-red-600" size={16} />;
    } else {
      return <Minus className="text-gray-600" size={16} />;
    }
  };

  const getTrendColor = () => {
    if (stats.trend === 'improving') return 'text-green-700 bg-green-50';
    if (stats.trend === 'declining') return 'text-red-700 bg-red-50';
    return 'text-gray-700 bg-gray-50';
  };

  return (
    <div className="flex flex-col gap-4 p-4 bg-white rounded-lg border border-gray-200">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-semibold text-gray-900">Reward Function Over Time</h3>
          <p className="text-xs text-gray-600">Training convergence analysis</p>
        </div>

        <div className={`flex items-center gap-2 px-3 py-1.5 rounded ${getTrendColor()}`}>
          {getTrendIcon()}
          <span className="text-sm font-medium">
            {stats.trend === 'improving'
              ? `+${stats.trendPercent.toFixed(2)}%`
              : `${stats.trendPercent.toFixed(2)}%`}
          </span>
        </div>
      </div>

      <div className="flex gap-3 flex-wrap">
        {(['total', 'defense_success', 'attack_prevention', 'recovery_speed', 'resource_efficiency'] as RewardMetric[]).map(
          (metric) => (
            <button
              key={metric}
              onClick={() => onMetricChange(metric)}
              className={`px-3 py-1.5 rounded text-sm font-medium transition ${
                selectedMetric === metric
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {metric.replace(/_/g, ' ')}
            </button>
          )
        )}
      </div>

      <svg
        width={SVG_WIDTH}
        height={SVG_HEIGHT}
        className="border border-gray-200 rounded bg-gray-50"
      >
        {/* Grid lines */}
        {[0, 0.25, 0.5, 0.75, 1].map((y) => (
          <line
            key={`h-${y}`}
            x1={PADDING}
            y1={PADDING + y * CHART_HEIGHT}
            x2={PADDING + CHART_WIDTH}
            y2={PADDING + y * CHART_HEIGHT}
            stroke="#e5e7eb"
            strokeWidth="1"
            strokeDasharray="4,4"
          />
        ))}

        {/* Axes */}
        <line
          x1={PADDING}
          y1={PADDING}
          x2={PADDING}
          y2={PADDING + CHART_HEIGHT}
          stroke="#000"
          strokeWidth="1"
        />
        <line
          x1={PADDING}
          y1={PADDING + CHART_HEIGHT}
          x2={PADDING + CHART_WIDTH}
          y2={PADDING + CHART_HEIGHT}
          stroke="#000"
          strokeWidth="1"
        />

        {/* Area under curve */}
        <path d={areaPath} fill="url(#rewardGradient)" opacity="0.3" />

        {/* Trend line */}
        <path
          d={trendPath}
          stroke="#3b82f6"
          strokeWidth="2"
          fill="none"
          vectorEffect="non-scaling-stroke"
        />

        {/* Data points */}
        {chartData.map((point, idx) => (
          <circle
            key={`point-${idx}`}
            cx={point.x}
            cy={point.y}
            r="3"
            fill="#3b82f6"
            opacity={idx === chartData.length - 1 ? 1 : 0.6}
          />
        ))}

        {/* Gradient definition */}
        <defs>
          <linearGradient id="rewardGradient" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.6" />
            <stop offset="100%" stopColor="#3b82f6" stopOpacity="0.1" />
          </linearGradient>
        </defs>

        {/* Y-axis labels */}
        {[0, 0.25, 0.5, 0.75, 1].map((y) => {
          const value = stats.min + (1 - y) * (stats.max - stats.min);
          return (
            <text
              key={`y-label-${y}`}
              x={PADDING - 8}
              y={PADDING + y * CHART_HEIGHT + 4}
              fontSize="12"
              textAnchor="end"
              fill="#6b7280"
            >
              {value.toFixed(2)}
            </text>
          );
        })}

        {/* X-axis labels */}
        {[0, 0.25, 0.5, 0.75, 1].map((x) => {
          const idx = Math.floor(x * (chartData.length - 1));
          const tick = chartData[idx]?.tick || 0;
          return (
            <text
              key={`x-label-${x}`}
              x={PADDING + x * CHART_WIDTH}
              y={PADDING + CHART_HEIGHT + 20}
              fontSize="12"
              textAnchor="middle"
              fill="#6b7280"
            >
              {tick}
            </text>
          );
        })}
      </svg>

      <div className="grid grid-cols-4 gap-2 text-sm">
        <div className="p-2 bg-blue-50 rounded border border-blue-200">
          <div className="text-xs text-blue-700">Current</div>
          <div className="font-semibold text-blue-900">{stats.current.toFixed(3)}</div>
        </div>
        <div className="p-2 bg-green-50 rounded border border-green-200">
          <div className="text-xs text-green-700">Avg</div>
          <div className="font-semibold text-green-900">{stats.avg.toFixed(3)}</div>
        </div>
        <div className="p-2 bg-purple-50 rounded border border-purple-200">
          <div className="text-xs text-purple-700">Max</div>
          <div className="font-semibold text-purple-900">{stats.max.toFixed(3)}</div>
        </div>
        <div className="p-2 bg-orange-50 rounded border border-orange-200">
          <div className="text-xs text-orange-700">Min</div>
          <div className="font-semibold text-orange-900">{stats.min.toFixed(3)}</div>
        </div>
      </div>

      {isLiveMode && (
        <div className="flex items-center gap-2 px-3 py-2 bg-amber-50 border border-amber-200 rounded text-xs text-amber-700">
          <div className="w-2 h-2 bg-amber-600 rounded-full animate-pulse" />
          Real-time update (next tick in {Math.floor(Math.random() * 5) + 1}s)
        </div>
      )}
    </div>
  );
};
