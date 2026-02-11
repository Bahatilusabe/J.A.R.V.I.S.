
import { useState, useEffect } from 'react';
import { useSelector } from 'react-redux';
import { RLAgentSimulation, PolicyEvolutionChart, RecoverySummary } from '../components/SelfHealingSimulation';
import PolicyTimelineViewer from '../components/PolicyTimelineViewer';
import { useSelfHealing } from '@/hooks/useSelfHealing';
import type { SimulationStartRequest, SnapshotMetadata, PolicyUpdate, SimulationMode } from '@/types/self_healing.types';

export default function SelfHealingMonitor() {
  // Use demo flag via env (keeps backward compatibility)
  const demoFlag = (import.meta.env?.VITE_SELF_HEALING_DEMO === 'true');
  const wsUrl = import.meta.env?.VITE_SELF_HEALING_WS_URL as string | undefined;
  const authToken = import.meta.env?.VITE_SELF_HEALING_WS_TOKEN as string | undefined;

  const {
    status,
    isConnected,
    currentJobId,
    startSimulation,
    stopSimulation,
    fetchMetrics,
    initiateRecovery,
    setupMetricsPolling,
    connectWebSocket,
    disconnectWebSocket,
  } = useSelfHealing({ autoConnect: false, demo: demoFlag, wsUrl, authToken });

  // Redux state
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const snapshots = useSelector((state: any) => state.selfHealing?.snapshots) as SnapshotMetadata[];
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const policyTimeline = useSelector((state: any) => state.selfHealing?.policyTimeline) as { updates: PolicyUpdate[] };
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const timelineSteps = useSelector((state: any) => state.selfHealing?.timelineSteps) || [];

  // Local UI state for config
  const [jobId, setJobId] = useState<string | null>(null);
  const [attackers, setAttackers] = useState<number>(5);
  const [defenders, setDefenders] = useState<number>(10);
  const [mode, setMode] = useState<SimulationMode>('training');
  const [polling, setPolling] = useState<boolean>(false);
  const [loadingStart, setLoadingStart] = useState(false);
  const [loadingStop, setLoadingStop] = useState(false);
  const [loadingFetch, setLoadingFetch] = useState(false);

  useEffect(() => {
    // auto-connect WS when component mounts so RLAgentSimulation can use it on demand
    connectWebSocket();
    return () => {
      disconnectWebSocket();
    };
  }, [connectWebSocket, disconnectWebSocket]);

  // Handlers
  const handleStart = async () => {
    setLoadingStart(true);
    const req: SimulationStartRequest = {
      mode,
      initialAttackers: attackers,
      initialDefenders: defenders,
      config: {},
    };

    try {
      const id = await startSimulation(req);
      setJobId(id ?? null);
      // start polling metrics for this job
      if (id) setupMetricsPolling(id);
      setPolling(true);
    } catch (err) {
      // error handled in hook (redux)
    } finally {
      setLoadingStart(false);
    }
  };

  const handleStop = async () => {
    setLoadingStop(true);
    try {
      await stopSimulation(jobId ?? undefined);
      setJobId(null);
      setPolling(false);
    } catch (err) {
      // handled in hook
    } finally {
      setLoadingStop(false);
    }
  };

  const handleFetchNow = async () => {
    if (!jobId) return;
    setLoadingFetch(true);
    try {
      await fetchMetrics(jobId);
    } catch (err) {
      // errors handled in hook
    } finally {
      setLoadingFetch(false);
    }
  };

  const handleRecover = async (snapshotId: string) => {
    try {
      await initiateRecovery(snapshotId, 'full');
    } catch (err) {
      // errors surfaced via Redux
    }
  };

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold text-cyan-400 mb-4">Self-Healing Monitor (Advanced)</h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        <div className="lg:col-span-2">
          <RLAgentSimulation />
          <PolicyEvolutionChart />
        </div>

        <aside className="space-y-4">
          <div className="bg-slate-900 rounded-lg p-4 border border-cyan-400/30">
            <h2 className="text-lg font-semibold text-cyan-300">Simulation Controls</h2>
            <div className="mt-3 space-y-3 text-sm">
              <div className="flex gap-2">
                <label className="flex-1">
                  <div className="text-xs text-gray-400">Mode</div>
                  <select
                    value={mode}
                    onChange={(e) => setMode(e.target.value as SimulationMode)}
                    className="w-full bg-slate-800 text-white rounded px-2 py-1 mt-1"
                    aria-label="Simulation mode"
                  >
                    <option value="training">Training</option>
                    <option value="evaluation">Evaluation</option>
                    <option value="attack_scenario">Attack Scenario</option>
                    <option value="recovery_test">Recovery Test</option>
                  </select>
                </label>
              </div>

              <div className="flex gap-2">
                <label className="flex-1">
                  <div className="text-xs text-gray-400">Initial Attackers</div>
                  <input
                    type="number"
                    value={attackers}
                    min={0}
                    onChange={(e) => setAttackers(Number(e.target.value))}
                    className="w-full bg-slate-800 text-white rounded px-2 py-1 mt-1"
                    aria-label="Initial attackers"
                  />
                </label>
                <label className="flex-1">
                  <div className="text-xs text-gray-400">Initial Defenders</div>
                  <input
                    type="number"
                    value={defenders}
                    min={0}
                    onChange={(e) => setDefenders(Number(e.target.value))}
                    className="w-full bg-slate-800 text-white rounded px-2 py-1 mt-1"
                    aria-label="Initial defenders"
                  />
                </label>
              </div>

              <div className="flex gap-2">
                <button
                  onClick={handleStart}
                  disabled={loadingStart}
                  className={`flex-1 rounded px-3 py-2 font-semibold transition ${loadingStart ? 'bg-emerald-600 text-gray-300 opacity-70 cursor-not-allowed' : 'bg-emerald-500 text-black hover:bg-emerald-600'}`}
                  title="Start simulation"
                >
                  {loadingStart ? '⏳ Starting...' : 'Start'}
                </button>
                <button
                  onClick={handleStop}
                  disabled={loadingStop}
                  className={`rounded px-3 py-2 font-semibold transition ${loadingStop ? 'bg-rose-600 text-gray-300 opacity-70 cursor-not-allowed' : 'bg-rose-500 text-white hover:bg-rose-600'}`}
                  title="Stop simulation"
                >
                  {loadingStop ? '⏳ Stopping...' : 'Stop'}
                </button>
              </div>

              <div className="flex gap-2">
                <button
                  onClick={handleFetchNow}
                  disabled={loadingFetch || !jobId}
                  className={`flex-1 rounded px-3 py-2 transition ${loadingFetch || !jobId ? 'bg-sky-600 text-gray-300 opacity-70 cursor-not-allowed' : 'bg-sky-500 text-white hover:bg-sky-600'}`}
                  title="Fetch latest metrics"
                >
                  {loadingFetch ? '⏳ Fetching...' : 'Fetch metrics now'}
                </button>
                <button
                  onClick={() => {
                    if (jobId) {
                      setupMetricsPolling(jobId);
                      setPolling(true);
                    }
                  }}
                  className={`px-3 py-2 rounded transition ${polling ? 'bg-yellow-500 text-black hover:bg-yellow-600' : 'bg-gray-700 text-white hover:bg-gray-600'}`}
                  title="Start polling metrics"
                >
                  {polling ? '▶ Polling…' : '⏸ Start polling'}
                </button>
              </div>

              <div className="text-xs text-gray-400">
                Status: <span className="text-white">{status ?? 'idle'}</span>
              </div>
              <div className="text-xs text-gray-400">Job ID: <span className="text-white">{jobId ?? currentJobId ?? '—'}</span></div>
              <div className="text-xs text-gray-400">WS Connected: <span className="text-white">{isConnected ? 'yes' : 'no'}</span></div>
            </div>
          </div>

          <RecoverySummary />

          <div className="bg-slate-900 rounded-lg p-4 border border-cyan-400/30">
            <h3 className="text-md font-semibold text-cyan-300 mb-2">Policy Action Timeline</h3>
            <PolicyTimelineViewer steps={timelineSteps} />
          </div>

          <div className="bg-slate-900 rounded-lg p-4 border border-cyan-400/30">
            <h3 className="text-md font-semibold text-cyan-300 mb-2">Policy Versions</h3>
            <div className="max-h-48 overflow-auto text-sm text-gray-200 space-y-2">
              {(policyTimeline?.updates || []).slice().reverse().map((u: PolicyUpdate) => (
                <div key={`${u.tick}-${u.timestamp}`} className="p-2 bg-slate-800 rounded">
                  <div className="text-xs text-gray-400">{new Date(u.timestamp).toLocaleString()}</div>
                  <div className="font-semibold text-white">{u.previousVersion} → {u.newVersion}</div>
                  <div className="text-xs text-gray-400">Improvement: {u.performanceImprovement?.toFixed?.(2) ?? u.performanceImprovement}</div>
                </div>
              ))}
              {(!policyTimeline?.updates || policyTimeline.updates.length === 0) && (
                <div className="text-gray-500">No policy updates yet</div>
              )}
            </div>
          </div>

          <div className="bg-slate-900 rounded-lg p-4 border border-cyan-400/30">
            <h3 className="text-md font-semibold text-cyan-300 mb-2">Snapshots</h3>
            <div className="max-h-40 overflow-auto text-sm text-gray-200 space-y-2">
              {(snapshots || []).slice(-10).reverse().map((s) => (
                <div key={s.id} className="flex items-center justify-between p-2 bg-slate-800 rounded">
                  <div>
                    <div className="font-medium">{s.name}</div>
                    <div className="text-xs text-gray-400">tick {s.tick} · {new Date(s.createdAt).toLocaleString()}</div>
                  </div>
                  <div className="flex flex-col gap-1">
                    <button
                      onClick={() => handleRecover(s.id)}
                      className="bg-indigo-500 text-white px-2 py-1 rounded text-sm"
                      title={`Recover from snapshot ${s.name}`}
                    >
                      Recover
                    </button>
                  </div>
                </div>
              ))}
              {(!snapshots || snapshots.length === 0) && <div className="text-gray-500">No snapshots available</div>}
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}
