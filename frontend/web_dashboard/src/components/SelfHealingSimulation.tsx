import React, { useMemo } from 'react';
import { useSelector } from 'react-redux';
import { useSelfHealing } from '@/hooks/useSelfHealing';
import type { RewardDataPoint, Agent } from '@/types/self_healing.types';

// Connected RL Multi-Agent View
function RLAgentSimulation() {
  // allow demo mode or custom WS via Vite env vars
  // VITE_SELF_HEALING_DEMO=true to enable demo generator
  const demoFlag = (import.meta.env?.VITE_SELF_HEALING_DEMO === 'true');
  const wsUrl = import.meta.env?.VITE_SELF_HEALING_WS_URL as string | undefined;
  const authToken = import.meta.env?.VITE_SELF_HEALING_WS_TOKEN as string | undefined;
  const { connectWebSocket } = useSelfHealing({ autoConnect: true, demo: demoFlag, wsUrl, authToken });
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const agents = useSelector((state: any) => state.selfHealing?.agents) as {
    attackers: Agent[];
    defenders: Agent[];
  };

  // ensure websocket is connected when component mounts
  React.useEffect(() => {
    connectWebSocket();
  }, [connectWebSocket]);

  const attackerNodes = agents?.attackers || [];
  const defenderNodes = agents?.defenders || [];

  return (
    <div className="bg-slate-900 rounded-lg p-4 mb-6 border border-cyan-400/30">
      <h2 className="text-lg font-bold text-cyan-300 mb-2">RL Multi-Agent View</h2>
      <div className="relative w-full min-h-[180px] rounded bg-slate-800/40 flex items-center justify-center">
        <div className="relative w-full h-48">
          {/* Render attackers and defenders positioned by x/y when available */}
          {[...attackerNodes].slice(0, 50).map((a) => (
            // eslint-disable-next-line
            <div
              key={a.id}
              title={`Attacker ${a.id}`}
              className="w-6 h-6 rounded-full bg-red-500 border-2 border-red-300 shadow-lg absolute"
              style={{ left: `${(a.x % 100)}%`, top: `${(a.y % 100)}%`, transform: 'translate(-50%, -50%)' }}
            />
          ))}

          {[...defenderNodes].slice(0, 50).map((d) => (
            // eslint-disable-next-line
            <div
              key={d.id}
              title={`Defender ${d.id}`}
              className="w-6 h-6 rounded-full bg-blue-500 border-2 border-blue-300 shadow-lg absolute"
              style={{ left: `${(d.x % 100)}%`, top: `${(d.y % 100)}%`, transform: 'translate(-50%, -50%)' }}
            />
          ))}
        </div>
        <div className="absolute bottom-2 left-2 text-xs text-gray-300">Red = Attacker · Blue = Defender</div>
      </div>
    </div>
  );
}

// Connected Policy Evolution Chart (uses reward history)
function PolicyEvolutionChart() {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const rewardHistory = useSelector((state: any) => state.selfHealing?.rewardHistory) as RewardDataPoint[];

  const points = useMemo(() => {
    if (!Array.isArray(rewardHistory) || rewardHistory.length === 0) return '';
    const last = rewardHistory.slice(-60); // last 60 points
    const w = 300;
    const h = 80;
    const maxReward = Math.max(...last.map((p) => p.totalReward), 1);
    return last
      .map((p, i) => {
        const x = Math.round((i / (last.length - 1 || 1)) * w);
        const y = Math.round(h - (p.totalReward / maxReward) * (h - 10));
        return `${x},${y}`;
      })
      .join(' ');
  }, [rewardHistory]);

  return (
    <div className="bg-slate-900 rounded-lg p-4 mb-6 border border-cyan-400/30">
      <h2 className="text-lg font-bold text-cyan-300 mb-2">Policy Evolution Curve</h2>
      <div className="h-32 flex items-end">
        <svg width="100%" height="100%" viewBox="0 0 300 80" className="w-full h-full">
          <polyline fill="none" stroke="#22d3ee" strokeWidth="3" points={points || '0,70 300,70'} />
        </svg>
      </div>
      <div className="text-xs text-gray-400 mt-2 text-center">Policy performance (total reward) over recent ticks</div>
    </div>
  );
}

// Connected Recovery Summary (metrics + snapshots)
function RecoverySummary() {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const metrics = useSelector((state: any) => state.selfHealing?.metrics) as {
    attackers: number;
    defenders: number;
    compromised: number;
    recovered: number;
    avgReward: number;
    totalReward: number;
    policyVersion: string;
  };

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const snapshots = useSelector((state: any) => state.selfHealing?.snapshots) as any[];

  return (
    <div className="bg-slate-900 rounded-lg p-4 border border-cyan-400/30">
      <h2 className="text-lg font-bold text-cyan-300 mb-2">Recovery Summary</h2>
      <div className="grid grid-cols-2 gap-3 text-sm text-gray-200">
        <div>
          <div className="text-xs text-gray-400">Attackers</div>
          <div className="font-semibold text-white">{metrics?.attackers ?? '—'}</div>
        </div>
        <div>
          <div className="text-xs text-gray-400">Defenders</div>
          <div className="font-semibold text-white">{metrics?.defenders ?? '—'}</div>
        </div>
        <div>
          <div className="text-xs text-gray-400">Compromised</div>
          <div className="font-semibold text-amber-400">{metrics?.compromised ?? '—'}</div>
        </div>
        <div>
          <div className="text-xs text-gray-400">Recovered</div>
          <div className="font-semibold text-green-400">{metrics?.recovered ?? '—'}</div>
        </div>
        <div className="col-span-2">
          <div className="text-xs text-gray-400">Policy Version</div>
          <div className="font-semibold text-cyan-300">{metrics?.policyVersion ?? '—'}</div>
        </div>
      </div>

      <div className="mt-4">
        <div className="text-xs text-gray-400">Recent Snapshots</div>
        <ul className="text-sm text-gray-200 mt-2 space-y-1 max-h-40 overflow-auto">
          {(snapshots || []).slice(-5).reverse().map((s) => (
            <li key={s.id} className="flex justify-between">
              <span>{s.name}</span>
              <span className="text-xs text-gray-400">tick {s.tick}</span>
            </li>
          ))}
          {(!snapshots || snapshots.length === 0) && <li className="text-gray-500">No snapshots available</li>}
        </ul>
      </div>
    </div>
  );
}

export { RLAgentSimulation, PolicyEvolutionChart, RecoverySummary };
