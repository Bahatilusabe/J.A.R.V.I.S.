import React from 'react';
import { AlertCircle, Wifi, WifiOff, RefreshCw } from 'lucide-react';
import FederationRing from '../components/FederationRing';
import LedgerTimeline from '../components/LedgerTimeline';
import ModelProvenance from '../components/ModelProvenanceCard';
import useXDRFederation from '../hooks/useXDRFederation';

/* eslint-disable @typescript-eslint/no-explicit-any */

/**
 * XDRFederation - Main dashboard for federated XDR + blockchain ledger
 * Integrates federation ring, ledger timeline, and model provenance
 */
const XDRFederation: React.FC = () => {
  const { federationNodes, ledgerEntries, modelProvenance, wsConnected, fetchFederationStatus } =
    useXDRFederation();

  const handleRefresh = async () => {
    await fetchFederationStatus();
  };

   
  const criticalEntries = (ledgerEntries as any[]).filter((e: any) => e.severity === 'critical');
   
  const healthPercent = (federationNodes as any[]).filter((n: any) => n.status === 'online').length;

  return (
    <div className="w-full space-y-4 pb-8">
      {/* Header */}
      <div className="flex justify-between items-center p-4 bg-gray-900 rounded-lg border border-gray-700">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            Federated XDR + Blockchain
          </h1>
          <p className="text-sm text-gray-400 mt-1">Network federation, ledger entries, and model provenance</p>
        </div>
        <div className="flex items-center gap-3">
          {wsConnected ? (
            <div className="flex items-center gap-2 text-green-500">
              <Wifi className="w-5 h-5 animate-pulse" />
              <span className="text-sm font-semibold">Connected</span>
            </div>
          ) : (
            <div className="flex items-center gap-2 text-red-500">
              <WifiOff className="w-5 h-5" />
              <span className="text-sm font-semibold">Offline</span>
            </div>
          )}
          {criticalEntries.length > 0 && (
            <div className="flex items-center gap-2 text-red-500 bg-red-950 px-3 py-2 rounded">
              <AlertCircle className="w-4 h-4" />
              <span className="text-sm font-semibold">{criticalEntries.length} Critical</span>
            </div>
          )}
          <button
            onClick={handleRefresh}
            className="p-2 bg-blue-900 hover:bg-blue-800 rounded border border-blue-700 text-blue-300 transition"
            title="Refresh data"
          >
            <RefreshCw className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-3 gap-4">
        {/* Federation Ring - Full Height */}
        <div className="col-span-2 row-span-2">
          <FederationRing
            nodes={federationNodes}
            syncAnimation={wsConnected}
            showLabels={true}
            onNodeSelect={() => {}}
          />
        </div>

        {/* Quick Stats */}
        <div className="space-y-3">
          <div className="p-3 bg-gray-900 rounded-lg border border-gray-700">
            <div className="text-sm text-gray-400">Federation Health</div>
            <div className="text-2xl font-bold text-green-500 mt-1">
              {federationNodes.length > 0 ? Math.round((healthPercent / federationNodes.length) * 100) : 0}%
            </div>
            <div className="text-xs text-gray-500 mt-1">
              {healthPercent} / {federationNodes.length} nodes online
            </div>
          </div>

          <div className="p-3 bg-gray-900 rounded-lg border border-gray-700">
            <div className="text-sm text-gray-400">Ledger Entries</div>
            <div className="text-2xl font-bold text-blue-500 mt-1">{ledgerEntries.length}</div>
            { }
            <div className="text-xs text-gray-500 mt-1">
              {(ledgerEntries as any[]).filter((e: any) => e.status === 'finalized').length} finalized
            </div>
          </div>

          <div className="p-3 bg-gray-900 rounded-lg border border-gray-700">
            <div className="text-sm text-gray-400">Model Provenance</div>
            <div className="text-2xl font-bold text-purple-500 mt-1">
              {modelProvenance.models.length}
            </div>
            { }
            <div className="text-xs text-gray-500 mt-1">
              {(modelProvenance.models as any[]).filter((m: any) => m.status === 'deployed').length} deployed
            </div>
          </div>
        </div>
      </div>

      {/* Ledger Timeline */}
      <LedgerTimeline
        entries={ledgerEntries}
        expandedEntryIds={[]}
        onEntryToggle={() => {}}
        onForensicsDownload={() => {}}
      />

      {/* Model Provenance */}
      <div className="bg-gray-900 rounded-lg border border-gray-700 p-4">
        <h2 className="text-lg font-bold text-white mb-4">Model Provenance & Training History</h2>
        <div className="space-y-3 max-h-96 overflow-y-auto">
          {modelProvenance.models.length === 0 ? (
            <div className="flex items-center justify-center py-8 text-gray-400">
              <p>No models in federation</p>
            </div>
          ) : (
             
            (modelProvenance.models as any[]).map((model: any) => (
              <ModelProvenance
                key={model.modelId}
                model={model}
                isExpanded={modelProvenance.expandedModelIds.includes(model.modelId)}
                onToggleExpand={() => {}}
                onHashVerify={() => {}}
              />
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default XDRFederation;
