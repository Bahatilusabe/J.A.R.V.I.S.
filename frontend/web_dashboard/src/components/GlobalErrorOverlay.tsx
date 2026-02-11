import { useEffect, useState } from 'react'

export default function GlobalErrorOverlay() {
  const [errorInfo, setErrorInfo] = useState<{ message: string; stack?: string } | null>(null)

  useEffect(() => {
    const onError = (ev: ErrorEvent) => {
      setErrorInfo({ message: ev.message || 'Unknown error', stack: ev.error?.stack })
      // keep original behavior
      console.error('[GlobalErrorOverlay] window.error', ev.error || ev.message)
    }

    const onRejection = (ev: PromiseRejectionEvent) => {
      const reason = ev.reason
      const message = (reason && (reason.message || String(reason))) || 'Unhandled Promise rejection'
      const stack = reason && reason.stack
      setErrorInfo({ message, stack })
      console.error('[GlobalErrorOverlay] unhandledrejection', reason)
    }

    window.addEventListener('error', onError)
    window.addEventListener('unhandledrejection', onRejection)

    return () => {
      window.removeEventListener('error', onError)
      window.removeEventListener('unhandledrejection', onRejection)
    }
  }, [])

  useEffect(() => {
    const handler = (err: { message: string; stack?: string }) => {
      setErrorInfo(err)
    }

      ; (window as any).__GLOBAL_ERROR_HOOK__ = handler

    return () => {
      try {
        delete (window as any).__GLOBAL_ERROR_HOOK__
      } catch (e) {
        ; (window as any).__GLOBAL_ERROR_HOOK__ = undefined
      }
    }
  }, [])

  if (!errorInfo) return null

  return (
    <div className="fixed inset-0 z-60 flex items-start justify-center pointer-events-none">
      <div className="mt-12 max-w-3xl w-full pointer-events-auto bg-red-900/95 border border-red-700 rounded-lg p-4 text-white shadow-2xl">
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="font-semibold text-lg">Application Error Detected</div>
            <div className="text-sm text-red-200 mt-1">{errorInfo.message}</div>
            {errorInfo.stack && (
              <pre className="mt-3 text-xs whitespace-pre-wrap max-h-64 overflow-auto text-red-100 bg-red-900/20 p-2 rounded">{errorInfo.stack}</pre>
            )}
          </div>
          <div>
            <button
              onClick={() => setErrorInfo(null)}
              className="px-3 py-1 bg-red-700 hover:bg-red-600 rounded text-sm font-medium"
              title="Dismiss"
            >
              Dismiss
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
