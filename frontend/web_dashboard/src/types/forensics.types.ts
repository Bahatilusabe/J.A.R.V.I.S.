// ============================================================================
// FORENSICS & INCIDENT RESPONSE TYPES
// ============================================================================

// ============================================================================
// SIGNATURE TYPES (DILITHIUM POST-QUANTUM CRYPTOGRAPHY)
// ============================================================================

export interface DilithiumPublicKey {
  keyId: string;
  publicKey: string;
  algorithm: 'DILITHIUM_3' | 'DILITHIUM_5';
  generatedAt: string;
  expiresAt?: string;
  keyOwner: string;
}

export interface DilithiumSignature {
  signature: string;
  keyId: string;
  algorithm: 'DILITHIUM_3' | 'DILITHIUM_5';
  timestamp: string;
  signedBy: string;
}

export interface SignatureVerificationResult {
  valid: boolean;
  keyId: string;
  algorithm: 'DILITHIUM_3' | 'DILITHIUM_5';
  verifiedAt: string;
  publicKeyUsed: DilithiumPublicKey;
  errorMessage?: string;
  verificationMethod: 'client_side' | 'server_side' | 'hybrid';
  verificationTime: number; // milliseconds
}

// ============================================================================
// INCIDENT & ACTION TYPES
// ============================================================================

export type IncidentSeverity = 'low' | 'medium' | 'high' | 'critical' | 'catastrophic';
export type IncidentStatus = 'detected' | 'investigating' | 'contained' | 'resolved' | 'archived';
export type ActionType = 'detection' | 'isolation' | 'recovery' | 'verification' | 'remediation' | 'post_mortem';

export interface IncidentAction {
  id: string;
  timestamp: string;
  tick?: number;
  actionType: ActionType;
  description: string;
  performedBy: string;
  evidenceHashes: string[];
  result: 'success' | 'partial' | 'failed';
  details: Record<string, string | number | boolean>;
}

export interface TimelineEntry {
  timestamp: string;
  tick?: number;
  event: string;
  actor: string;
  severity: IncidentSeverity;
  evidence: string[];
  action?: IncidentAction;
}

export interface IncidentMetadata {
  id: string;
  incidentId: string;
  createdAt: string;
  detectedAt: string;
  containedAt?: string;
  resolvedAt?: string;
  status: IncidentStatus;
  severity: IncidentSeverity;
  affectedSystems: string[];
  affectedAgents: number;
  rootCauseDescription?: string;
  resolutionSummary?: string;
}

// ============================================================================
// FORENSIC REPORT TYPES
// ============================================================================

export interface EvidenceItem {
  id: string;
  hash: string; // SHA-256 or BLAKE3
  hashAlgorithm: 'SHA256' | 'BLAKE3' | 'SHA512';
  type: 'log' | 'trace' | 'snapshot' | 'configuration' | 'traffic' | 'other';
  size: number; // bytes
  collectedAt: string;
  source: string;
  integrityVerified: boolean;
  chainOfCustodyLog: string[];
}

export interface ForensicFinding {
  id: string;
  title: string;
  description: string;
  category: 'root_cause' | 'contributing_factor' | 'observable' | 'recommendation';
  severity: IncidentSeverity;
  evidence: EvidenceItem[];
  analysisDate: string;
  analystedBy: string;
}

export interface ForensicReport {
  id: string;
  reportId: string;
  incidentMetadata: IncidentMetadata;
  executiveSummary: string;
  timelineOfEvents: TimelineEntry[];
  findings: ForensicFinding[];
  recommendations: string[];
  evidenceInventory: EvidenceItem[];
  generatedAt: string;
  generatedBy: string;
  version: string;
  classification: 'public' | 'internal' | 'confidential' | 'restricted';
}

export interface SignedForensicReport {
  report: ForensicReport;
  signature: DilithiumSignature;
}

// ============================================================================
// FORENSIC REPORT METADATA (FOR LISTS & SUMMARIES)
// ============================================================================

export interface ForensicReportSummary {
  id: string;
  reportId: string;
  incidentId: string;
  title: string;
  status: IncidentStatus;
  severity: IncidentSeverity;
  detectedAt: string;
  generatedAt: string;
  generatedBy: string;
  affectedSystems: number;
  affectedAgents: number;
  findingsCount: number;
  evidenceCount: number;
  isSigned: boolean;
  signatureValid: boolean;
  classification: 'public' | 'internal' | 'confidential' | 'restricted';
}

// ============================================================================
// FORENSIC REPORT FILTERING & SEARCHING
// ============================================================================

export interface ForensicReportFilter {
  status?: IncidentStatus[];
  severity?: IncidentSeverity[];
  dateRange?: {
    start: string;
    end: string;
  };
  classification?: string[];
  searchText?: string;
}

// ============================================================================
// API REQUEST/RESPONSE TYPES
// ============================================================================

export interface ListForensicReportsRequest {
  limit?: number;
  offset?: number;
  filter?: ForensicReportFilter;
  sortBy?: 'date' | 'severity' | 'status';
  sortOrder?: 'asc' | 'desc';
}

export interface ListForensicReportsResponse {
  reports: ForensicReportSummary[];
  total: number;
  limit: number;
  offset: number;
  timestamp: string;
}

export interface GetForensicReportResponse {
  signedReport: SignedForensicReport;
  publicKeyUsed?: DilithiumPublicKey;
}

export interface VerifyForensicSignatureRequest {
  reportId: string;
  signature: string;
  publicKey?: string; // Optional, backend can look up
}

export interface VerifyForensicSignatureResponse {
  verified: boolean;
  verificationResult: SignatureVerificationResult;
  reportId: string;
  timestamp: string;
}

export interface GetPublicKeysResponse {
  keys: DilithiumPublicKey[];
  timestamp: string;
}

// ============================================================================
// REPORT PARSING & DISPLAY TYPES
// ============================================================================

export interface ReportSection {
  title: string;
  content: string | Record<string, unknown>;
  collapsed: boolean;
}

export interface PDFReportMetadata {
  fileName: string;
  fileSize: number;
  pages: number;
  generatedAt: string;
  downloadUrl: string;
  contentType: 'application/pdf';
}

// ============================================================================
// UI STATE TYPES
// ============================================================================

export interface ForensicsUIState {
  // Report List
  selectedReports: string[];
  expandedReportId?: string;
  reportListFilter: ForensicReportFilter;
  reportListSort: {
    field: 'date' | 'severity' | 'status';
    order: 'asc' | 'desc';
  };

  // Report Viewer
  viewingReportId?: string;
  viewerTab: 'summary' | 'timeline' | 'findings' | 'evidence' | 'pdf';
  pdfViewerPage: number;
  pdfViewerZoom: number;

  // Signature Verification
  verificationInProgress: boolean;
  verificationResults: Record<string, SignatureVerificationResult>;
  showSignatureDetails: boolean;

  // Timeline
  timelineExpanded: Record<string, boolean>;
  timelineFilter: {
    severities: IncidentSeverity[];
    actionTypes: ActionType[];
    dateRange?: {
      start: string;
      end: string;
    };
  };

  // UI
  isLoading: boolean;
  error?: string;
  successMessage?: string;
}

// ============================================================================
// COMPLETE STATE SHAPE
// ============================================================================

export interface ForensicsState {
  // Data
  reports: ForensicReportSummary[];
  currentReport?: SignedForensicReport;
  publicKeys: DilithiumPublicKey[];

  // Operations
  totalReports: number;
  isLoadingReports: boolean;
  isLoadingCurrentReport: boolean;

  // UI
  ui: ForensicsUIState;

  // Metadata
  lastUpdated: string;
  cacheExpiry?: string;
}
