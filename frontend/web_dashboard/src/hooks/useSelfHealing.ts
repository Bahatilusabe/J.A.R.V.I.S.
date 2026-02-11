import { useEffect, useRef, useCallback, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import type { Dispatch as ReduxDispatch, AnyAction } from 'redux';
import type {
  SimulationStartRequest,
  AgentUpdateMessage,
  RewardUpdateMessage,
  MetricsUpdateMessage,
  ErrorMessage,
} from '@/types/self_healing.types';
import startSelfHealingDemo from './selfHealingDemo';

/*
  useSelfHealing hook options and env var examples

  You can run the UI in demo mode (no backend) by calling:
    useSelfHealing({ demo: true })

  Or provide a custom WebSocket URL and token (useful when backend is on a different host):
    useSelfHealing({ wsUrl: import.meta.env.VITE_SELF_HEALING_WS_URL, authToken: import.meta.env.VITE_SELF_HEALING_WS_TOKEN })

  Vite env var examples (add to .env or .env.local):
    VITE_SELF_HEALING_WS_URL=wss://my-backend.example.com/ws/self_healing
    VITE_SELF_HEALING_WS_TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6...YOUR_TOKEN
    VITE_SELF_HEALING_DEMO=true

  Note: The hook will append the token as a query parameter to the WS URL when provided.
*/

// Note: These Redux actions will be created in the selfHealingSlice
// For now, we'll define placeholder functions that dispatch appropriate actions
interface DispatchAction {
  type: string;
  payload?: unknown;
}

const setSimulationStatus = (status: string): DispatchAction => ({ type: 'selfHealing/setStatus', payload: status });
const setMetrics = (metrics: unknown): DispatchAction => ({ type: 'selfHealing/setMetrics', payload: metrics });
const setTimelineSteps = (steps: unknown): DispatchAction => ({ type: 'selfHealing/setTimelineSteps', payload: steps });
const setAgents = (agents: unknown): DispatchAction => ({ type: 'selfHealing/setAgents', payload: agents });
const setRewardFunction = (reward: unknown): DispatchAction => ({ type: 'selfHealing/setReward', payload: reward });
const setWebSocketConnected = (connected: boolean): DispatchAction => ({ type: 'selfHealing/setWSConnected', payload: connected });
const setError = (error: string): DispatchAction => ({ type: 'selfHealing/setError', payload: error });
const setLoading = (loading: boolean): DispatchAction => ({ type: 'selfHealing/setLoading', payload: loading });

interface UseSpelfHealingOptions {
  autoConnect?: boolean;
  metricsInterval?: number;
  snapshotsInterval?: number;
  // demo: run the in-browser demo data generator instead of real WebSocket
  demo?: boolean;
  // optional custom websocket URL (overrides auto-constructed url)
  wsUrl?: string;
  // optional auth token to append to websocket query
  authToken?: string;
}

export const useSelfHealing = (options: UseSpelfHealingOptions = {}) => {
  const { autoConnect = true, metricsInterval = 15000, snapshotsInterval = 60000 } = options;

  const dispatch = useDispatch<ReduxDispatch<AnyAction>>();
  const wsRef = useRef<WebSocket | null>(null);
  const demoHandleRef = useRef<ReturnType<typeof startSelfHealingDemo> | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const metricsIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const snapshotsIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const status = useSelector((state: any) => state.selfHealing?.simulationStatus);
  // WebSocket connected flag from Redux (works for demo mode too)
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const wsConnected = useSelector((state: any) => state.selfHealing?.wsConnected);

  // WebSocket connection handler - uses effect to manage lifecycle
  const connectWebSocket = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      // If a custom wsUrl is provided in options, use it; otherwise construct from current host
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const baseUrl = options.wsUrl || `${protocol}//${window.location.host}/ws/self_healing`;
      const wsUrl = options.authToken ? `${baseUrl}${baseUrl.includes('?') ? '&' : '?'}token=${encodeURIComponent(options.authToken)}` : baseUrl;
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        console.log('[SelfHealing] WebSocket connected');
        dispatch(setWebSocketConnected(true));
        reconnectAttemptsRef.current = 0;
      };

      wsRef.current.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          // Handle message directly here to avoid dependency issues
          const { type } = message as { type: string };
          if (type === 'agent_update') {
            const agentMsg = message as AgentUpdateMessage;
            dispatch(setAgents({
              attackers: agentMsg.agentCount.attackers,
              defenders: agentMsg.agentCount.defenders,
              totalAgents: agentMsg.agentCount.attackers + agentMsg.agentCount.defenders,
            }));
          } else if (type === 'reward_update') {
            const rewardMsg = message as RewardUpdateMessage;
            dispatch(
              setRewardFunction({
                metric: 'total' as const,
                avgReward: rewardMsg.avgReward,
                maxReward: rewardMsg.totalReward,
                minReward: 0,
              })
            );
          } else if (type === 'metrics_update') {
            const metricsMsg = message as MetricsUpdateMessage;
            dispatch(setMetrics(metricsMsg.metrics));
          } else if (type === 'error') {
            const errorMsg = message as ErrorMessage;
            dispatch(setError(errorMsg.message));
          }
        } catch (err) {
          console.error('[SelfHealing] Failed to parse WebSocket message:', err);
        }
      };

      wsRef.current.onerror = (error) => {
        console.error('[SelfHealing] WebSocket error:', error);
        dispatch(setError('WebSocket connection error'));
      };

      wsRef.current.onclose = () => {
        console.log('[SelfHealing] WebSocket closed');
        dispatch(setWebSocketConnected(false));
        // Attempt reconnect with exponential backoff
        reconnectAttemptsRef.current += 1;
        const backoffMs = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 30000);
        if (reconnectAttemptsRef.current <= 5) {
          setTimeout(() => connectWebSocket(), backoffMs);
        }
      };
    } catch (err) {
      console.error('[SelfHealing] Failed to connect WebSocket:', err);
      dispatch(setError('Failed to connect to real-time updates'));
      // Attempt reconnect
      reconnectAttemptsRef.current += 1;
      const backoffMs = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 30000);
      if (reconnectAttemptsRef.current <= 5) {
        setTimeout(() => connectWebSocket(), backoffMs);
      }
    }
  }, [dispatch, options.wsUrl, options.authToken]);


  // Handle WebSocket messages

  // REST API functions
  const startSimulation = useCallback(
    async (config: SimulationStartRequest) => {
      try {
        dispatch(setLoading(true));
        const response = await fetch('/api/self_healing/start', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(config),
        });

        if (!response.ok) throw new Error('Failed to start simulation');

        const data = await response.json();
        const jobId = data?.jobId ?? `job_${Date.now()}`;
        setCurrentJobId(jobId);
        dispatch(setSimulationStatus('running'));
        return jobId;
      } catch (err) {
        dispatch(setError(err instanceof Error ? err.message : 'Start simulation failed'));
        throw err;
      } finally {
        dispatch(setLoading(false));
      }
    },
    [dispatch]
  );

  const stopSimulation = useCallback(
    async (jobId?: string) => {
      const targetJobId = jobId || currentJobId;
      if (!targetJobId) {
        dispatch(setError('No active job to stop'));
        return;
      }

      try {
        dispatch(setLoading(true));
        const response = await fetch('/api/self_healing/stop', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ jobId: targetJobId }),
        });

        if (!response.ok) throw new Error('Failed to stop simulation');

        dispatch(setSimulationStatus('stopped'));
        setCurrentJobId(null);
      } catch (err) {
        dispatch(setError(err instanceof Error ? err.message : 'Stop simulation failed'));
        throw err;
      } finally {
        dispatch(setLoading(false));
      }
    },
    [dispatch, currentJobId]
  );

  const fetchMetrics = useCallback(
    async (_jobId?: string) => {
      try {
        // Ignore jobId for now; backend /metrics endpoint doesn't support filtering by job
        const response = await fetch('/api/self_healing/metrics');
        if (!response.ok) throw new Error('Failed to fetch metrics');

        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const data: any = await response.json();
        // Transform backend response to match Redux expected shape
        const timeline = data.timeline || [];
        const avgRewardValue = Object.values(data.rolling_average || {}).reduce((a: number, b: unknown) => a + (typeof b === 'number' ? b : 0), 0) / Object.keys(data.rolling_average || {}).length;
        const totalRewardValue = Object.values(data.per_agent || {}).reduce((a: number, b: unknown) => a + (typeof b === 'number' ? b : 0), 0);
        dispatch(setMetrics({
          currentTick: timeline.length,
          elapsedTime: 0,
          attackers: 0,
          defenders: 0,
          compromised: 0,
          recovered: 0,
          avgReward: avgRewardValue,
          totalReward: totalRewardValue,
          policyVersion: data.model_id || 'v1.0.0',
          convergenceProgress: (data.confidence || 0) * 100,
        }));
        // Also store the timeline steps for display
        dispatch(setTimelineSteps(timeline));
        return data;
      } catch (err) {
        console.error('[SelfHealing] Failed to fetch metrics:', err);
        return null;
      }
    },
    [dispatch]
  );

  // Policies & actions integration
  const fetchPolicies = useCallback(async (orgId?: string, limit = 100) => {
    try {
      const q = orgId ? `?org_id=${encodeURIComponent(orgId)}&limit=${limit}` : `?limit=${limit}`;
      const res = await fetch(`/api/self_healing/policies${q}`);
      if (!res.ok) throw new Error('Failed to fetch policies');
      return await res.json();
    } catch (err) {
      console.error('[SelfHealing] Failed to fetch policies:', err);
      return null;
    }
  }, []);

  const getPolicyDetails = useCallback(async (policyId: string) => {
    try {
      const res = await fetch(`/api/self_healing/policies/${encodeURIComponent(policyId)}`);
      if (!res.ok) throw new Error('Failed to fetch policy details');
      return await res.json();
    } catch (err) {
      console.error('[SelfHealing] Failed to fetch policy details:', err);
      return null;
    }
  }, []);

  const generatePolicy = useCallback(async (payload: { org_id: string; recent_incidents: string[]; threat_landscape: string; custom_rules?: Record<string, unknown>[] }) => {
    try {
      const res = await fetch(`/api/self_healing/policies/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error('Failed to generate policy');
      return await res.json();
    } catch (err) {
      console.error('[SelfHealing] Policy generation failed:', err);
      return null;
    }
  }, []);

  const simulatePolicy = useCallback(async (policyId: string, body: { simulated_attacks: string[]; simulation_rounds?: number }) => {
    try {
      const res = await fetch(`/api/self_healing/policies/${encodeURIComponent(policyId)}/simulate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error('Policy simulation failed');
      return await res.json();
    } catch (err) {
      console.error('[SelfHealing] Policy simulation failed:', err);
      return null;
    }
  }, []);

  const submitPolicyToBlockchain = useCallback(async (policyId: string, payload: { policy_hash: string; policy_content?: string; org_id?: string }) => {
    try {
      const res = await fetch(`/api/self_healing/policies/${encodeURIComponent(policyId)}/submit-blockchain`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error('Blockchain submission failed');
      return await res.json();
    } catch (err) {
      console.error('[SelfHealing] Blockchain submission failed:', err);
      return null;
    }
  }, []);

  const fetchActions = useCallback(async (resource?: string) => {
    try {
      const url = resource ? `/api/self_healing/actions?resource=${encodeURIComponent(resource)}` : `/api/self_healing/actions`;
      const res = await fetch(url);
      if (!res.ok) throw new Error('Failed to fetch actions');
      return await res.json();
    } catch (err) {
      console.error('[SelfHealing] Failed to fetch actions:', err);
      return null;
    }
  }, []);

  const fetchHistory = useCallback(async (page = 1, per_page = 20) => {
    try {
      const res = await fetch(`/api/self_healing/history?page=${page}&per_page=${per_page}`);
      if (!res.ok) throw new Error('Failed to fetch history');
      return await res.json();
    } catch (err) {
      console.error('[SelfHealing] Failed to fetch history:', err);
      return null;
    }
  }, []);

  // Initiate recovery from a snapshot
  const initiateRecovery = useCallback(async (snapshotId: string, recoveryType: 'full' | 'partial' | 'differential' = 'full') => {
    try {
      dispatch(setLoading(true));
      const res = await fetch(`/api/self_healing/recover`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ snapshotId, recoveryType }),
      });
      if (!res.ok) {
        const text = await res.text().catch(() => '');
        throw new Error(`Recovery request failed${text ? `: ${text}` : ''}`);
      }
      const data = await res.json().catch(() => ({}));
      // Optionally update Redux status so UI reacts
      dispatch(setSimulationStatus('recovery_in_progress'));
      return data;
    } catch (err) {
      console.error('[SelfHealing] initiateRecovery failed:', err);
      dispatch(setError(err instanceof Error ? err.message : 'Recovery failed'));
      return null;
    } finally {
      dispatch(setLoading(false));
    }
  }, [dispatch]);

  // Setup periodic metric polling
  const setupMetricsPolling = useCallback((jobId: string) => {
    if (metricsIntervalRef.current) clearInterval(metricsIntervalRef.current);

    metricsIntervalRef.current = setInterval(() => {
      fetchMetrics(jobId).catch(console.error);
    }, metricsInterval);
  }, [metricsInterval, fetchMetrics]);

  // Setup periodic snapshot fetching
  const setupSnapshotsPolling = useCallback(() => {
    if (snapshotsIntervalRef.current) clearInterval(snapshotsIntervalRef.current);

    snapshotsIntervalRef.current = setInterval(() => {
      // Trigger snapshots fetch via WebSocket or REST API
      // This would be handled by the Redux thunk in a real implementation
      console.log('[SelfHealing] Polling snapshots...');
    }, snapshotsInterval);
  }, [snapshotsInterval]);

  // Auto-connect on mount. If demo mode is requested, start the in-browser demo generator instead of a real WS.
  useEffect(() => {
    if (!autoConnect) return undefined;

    if (options.demo) {
      // start demo generator which will dispatch into Redux
      demoHandleRef.current = startSelfHealingDemo(dispatch as ReduxDispatch<AnyAction>);
      setupSnapshotsPolling();
    } else {
      connectWebSocket();
      setupSnapshotsPolling();
    }

    return () => {
      // cleanup ws or demo
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.close();
      }
      if (demoHandleRef.current && typeof demoHandleRef.current.stop === 'function') {
        demoHandleRef.current.stop();
        demoHandleRef.current = null;
      }
      if (metricsIntervalRef.current) clearInterval(metricsIntervalRef.current);
      if (snapshotsIntervalRef.current) clearInterval(snapshotsIntervalRef.current);
    };
  }, [autoConnect, connectWebSocket, setupSnapshotsPolling, options.demo, dispatch]);

  return {
    // Status
    status,
    isConnected: !!wsConnected,
    currentJobId,

    // Operations
    startSimulation,
    stopSimulation,
    fetchMetrics,
    initiateRecovery,
    setupMetricsPolling,
    setupSnapshotsPolling,

    // Policies & actions
    fetchPolicies,
    getPolicyDetails,
    generatePolicy,
    simulatePolicy,
    submitPolicyToBlockchain,
    fetchActions,
    fetchHistory,

    // WebSocket
    connectWebSocket,
    disconnectWebSocket: () => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.close();
      }
      if (demoHandleRef.current && typeof demoHandleRef.current.stop === 'function') {
        demoHandleRef.current.stop();
        demoHandleRef.current = null;
      }
    },
  };
};

export default useSelfHealing;
