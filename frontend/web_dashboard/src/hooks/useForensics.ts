import { useState, useCallback } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import forensicsService from '../services/forensics.service'
import {
  ForensicsAuditLog,
  BlockchainTransaction,
  LedgerEntry,
  PaginatedResponse,
} from '../types/index'
import { ForensicReportSummary, ListForensicReportsRequest, ListForensicReportsResponse } from '../types/forensics.types'
import { RootState } from '../store/index'

interface UseForensicsReturn {
  reports: ForensicReportSummary[] | null
  auditLogs: PaginatedResponse<ForensicsAuditLog> | null
  transactions: PaginatedResponse<BlockchainTransaction> | null
  ledgerEntries: PaginatedResponse<LedgerEntry> | null
  currentPage: number
  isLoading: boolean
  error: string | null
  getReports: (opts?: ListForensicReportsRequest) => Promise<void>
  getAuditLogs: (page?: number, pageSize?: number) => Promise<void>
  searchAuditLogs: (query: Record<string, unknown>) => Promise<void>
  getBlockchainTransactions: (page?: number, pageSize?: number) => Promise<void>
  getLedgerEntries: (channel: string, page?: number, pageSize?: number) => Promise<void>
  verifyLedgerEntry: (entryId: string) => Promise<void>
  generateReport: (options: Record<string, unknown>) => Promise<void>
  exportAuditTrail: (format: 'csv' | 'json' | 'pdf') => Promise<void>
  clearError: () => void
}

/**
 * Hook for forensics and blockchain data
 * Manages audit logs, transactions, and ledger entries
 * Provides report generation and export capabilities
 */
export function useForensics(): UseForensicsReturn {
  const dispatch = useDispatch()
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [currentPage, setCurrentPage] = useState(1)

  // Get forensics state from Redux
  const forensicsState = useSelector((state: RootState) => state.forensics)
  const auditLogs = forensicsState?.auditLogs || null
  const transactions = forensicsState?.transactions || null
  const ledgerEntries = forensicsState?.ledgerEntries || null
  const reports = forensicsState?.reports || null

  /**
   * Fetch audit logs with pagination
   */
  const getAuditLogs = useCallback(
    async (page = 1, pageSize = 20) => {
      try {
        setIsLoading(true)
        setError(null)
        setCurrentPage(page)

        const response = await forensicsService.getAuditLogs({
          page,
          pageSize,
        })

        // Dispatch to Redux store
        dispatch({
          type: 'forensics/auditLogsFetched',
          payload: response,
        })
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to fetch audit logs'
        setError(message)
        throw err
      } finally {
        setIsLoading(false)
      }
    },
    [dispatch]
  )

    /**
     * Fetch forensic report summaries (list) and store in Redux
     */
    const getReports = useCallback(
      async (opts: ListForensicReportsRequest = {}) => {
        try {
          setIsLoading(true)
          setError(null)

          const response: ListForensicReportsResponse = await forensicsService.listReports(opts)

          // Dispatch to Redux store
          dispatch({
            type: 'forensics/reportsFetched',
            payload: response,
          })
        } catch (err) {
          const message = err instanceof Error ? err.message : 'Failed to fetch forensic reports'
          setError(message)
          throw err
        } finally {
          setIsLoading(false)
        }
      },
      [dispatch]
    )

  /**
   * Search audit logs
   */
  const searchAuditLogs = useCallback(
    async (query: Record<string, unknown>) => {
      try {
        setIsLoading(true)
        setError(null)
        setCurrentPage(1)

        const results = await forensicsService.searchAuditLogs(query)

        // Dispatch to Redux store
        dispatch({
          type: 'forensics/auditLogsSearched',
          payload: results,
        })
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to search audit logs'
        setError(message)
        throw err
      } finally {
        setIsLoading(false)
      }
    },
    [dispatch]
  )

  /**
   * Fetch blockchain transactions
   */
  const getBlockchainTransactions = useCallback(
    async (page = 1, pageSize = 20) => {
      try {
        setIsLoading(true)
        setError(null)
        setCurrentPage(page)

        const response = await forensicsService.getBlockchainTransactions({
          page,
          pageSize,
        })

        // Dispatch to Redux store
        dispatch({
          type: 'forensics/transactionsFetched',
          payload: response,
        })
      } catch (err) {
        const message =
          err instanceof Error ? err.message : 'Failed to fetch blockchain transactions'
        setError(message)
        throw err
      } finally {
        setIsLoading(false)
      }
    },
    [dispatch]
  )

  /**
   * Fetch ledger entries
   */
  const getLedgerEntries = useCallback(
    async (channel: string, page = 1, pageSize = 20) => {
      try {
        setIsLoading(true)
        setError(null)
        setCurrentPage(page)

        const response = await forensicsService.getLedgerEntries(channel, {
          page,
          pageSize,
        })

        // Dispatch to Redux store
        dispatch({
          type: 'forensics/ledgerEntriesFetched',
          payload: response,
        })
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to fetch ledger entries'
        setError(message)
        throw err
      } finally {
        setIsLoading(false)
      }
    },
    [dispatch]
  )

  /**
   * Verify ledger entry integrity
   */
  const verifyLedgerEntry = useCallback(
    async (entryId: string) => {
      try {
        setIsLoading(true)
        setError(null)

        const result = await forensicsService.verifyLedgerEntry(entryId)

        // Dispatch to Redux store
        dispatch({
          type: 'forensics/ledgerEntryVerified',
          payload: { entryId, ...result },
        })
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to verify ledger entry'
        setError(message)
        throw err
      } finally {
        setIsLoading(false)
      }
    },
    [dispatch]
  )

  /**
   * Generate forensics report
   */
  const generateReport = useCallback(
    async (options: Record<string, unknown>) => {
      try {
        setIsLoading(true)
        setError(null)

        const report = await forensicsService.generateReport(
          options as Parameters<typeof forensicsService.generateReport>[0]
        )

        // Dispatch to Redux store
        dispatch({
          type: 'forensics/reportGenerated',
          payload: report,
        })
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to generate report'
        setError(message)
        throw err
      } finally {
        setIsLoading(false)
      }
    },
    [dispatch]
  )

  /**
   * Export audit trail as file
   */
  const exportAuditTrail = useCallback(
    async (format: 'csv' | 'json' | 'pdf') => {
      try {
        setIsLoading(true)
        setError(null)

        const blob = await forensicsService.exportAuditTrail({
          format,
          filters: {},
        })

        // Create download link
        const url = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = `audit-trail.${format}`
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        window.URL.revokeObjectURL(url)

        // Dispatch to Redux store
        dispatch({
          type: 'forensics/auditTrailExported',
          payload: { format, timestamp: new Date().toISOString() },
        })
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to export audit trail'
        setError(message)
        throw err
      } finally {
        setIsLoading(false)
      }
    },
    [dispatch]
  )

  /**
   * Clear error message
   */
  const clearError = useCallback(() => {
    setError(null)
  }, [])

  return {
    reports,
    auditLogs,
    transactions,
    ledgerEntries,
    currentPage,
    isLoading,
    error,
    getReports,
    getAuditLogs,
    searchAuditLogs,
    getBlockchainTransactions,
    getLedgerEntries,
    verifyLedgerEntry,
    generateReport,
    exportAuditTrail,
    clearError,
  }
}

export default useForensics
