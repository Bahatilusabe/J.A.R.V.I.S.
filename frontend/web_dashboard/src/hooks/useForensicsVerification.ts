import { useCallback, useEffect, useRef, useState } from 'react'
import forensicsService from '../services/forensics.service'
import {
  DilithiumPublicKey,
  VerifyForensicSignatureRequest,
  VerifyForensicSignatureResponse,
  GetPublicKeysResponse,
} from '../types/forensics.types'

/**
 * Hook: useForensicsVerification
 * - centralizes GET /forensics/keys/public and POST /forensics/verify
 * - caches public keys for a short TTL to avoid refetching
 * - exposes verify(reportId, signature, publicKey?) => result
 */
export function useForensicsVerification(opts?: { keysTtlMs?: number }) {
  const ttl = opts?.keysTtlMs ?? 5 * 60 * 1000 // default 5 minutes

  const [publicKeys, setPublicKeys] = useState<DilithiumPublicKey[] | null>(null)
  const [isLoadingKeys, setIsLoadingKeys] = useState(false)
  const [isVerifying, setIsVerifying] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // cache timestamp
  const fetchedAtRef = useRef<number | null>(null)

  const fetchPublicKeys = useCallback(async (force = false) => {
    try {
      if (!force && publicKeys && fetchedAtRef.current && Date.now() - fetchedAtRef.current < ttl) {
        return publicKeys
      }

      setIsLoadingKeys(true)
      setError(null)
      const res: GetPublicKeysResponse = await forensicsService.getPublicKeys()
      setPublicKeys(res.keys)
      fetchedAtRef.current = Date.now()
      return res.keys
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err)
      setError(msg)
      throw err
    } finally {
      setIsLoadingKeys(false)
    }
  }, [publicKeys, ttl])

  const verify = useCallback(async (req: VerifyForensicSignatureRequest) => {
    try {
      setIsVerifying(true)
      setError(null)

      const res: VerifyForensicSignatureResponse = await forensicsService.verifyForensicSignature(req)

      return res
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err)
      setError(msg)
      throw err
    } finally {
      setIsVerifying(false)
    }
  }, [])

  useEffect(() => {
    // eager load keys on mount (non-blocking)
    fetchPublicKeys().catch(() => {})
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return {
    publicKeys,
    fetchPublicKeys,
    verify,
    isLoadingKeys,
    isVerifying,
    error,
  }
}

export default useForensicsVerification
