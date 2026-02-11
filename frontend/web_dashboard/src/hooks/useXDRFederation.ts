import { useEffect, useCallback } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { RootState } from '../store';
import {
  setFederationNodes,
  setLedgerEntries,
  setModelProvenance,
  addSyncEvent,
  setWSConnected,
  setError,
  setWarning,
} from '../store/slices/xdrSlice';
import {
  FederationStatusResponse,
  LedgerEntriesResponse,
  ModelProvenanceResponse,
  ForensicsResponse,
  FederatedTrainingJob,
} from '../types/xdr.types';

/**
 * useXDRFederation - Custom hook for federated XDR + blockchain ledger
 * Manages WebSocket streaming, REST API calls, and Redux state synchronization
 */
export const useXDRFederation = () => {
  const dispatch = useDispatch();
  const xdrState = useSelector((state: RootState) => state.xdr);

  // Initialize WebSocket connections
  const initializeWebSockets = useCallback(() => {
    // Federation sync WebSocket
    const federationWs = new WebSocket('ws://localhost:5000/ws/federation');

    federationWs.onopen = () => {
      console.log('Federation WebSocket connected');
      dispatch(setWSConnected(true));
      federationWs.send(JSON.stringify({ type: 'subscribe', channel: 'federation_sync' }));
    };

    federationWs.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        if (message.type === 'federation_sync' || message.type === 'node_status') {
          dispatch(addSyncEvent(message.payload));
        }
      } catch (_err) {
        console.error('Federation WS message parse error');
      }
    };

    federationWs.onclose = () => {
      dispatch(setWSConnected(false));
      setTimeout(() => initializeWebSockets(), 5000);
    };

    federationWs.onerror = () => {
      dispatch(setError('Federation WebSocket connection failed'));
    };

    // Ledger subscription WebSocket
    const ledgerWs = new WebSocket('ws://localhost:5000/ws/ledger');

    ledgerWs.onopen = () => {
      console.log('Ledger WebSocket connected');
      ledgerWs.send(JSON.stringify({ type: 'subscribe', channel: 'ledger_entries' }));
    };

    ledgerWs.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        if (message.type === 'ledger_entry') {
          dispatch(setLedgerEntries([message.payload.ledgerEntry, ...xdrState.ledgerEntries]));
        }
      } catch (_err) {
        console.error('Ledger WS message parse error');
      }
    };

    ledgerWs.onerror = () => {
      dispatch(setWarning('Ledger WebSocket connection error'));
    };

    return { federationWs, ledgerWs };
  }, [dispatch, xdrState.ledgerEntries]);

  // Fetch federation status
  const fetchFederationStatus = useCallback(async () => {
    try {
      const response = await fetch('/federation/status');
      if (!response.ok) throw new Error('Federation status fetch failed');
      const data: FederationStatusResponse = await response.json();
      dispatch(setFederationNodes(data.nodes));
      return data.status;
    } catch (err) {
      dispatch(setError(`Federation status error: ${err}`));
      return null;
    }
  }, [dispatch]);

  // Fetch ledger entries
  const fetchLedgerEntries = useCallback(
    async (limit = 50) => {
      try {
        const response = await fetch(`/ledger/entries?limit=${limit}`);
        if (!response.ok) throw new Error('Ledger fetch failed');
        const data: LedgerEntriesResponse = await response.json();
        dispatch(setLedgerEntries(data.entries));
        return data;
      } catch (err) {
        dispatch(setError(`Ledger fetch error: ${err}`));
        return null;
      }
    },
    [dispatch]
  );

  // Fetch model provenance
  const fetchModelProvenance = useCallback(async () => {
    try {
      const response = await fetch('/federation/models');
      if (!response.ok) throw new Error('Model provenance fetch failed');
      const data: ModelProvenanceResponse = await response.json();
      dispatch(setModelProvenance(data.models));
      return data;
    } catch (err) {
      dispatch(setError(`Model provenance error: ${err}`));
      return null;
    }
  }, [dispatch]);

  // Download forensics data
  const downloadForensics = useCallback(
    async (forensicsId: string) => {
      try {
        const response = await fetch(`/forensics/${forensicsId}`);
        if (!response.ok) throw new Error('Forensics download failed');
        const data: ForensicsResponse = await response.json();

        // Verify signature
        if (!data.verifiable) {
          dispatch(setWarning('Forensics signature verification failed'));
          return null;
        }

        return data;
      } catch (err) {
        dispatch(setError(`Forensics download error: ${err}`));
        return null;
      }
    },
    [dispatch]
  );

  // Start federated training
  const startFederatedTraining = useCallback(
    async (modelId: string, config: Record<string, string | number | boolean>) => {
      try {
        const response = await fetch('/federation/start_training', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ modelId, config }),
        });
        if (!response.ok) throw new Error('Training start failed');
        const job: FederatedTrainingJob = await response.json();
        return job;
      } catch (err) {
        dispatch(setError(`Training start error: ${err}`));
        return null;
      }
    },
    [dispatch]
  );

  // Verify model hash
  const verifyModelHash = useCallback(
    async (modelId: string) => {
      try {
        const response = await fetch(`/federation/models/${modelId}/verify`, {
          method: 'POST',
        });
        if (!response.ok) throw new Error('Hash verification failed');
        const result = await response.json();
        return result;
      } catch (err) {
        dispatch(setError(`Hash verification error: ${err}`));
        return null;
      }
    },
    [dispatch]
  );

  // Approve ledger entry forensics
  const approveLedgerEntry = useCallback(
    async (txId: string) => {
      try {
        const response = await fetch(`/ledger/entries/${txId}/approve`, {
          method: 'POST',
        });
        if (!response.ok) throw new Error('Ledger approval failed');
        return await response.json();
      } catch (err) {
        dispatch(setError(`Ledger approval error: ${err}`));
        return null;
      }
    },
    [dispatch]
  );

  // Initialize on mount
  useEffect(() => {
    const { federationWs, ledgerWs } = initializeWebSockets();
    fetchFederationStatus();
    fetchLedgerEntries();
    fetchModelProvenance();

    // Poll federation status every 30s
    const statusInterval = setInterval(fetchFederationStatus, 30000);
    const ledgerInterval = setInterval(() => fetchLedgerEntries(10), 15000);

    return () => {
      clearInterval(statusInterval);
      clearInterval(ledgerInterval);
      federationWs?.close();
      ledgerWs?.close();
    };
  }, [initializeWebSockets, fetchFederationStatus, fetchLedgerEntries, fetchModelProvenance]);

  return {
    // State
    federationNodes: xdrState.federationNodes,
    ledgerEntries: xdrState.ledgerEntries,
    modelProvenance: xdrState.modelProvenance,
    syncEvents: xdrState.syncEvents,
    wsConnected: xdrState.wsConnected,
    isLoading: xdrState.isLoading,

    // Functions
    fetchFederationStatus,
    fetchLedgerEntries,
    fetchModelProvenance,
    downloadForensics,
    startFederatedTraining,
    verifyModelHash,
    approveLedgerEntry,
  };
};

export default useXDRFederation;
