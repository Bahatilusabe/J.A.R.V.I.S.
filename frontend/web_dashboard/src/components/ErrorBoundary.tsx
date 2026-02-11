import React from 'react'

declare global {
  interface Window {
    __GLOBAL_ERROR_HOOK__?: (e: Error) => void
  }
}

interface State {
  hasError: boolean
  error?: Error | null
}

interface ErrorBoundaryProps {
  children?: React.ReactNode
}

export default class ErrorBoundary extends React.Component<ErrorBoundaryProps, State> {
  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error('[ErrorBoundary] component error', error, info)
    // Surface to window for GlobalErrorOverlay
    const globalHook = window.__GLOBAL_ERROR_HOOK__
    if (globalHook) {
      try {
        globalHook(error)
      } catch (e) {
        // ignore
      }
    }
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-slate-900 text-white">
          <div className="max-w-2xl p-6 bg-red-900/90 rounded-lg border border-red-700">
            <h2 className="text-xl font-semibold">Application error</h2>
            <p className="mt-2 text-sm text-red-200">An unexpected error occurred while rendering the application.</p>
            <pre className="mt-4 text-xs text-red-100 bg-red-900/20 p-2 rounded">{this.state.error?.stack}</pre>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
