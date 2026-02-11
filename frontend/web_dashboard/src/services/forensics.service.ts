import { apiClient } from '../utils/api'
import {
  ForensicsAuditLog,
  BlockchainTransaction,
  LedgerEntry,
  PaginatedResponse,
} from '../types/index'
import {
  ListForensicReportsRequest,
  ListForensicReportsResponse,
  GetPublicKeysResponse,
  VerifyForensicSignatureResponse,
} from '../types/forensics.types'

/**
 * Forensics Service
 * Handles ledger reads and signed reports from blockchain
 * Connects to backend/api/forensics.py which calls blockchain_xdr/ledger_manager.py
 */
class ForensicsService {
  /**
   * Fetch audit logs with pagination
   */
  async getAuditLogs(options: {
    page?: number
    pageSize?: number
    actor?: string
    resource?: string
    startDate?: string
    endDate?: string
  } = {}): Promise<PaginatedResponse<ForensicsAuditLog>> {
    try {
      const params = new URLSearchParams()

      if (options.page) params.append('page', String(options.page))
      if (options.pageSize) params.append('pageSize', String(options.pageSize))
      if (options.actor) params.append('actor', options.actor)
      if (options.resource) params.append('resource', options.resource)
      if (options.startDate) params.append('startDate', options.startDate)
      if (options.endDate) params.append('endDate', options.endDate)

      const response = await apiClient.get<PaginatedResponse<ForensicsAuditLog>>(
        `/api/forensics/audit-logs?${params}`
      )

      return response.data
    } catch (error) {
      console.error('Failed to fetch audit logs:', error)
      throw error
    }
  }

  /**
   * Get specific audit log entry
   */
  async getAuditLogEntry(id: string): Promise<ForensicsAuditLog> {
    try {
      const response = await apiClient.get<ForensicsAuditLog>(
        `/api/forensics/audit-logs/${id}`
      )

      return response.data
    } catch (error) {
      console.error('Failed to fetch audit log entry:', error)
      throw error
    }
  }

  /**
   * Search audit logs by criteria
   */
  async searchAuditLogs(query: {
    text?: string
    severity?: string
    action?: string
    timeRange?: {
      start: string
      end: string
    }
  }): Promise<ForensicsAuditLog[]> {
    try {
      const response = await apiClient.post<ForensicsAuditLog[]>(
        '/api/forensics/audit-logs/search',
        query
      )

      return response.data
    } catch (error) {
      console.error('Failed to search audit logs:', error)
      throw error
    }
  }

  /**
   * Get blockchain transactions
   */
  async getBlockchainTransactions(options: {
    page?: number
    pageSize?: number
    source?: string
    destination?: string
    status?: 'pending' | 'confirmed' | 'failed'
  } = {}): Promise<PaginatedResponse<BlockchainTransaction>> {
    try {
      const params = new URLSearchParams()

      if (options.page) params.append('page', String(options.page))
      if (options.pageSize) params.append('pageSize', String(options.pageSize))
      if (options.source) params.append('source', options.source)
      if (options.destination) params.append('destination', options.destination)
      if (options.status) params.append('status', options.status)

      const response = await apiClient.get<PaginatedResponse<BlockchainTransaction>>(
        `/api/forensics/blockchain/transactions?${params}`
      )

      return response.data
    } catch (error) {
      console.error('Failed to fetch blockchain transactions:', error)
      throw error
    }
  }

  /**
   * Get specific blockchain transaction
   */
  async getBlockchainTransaction(id: string): Promise<BlockchainTransaction> {
    try {
      const response = await apiClient.get<BlockchainTransaction>(
        `/api/forensics/blockchain/transactions/${id}`
      )

      return response.data
    } catch (error) {
      console.error('Failed to fetch blockchain transaction:', error)
      throw error
    }
  }

  /**
   * Get ledger entries for a specific channel
   */
  async getLedgerEntries(
    channel: string,
    options: { page?: number; pageSize?: number } = {}
  ): Promise<PaginatedResponse<LedgerEntry>> {
    try {
      const params = new URLSearchParams()

      if (options.page) params.append('page', String(options.page))
      if (options.pageSize) params.append('pageSize', String(options.pageSize))

      const response = await apiClient.get<PaginatedResponse<LedgerEntry>>(
        `/api/forensics/ledger/${channel}?${params}`
      )

      return response.data
    } catch (error) {
      console.error('Failed to fetch ledger entries:', error)
      throw error
    }
  }

  /**
   * Verify ledger entry integrity
   */
  async verifyLedgerEntry(entryId: string): Promise<{ valid: boolean; proof: string }> {
    try {
      const response = await apiClient.get<{ valid: boolean; proof: string }>(
        `/api/forensics/ledger/verify/${entryId}`
      )

      return response.data
    } catch (error) {
      console.error('Failed to verify ledger entry:', error)
      throw error
    }
  }

  /**
   * Generate forensics report
   */
  async generateReport(options: {
    type: 'incident' | 'compliance' | 'audit' | 'investigation'
    startDate: string
    endDate: string
    scope?: string[]
    includeLedger?: boolean
  }): Promise<{ reportId: string; status: string; url: string }> {
    try {
      const response = await apiClient.post<{
        reportId: string
        status: string
        url: string
      }>('/api/forensics/reports/generate', options)

      return response.data
    } catch (error) {
      console.error('Failed to generate forensics report:', error)
      throw error
    }
  }

  /**
   * Get generated report
   */
  async getReport(reportId: string): Promise<Blob> {
    try {
      const response = await apiClient.getInstance().get(
        `/api/forensics/reports/${reportId}`,
        { responseType: 'blob' }
      )

      return response.data
    } catch (error) {
      console.error('Failed to fetch forensics report:', error)
      throw error
    }
  }

  /**
   * Get blockchain ledger metadata
   */
  async getLedgerMetadata(channel: string): Promise<{
    channel: string
    height: number
    latestBlockHash: string
    previousBlockHash: string
    timestamp: string
  }> {
    try {
      const response = await apiClient.get<{
        channel: string
        height: number
        latestBlockHash: string
        previousBlockHash: string
        timestamp: string
      }>(`/api/forensics/ledger/${channel}/metadata`)

      return response.data
    } catch (error) {
      console.error('Failed to fetch ledger metadata:', error)
      throw error
    }
  }

  /**
   * Export audit trail
   */
  async exportAuditTrail(options: {
    format: 'csv' | 'json' | 'pdf'
    filters: {
      actor?: string
      action?: string
      startDate?: string
      endDate?: string
    }
  }): Promise<Blob> {
    try {
      const response = await apiClient.getInstance().post(
        '/api/forensics/export/audit-trail',
        options,
        { responseType: 'blob' }
      )

      return response.data
    } catch (error) {
      console.error('Failed to export audit trail:', error)
      throw error
    }
  }

  /**
   * Get public keys used to verify forensic signatures
   */
  async getPublicKeys(): Promise<GetPublicKeysResponse> {
    try {
      const response = await apiClient.get<GetPublicKeysResponse>('/api/forensics/keys/public')

      return response.data
    } catch (error) {
      console.error('Failed to fetch public keys for forensics:', error)
      throw error
    }
  }

  /**
   * Verify a forensic report signature via backend
   */
  async verifyForensicSignature(
    body: { reportId: string; signature: string; publicKey?: string }
  ): Promise<VerifyForensicSignatureResponse> {
    try {
      const response = await apiClient.post<VerifyForensicSignatureResponse>('/api/forensics/verify', body)

      return response.data
    } catch (error) {
      console.error('Failed to verify forensic signature:', error)
      throw error
    }
  }

  /**
   * List forensic report summaries (paginated)
   */
  async listReports(options: ListForensicReportsRequest = {}): Promise<ListForensicReportsResponse> {
    try {
      const params = new URLSearchParams()

      if (options.limit) params.append('limit', String(options.limit))
      if (options.offset) params.append('offset', String(options.offset))
      if (options.sortBy) params.append('sortBy', options.sortBy)
      if (options.sortOrder) params.append('sortOrder', options.sortOrder)
      if (options.filter) params.append('filter', JSON.stringify(options.filter))

      const response = await apiClient.get<ListForensicReportsResponse>(
        `/api/forensics/reports?${params}`
      )

      return response.data
    } catch (error) {
      console.error('Failed to list forensic reports:', error)
      throw error
    }
  }

  /**
   * Get forensics statistics for dashboard
   */
  async getForensicsStats(): Promise<{
    attackSurface: number
    vulnerabilities: number
    detectionRate: number
    lastUpdated: string
  }> {
    try {
      const response = await apiClient.get<{
        attackSurface: number
        vulnerabilities: number
        detectionRate: number
        lastUpdated: string
      }>('/api/forensics/stats')

      return response.data
    } catch (error) {
      console.error('Failed to fetch forensics stats:', error)
      throw error
    }
  }

  /**
   * Get evidence inventory
   */
  async getEvidenceInventory(options: {
    status?: string
    limit?: number
    offset?: number
  } = {}): Promise<{
    data: Array<{
      id: string
      type: string
      hash: string
      collected_at: string
      status: string
      size: number
      source: string
    }>
    total: number
  }> {
    try {
      const params = new URLSearchParams()

      if (options.status) params.append('status', options.status)
      if (options.limit) params.append('limit', String(options.limit || 50))
      if (options.offset) params.append('offset', String(options.offset || 0))

      const response = await apiClient.get<{
        data: Array<{
          id: string
          type: string
          hash: string
          collected_at: string
          status: string
          size: number
          source: string
        }>
        total: number
      }>(`/api/forensics/evidence?${params}`)

      return response.data
    } catch (error) {
      console.error('Failed to fetch evidence inventory:', error)
      throw error
    }
  }

  /**
   * Analyze evidence
   */
  async analyzeEvidence(
    evidenceId: string,
    analysisType: 'cryptographic' | 'pattern' | 'anomaly' | 'malware'
  ): Promise<{
    evidenceId: string
    analysisType: string
    findings: Array<{
      finding_type: string
      description: string
      confidence: number
    }>
    riskScore: number
    completedAt: string
  }> {
    try {
      const response = await apiClient.post<{
        evidenceId: string
        analysisType: string
        findings: Array<{
          finding_type: string
          description: string
          confidence: number
        }>
        riskScore: number
        completedAt: string
      }>('/api/forensics/evidence/analyze', {
        evidence_id: evidenceId,
        analysis_type: analysisType,
      })

      return response.data
    } catch (error) {
      console.error('Failed to analyze evidence:', error)
      throw error
    }
  }
}

// Export singleton instance
export default new ForensicsService()
