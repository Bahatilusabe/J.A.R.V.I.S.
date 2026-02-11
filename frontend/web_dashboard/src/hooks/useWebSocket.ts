// Lightweight stub for useWebSocket used by several pages during type-only iteration
import { useState, useEffect } from 'react'

export function useWebSocket(_url: string) {
  const [message, _setMessage] = useState<unknown>(null)

  useEffect(() => {
    // No-op stub: real implementation lives in hooks repo or will be added later.
    return () => { }
  }, [_url])

  const send = (_payload?: unknown) => {
    // no-op
    void _payload
  }

  return { send, message }
}
