# Advanced Forensics Panel - Integration & Usage Guide

## Overview

The Advanced Forensics Panel is a cutting-edge forensics analysis dashboard that provides comprehensive incident investigation capabilities aligned with the backend forensics APIs. It enables security analysts to investigate incidents across multiple layers:

- **Real-time timeline visualization** of incident events
- **Interactive evidence browser** with chain-of-custody tracking
- **Cryptographic signature verification** using post-quantum cryptography (Dilithium)
- **Multi-source data aggregation** from LedgerManager, Web3, and Hyperledger Fabric
- **Advanced filtering, search, and export** capabilities

## Architecture

### Components

The forensics panel consists of three main components:

#### 1. **AdvancedForensicsPanel** (`AdvancedForensicsPanel.tsx`)
The main dashboard orchestrator that:
- Fetches forensics records from `/forensics/incidents/{incident_id}/forensics`
- Manages state for timeline, findings, and evidence filtering
- Provides view switching between timeline, evidence, findings, and verification modes
- Integrates signature verification
- Handles data export in JSON and CSV formats

**Props:**
```typescript
interface AdvancedForensicsPanelProps {
  incidentId: string              // Incident ID to analyze
  onClose?: () => void            // Callback when closing panel
  onExport?: (format: 'json' | 'pdf' | 'csv') => void  // Custom export handler
}
```

#### 2. **ForensicsTimeline** (`ForensicsTimeline.tsx`)
Interactive vertical timeline visualization that:
- Displays incident events chronologically
- Uses severity-based color coding
- Shows evidence references and action details
- Supports event expansion for detailed inspection

**Props:**
```typescript
interface ForensicsTimelineProps {
  events: TimelineEntry[]                    // Events to display
  onSelectEvent?: (event: TimelineEntry) => void  // Event selection callback
  compact?: boolean                          // Compact rendering mode
}
```

#### 3. **EvidenceBrowser** (`EvidenceBrowser.tsx`)
Advanced artifact browser featuring:
- Sortable evidence table (by type, source, size, collection time)
- Multi-select capability for batch operations
- Cryptographic hash display and verification status
- Chain-of-custody tracking
- Expandable rows for detailed evidence inspection

**Props:**
```typescript
interface EvidenceBrowserProps {
  evidence: EvidenceItem[]                   // Evidence/artifacts to browse
  onSelectEvidence?: (evidence: EvidenceItem) => void  // Selection callback
  onExport?: (evidence: EvidenceItem[]) => void      // Batch export handler
  showChainOfCustody?: boolean               // Show custody chain details
}
```

## Integration with Backend APIs

### Forensics API Endpoints

The panel integrates with these backend endpoints:

#### 1. List Forensics Records for Incident
```
GET /forensics/incidents/{incident_id}/forensics
Query Parameters:
  - status: Optional filter by status (open, closed, archived)

Response:
{
  "incident_id": string,
  "status_filter": string | null,
  "count": number,
  "records": {
    "record": ForensicsRecord,
    "txid": string,
    "timestamp": string
  }[]
}
```

#### 2. Store Forensics Record
```
POST /forensics/store
Request:
{
  "record": ForensicsRecord,
  "signature": string (hex-encoded),  // Optional
  "signer_cert_pem": string           // Optional
}

Response:
{
  "status": "stored",
  "record_id": string,
  "txid": string,
  "timestamp": string
}
```

#### 3. Verify Forensics Signature
```
POST /forensics/verify
Request:
{
  "txid": string,           // Optional: transaction ID on ledger
  "record": Record,         // Optional: direct record
  "signature": string,      // Optional: hex-encoded signature
  "signer_cert_pem": string // Optional: PEM certificate
}

Response:
{
  "verified": boolean | null,
  "reason": string,
  "signer": string | null,
  "txid": string | null
}
```

#### 4. Retrieve Forensics Record by ID
```
GET /forensics/records/{record_id}

Response:
{
  "status": "found",
  "source": "ledger" | "web3" | "fabric",
  "record": ForensicsRecord,
  "txid": string,
  "timestamp": string
}
```

## Data Models

### ForensicReport
```typescript
interface ForensicReport {
  id: string
  reportId: string
  incidentMetadata: IncidentMetadata
  executiveSummary: string
  timelineOfEvents: TimelineEntry[]
  findings: ForensicFinding[]
  recommendations: string[]
  evidenceInventory: EvidenceItem[]
  generatedAt: string
  generatedBy: string
  version: string
  classification: 'public' | 'internal' | 'confidential' | 'restricted'
}
```

### TimelineEntry
```typescript
interface TimelineEntry {
  timestamp: string
  tick?: number
  event: string
  actor: string
  severity: IncidentSeverity
  evidence: string[]
  action?: IncidentAction
}
```

### EvidenceItem
```typescript
interface EvidenceItem {
  id: string
  hash: string                                              // SHA-256, BLAKE3, or SHA512
  hashAlgorithm: 'SHA256' | 'BLAKE3' | 'SHA512'
  type: 'log' | 'trace' | 'snapshot' | 'configuration' | 'traffic' | 'other'
  size: number                                              // bytes
  collectedAt: string                                       // ISO timestamp
  source: string                                            // file path or source identifier
  integrityVerified: boolean                               // hash verification status
  chainOfCustodyLog: string[]                              // custody chain timestamps
}
```

## Usage Example

### Basic Integration

```tsx
import { AdvancedForensicsPanel } from './components/AdvancedForensicsPanel'

export function IncidentAnalysis() {
  const [selectedIncident, setSelectedIncident] = useState<string | null>(null)

  return (
    <div className="h-screen flex flex-col">
      <header className="p-4 border-b">
        <h1>Incident Investigation</h1>
      </header>
      
      <main className="flex-1 overflow-hidden">
        {selectedIncident ? (
          <AdvancedForensicsPanel
            incidentId={selectedIncident}
            onClose={() => setSelectedIncident(null)}
            onExport={(format) => {
              // Handle custom export logic
              console.log(`Exporting as ${format}`)
            }}
          />
        ) : (
          <div className="p-8">Select an incident to analyze</div>
        )}
      </main>
    </div>
  )
}
```

### With Real-time Updates

```tsx
import { useEffect, useState } from 'react'
import { AdvancedForensicsPanel } from './components/AdvancedForensicsPanel'

export function LiveForensicsMonitor({ incidentId }: { incidentId: string }) {
  const [refreshKey, setRefreshKey] = useState(0)

  useEffect(() => {
    // Poll for updates every 30 seconds
    const interval = setInterval(() => {
      setRefreshKey(k => k + 1)
    }, 30000)

    return () => clearInterval(interval)
  }, [])

  return (
    <AdvancedForensicsPanel
      key={refreshKey}
      incidentId={incidentId}
      onExport={(format) => {
        const timestamp = new Date().toISOString()
        const filename = `forensics-${incidentId}-${timestamp}.${format}`
        // Implement download logic
      }}
    />
  )
}
```

## Advanced Features

### 1. Filtering & Search

The panel supports:
- **Timeline search**: Search by event description or actor
- **Severity filtering**: Show only critical/high/medium/low events
- **Evidence filtering**: Filter by artifact type (log, trace, snapshot, etc.)
- **Date range filtering**: Built-in for evidence collection time

### 2. Evidence Chain of Custody

Evidence items include `chainOfCustodyLog` which tracks:
- Collection timestamps
- Handler information
- Verification checkpoints

The browser displays this chain when evidence is expanded.

### 3. Signature Verification

The verification view:
- Integrates with post-quantum cryptography (Dilithium)
- Supports verification against multiple blockchain sources
- Displays signer certificate information
- Shows verification timestamps and methods

### 4. Multi-Source Data

The backend forensics API can aggregate data from:
- **LedgerManager**: In-memory Hyperledger Fabric transaction ledger
- **Web3.py**: Ethereum/Web3 blockchain sources
- **Hyperledger Fabric**: Direct chaincode queries

The panel transparently handles source resolution.

## Performance Considerations

### Large Datasets

For incidents with thousands of events:
1. Enable `compact` mode in ForensicsTimeline
2. Implement pagination in the backend API
3. Use filtering to reduce visible items
4. Consider lazy-loading evidence details

### Memory Optimization

```tsx
// Use useMemo for expensive filtering operations
const filteredEvents = useMemo(() => {
  return events.filter(e => {
    // Complex filter logic
  })
}, [events, filterCriteria])
```

## Security Best Practices

1. **Signature Verification**: Always verify forensics records when imported from external sources
2. **Evidence Integrity**: Check hash verification status before relying on evidence
3. **Chain of Custody**: Review the complete chain of custody for critical evidence
4. **Classification Levels**: Respect report classification when exporting data
5. **Access Control**: Implement backend authorization checks on forensics endpoints

## Theming & Customization

The panel uses Tailwind CSS with a dark theme optimized for security dashboards:
- Primary color: Cyan (`cyan-500`)
- Severity colors: Red (critical), Orange (high), Amber (medium), Emerald (low)
- Background: Dark slate (`slate-900` to `slate-800`)
- Borders: Subtle with hover effects

To customize, modify the className props throughout the components.

## Troubleshooting

### Panel shows "No forensics data available"
- Verify incident exists in backend
- Check if forensics records have been stored via `/forensics/store`
- Ensure incident ID is correct

### Evidence hash verification shows "Unverified"
- Backend may not have calculated/stored hash
- Check `integrityVerified` flag in EvidenceItem
- Consider requesting hash calculation from evidence collector

### Timeline events not showing
- Verify `timelineOfEvents` array is populated in ForensicsRecord
- Check if events have valid timestamps
- Filter criteria may be hiding events (check severity filter)

### Signature verification fails
- Verify certificate is provided in `signer_cert_pem`
- Check signature hex format
- Ensure post-quantum cryptography library is configured
- Review signer certificate expiration

## Future Enhancements

1. **Real-time WebSocket updates** for live incident monitoring
2. **Automated threat correlation** across evidence
3. **Machine learning-based** root cause analysis
4. **Advanced visualizations**: Attack flow diagrams, network graphs
5. **Collaborative annotations** on evidence
6. **Automated playbook execution** for remediation
7. **Integration with SOAR platforms** for orchestration

## Related Documentation

- [Backend Forensics API](../../backend/api/routes/forensics.py)
- [Forensics Types](../types/forensics.types.ts)
- [LedgerManager Documentation](../../backend/core/blockchain_xdr/README.md)
- [Post-Quantum Cryptography](../../backend/core/pqcrypto/README.md)
