import React, { useEffect, useState, useCallback } from 'react'
import type {
  SignedForensicReport,
  VerifyForensicSignatureResponse,
  DilithiumPublicKey,
} from '../types/forensics.types'
import SignatureVerifier from './SignatureVerifier'

interface ForensicReportViewerProps {
  reportId: string
  onClose?: () => void
}

/**
 * ForensicReportViewer
 * - Fetches signed report JSON from GET /forensics/{id}
 * - Displays a PDF embed (GET /forensics/{id}/pdf)
 * - Shows structured JSON (executive summary, timeline, findings)
 * - Integrates SignatureVerifier which calls POST /forensics/verify
 */
export const ForensicReportViewer: React.FC<ForensicReportViewerProps> = ({
  reportId,
  onClose,
}) => {
  const [signedReport, setSignedReport] = useState<SignedForensicReport | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isVerifying, setIsVerifying] = useState(false)
  const [verificationResult, setVerificationResult] = useState<VerifyForensicSignatureResponse | null>(null)
  const [publicKey, setPublicKey] = useState<DilithiumPublicKey | undefined>(undefined)

  const apiBase = process.env.REACT_APP_API_URL || 'http://localhost:8000'
  const reportUrl = `${apiBase}/forensics/${reportId}`
  const pdfUrl = `${reportUrl}/pdf`

  const fetchReport = useCallback(async () => {
    try {
      setIsLoading(true)
      setError(null)
      const res = await fetch(reportUrl, { credentials: 'include' })
      if (!res.ok) throw new Error(`Failed to fetch report: ${res.statusText}`)
      const data = await res.json()
      setSignedReport(data.signedReport)

      // Try to fetch public keys and set the one referenced by the signature
      try {
        const keyRes = await fetch(`${apiBase}/keys/public`, { credentials: 'include' })
        if (keyRes.ok) {
          const keyData = await keyRes.json()
          const keys: DilithiumPublicKey[] = keyData.keys || []
          const keyId = data.signedReport.signature?.keyId
          const found = keys.find((k) => k.keyId === keyId)
          if (found) setPublicKey(found)
        }
      } catch (kerr) {
        // non-fatal
        console.warn('Failed to fetch public keys', kerr)
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err)
      setError(msg)
    } finally {
      setIsLoading(false)
    }
  }, [reportUrl, apiBase])

  useEffect(() => {
    fetchReport()
  }, [fetchReport])

  const handleVerify = useCallback(async () => {
    if (!signedReport) return
    try {
      setIsVerifying(true)
      setError(null)

      const payload = {
        reportId: signedReport.report.reportId,
        signature: signedReport.signature.signature,
      }

      const res = await fetch(`${apiBase}/forensics/verify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        credentials: 'include',
      })

      if (!res.ok) throw new Error(`Verification API error: ${res.statusText}`)
      const data: VerifyForensicSignatureResponse = await res.json()
      setVerificationResult(data)
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err)
      setError(msg)
    } finally {
      setIsVerifying(false)
    }
  }, [signedReport, apiBase])

  if (isLoading) {
    return (
      <div className="p-6 bg-white border rounded">
        <div className="text-sm text-slate-600">Loading report...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-6 bg-white border rounded">
        <div className="text-sm text-red-600">{error}</div>
      </div>
    )
  }

  if (!signedReport) {
    return (
      <div className="p-6 bg-white border rounded">
        <div className="text-sm text-slate-600">No report available</div>
      </div>
    )
  }

  const { report, signature } = signedReport

  return (
    <div className="flex flex-col h-full bg-white rounded border border-slate-200">
      <div className="flex items-center justify-between p-4 border-b">
        <div>
          <div className="text-sm font-semibold text-slate-900">{report.incidentMetadata.incidentId}</div>
          <div className="text-xs text-slate-500">Report: {report.reportId}</div>
        </div>
        <div className="flex items-center gap-2">
          <a href={pdfUrl} target="_blank" rel="noreferrer" className="text-sm text-sky-600">Open PDF</a>
          <button
            onClick={() => fetchReport()}
            className="px-3 py-1 bg-slate-50 border rounded text-sm text-slate-700"
          >
            Refresh
          </button>
          {onClose && (
            <button
              onClick={onClose}
              className="px-3 py-1 bg-red-50 border rounded text-sm text-red-700"
            >
              Close
            </button>
          )}
        </div>
      </div>

      <div className="flex-1 flex gap-4 p-4 overflow-hidden">
        {/* Left: PDF viewer (iframe fallback) */}
        <div className="w-2/3 h-full border rounded overflow-hidden">
          <iframe
            title={`forensic-pdf-${report.reportId}`}
            src={pdfUrl}
            className="w-full h-full"
          />
        </div>

        {/* Right: Structured report + signature verification */}
        <div className="w-1/3 h-full overflow-auto">
          <div className="p-3">
            <div className="mb-3">
              <div className="text-xs text-slate-500">Executive Summary</div>
              <div className="text-sm text-slate-800 mt-1">{report.executiveSummary || '—'}</div>
            </div>

            <div className="mb-3">
              <div className="text-xs text-slate-500">Metadata</div>
              <div className="text-sm text-slate-800 mt-1">
                <div>Severity: <strong>{report.incidentMetadata.severity}</strong></div>
                <div>Status: <strong>{report.incidentMetadata.status}</strong></div>
                <div>Detected: <strong>{report.incidentMetadata.detectedAt}</strong></div>
                <div>Generated: <strong>{report.generatedAt}</strong></div>
              </div>
            </div>

            <div className="mb-3">
              <div className="text-xs text-slate-500">Signature</div>
              <div className="mt-2">
                <SignatureVerifier
                  signature={signature.signature}
                  publicKey={
                    publicKey || {
                      keyId: signature.keyId,
                      publicKey: '',
                      algorithm: signature.algorithm,
                      generatedAt: '',
                      keyOwner: '',
                    }
                  }
                  isVerifying={isVerifying}
                  verificationResult={verificationResult?.verificationResult}
                  onVerify={handleVerify}
                />
              </div>
            </div>

            <div className="mb-3">
              <div className="text-xs text-slate-500">Timeline (last 5)</div>
              <div className="mt-2 text-sm text-slate-700">
                {report.timelineOfEvents.slice(0,5).map((t, i) => (
                  <div key={i} className="mb-2">
                    <div className="font-medium">{t.event}</div>
                    <div className="text-xs text-slate-500">{t.timestamp} • {t.actor}</div>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <div className="text-xs text-slate-500">Findings</div>
              <div className="mt-2 text-sm text-slate-700">
                {report.findings.length === 0 && <div className="text-sm text-slate-500">No findings</div>}
                {report.findings.map((f) => (
                  <div key={f.id} className="mb-2 border-l-2 pl-2 border-slate-100">
                    <div className="font-medium">{f.title}</div>
                    <div className="text-xs text-slate-500">{f.category} • {f.severity}</div>
                    <div className="text-sm mt-1 text-slate-700">{f.description}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ForensicReportViewer
