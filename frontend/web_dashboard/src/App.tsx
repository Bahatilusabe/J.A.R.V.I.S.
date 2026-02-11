import { BrowserRouter as Router, Routes, Route, useLocation, useNavigate } from 'react-router-dom'
import { QueryClientProvider, QueryClient } from '@tanstack/react-query'
import { Provider } from 'react-redux'
import { useEffect, useState, useEffect as useEffectReact, lazy, startTransition } from 'react'

import store from './store/index.ts'
import authService from './services/auth.service.ts'
import websocketService from './services/websocket.service.ts'
import GlobalErrorOverlay from './components/GlobalErrorOverlay'
import ErrorBoundary from './components/ErrorBoundary'

// Lazy load all page components to speed up initial load
import LoginPage from './pages/Login.tsx'
const Dashboard = lazy(() => import('./pages/Dashboard.tsx'))
const MilitaryOverview = lazy(() => import('./pages/MilitaryOverview.tsx'))
const PasmPage = lazy(() => import('./pages/pasm.tsx'))
const ModelOpsPage = lazy(() => import('./pages/ModelOps.tsx'))
const FederationPage = lazy(() => import('./pages/Federation.tsx'))
const SelfHealingPage = lazy(() => import('./pages/self-healing-monitor.tsx'))
const NotFoundPage = lazy(() => import('./pages/NotFound.tsx'))
const ForensicsPage = lazy(() => import('./pages/Forensics.tsx'))
const NetworkSecurityPage = lazy(() => import('./pages/NetworkSecurity.tsx'))
const SettingsPage = lazy(() => import('./pages/Settings.tsx'))
const AdminConsole = lazy(() => import('./pages/AdminConsole.tsx'))
const AdminLogin = lazy(() => import('./pages/AdminLogin.tsx'))
const IncidentsPage = lazy(() => import('./pages/Incidents.tsx'))
const IncidentDetail = lazy(() => import('./pages/IncidentDetail.tsx'))
const PoliciesPage = lazy(() => import('./pages/Policies.tsx'))
const EdgeDevices = lazy(() => import('./pages/EdgeDevices.tsx'))
const DeceptionGrid = lazy(() => import('./pages/DeceptionGrid.tsx'))

import PrivateRoute from './components/PrivateRoute.tsx'
import AdminRoute from './components/AdminRoute.tsx'
import Layout from './components/Layout.tsx'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: 2,
    },
  },
})

function LocationLogger() {
  const location = useLocation()
  useEffectReact(() => {
    console.debug('[LocationLogger] navigated', { pathname: location.pathname, search: location.search, hash: location.hash })
    // Also dump stack for debugging sources of navigation
    console.debug(new Error('Navigation stack').stack)
  }, [location])
  return null
}

function LogoutListener() {
  const navigate = useNavigate()
  useEffectReact(() => {
    const handler = () => {
      console.debug('[LogoutListener] received jarvis:logout, navigating to /login')
      navigate('/login')
    }
    window.addEventListener('jarvis:logout', handler)
    return () => window.removeEventListener('jarvis:logout', handler)
  }, [navigate])
  return null
}

function DebugClickListener() {
  useEffectReact(() => {
    const onClick = (e: MouseEvent) => {
      try {
        const target = e.target as HTMLElement
        // find closest anchor
        const anchor = target.closest && (target.closest('a') as HTMLAnchorElement | null)
        if (anchor) {
          console.debug('[DebugClickListener] anchor click', { href: anchor.getAttribute('href'), target: anchor, defaultPrevented: e.defaultPrevented, button: e.button })
        }
      } catch (err) {
        // ignore
      }
    }

    // Use capture phase to see events before React handlers
    window.addEventListener('click', onClick, true)
    return () => window.removeEventListener('click', onClick, true)
  }, [])

  return null
}

function InternalLinkInterceptor() {
  const navigate = useNavigate()

  useEffectReact(() => {
    const handler = (e: MouseEvent) => {
      try {
        // Only handle plain left-clicks
        if (e.button !== 0 || e.defaultPrevented) return

        const target = e.target as HTMLElement
        const anchor = target.closest && (target.closest('a') as HTMLAnchorElement | null)
        if (!anchor) return

        // Respect explicit opt-out (data-no-spa) or targets that open a new tab/window
        if (anchor.hasAttribute('data-no-spa')) return
        if (anchor.target && anchor.target !== '' && anchor.target !== '_self') return

        const href = anchor.getAttribute('href')
        if (!href) return

        // Do not intercept fragment-only anchors (in-page tabs and hash nav)
        if (href.startsWith('#')) return

        // Only handle same-origin, absolute or root-relative links
        const url = new URL(href, window.location.href)
        if (url.origin !== window.location.origin) return

        // Preserve modifier keys (allow ctrl/cmd/middle click to open in new tab)
        const me = e as MouseEvent & { metaKey?: boolean; ctrlKey?: boolean; shiftKey?: boolean; altKey?: boolean }
        if (me.metaKey || me.ctrlKey || me.shiftKey || me.altKey) return

        // Prevent full navigation and use router navigation instead
        e.preventDefault()
        // If the link points to current location, let it pass through
        const dest = url.pathname + url.search + url.hash
        if (dest === window.location.pathname + window.location.search + window.location.hash) return
        console.debug('[InternalLinkInterceptor] intercepting anchor', { href: dest })
        startTransition(() => navigate(dest))
      } catch (err) {
        // ignore and let browser handle it
      }
    }

    window.addEventListener('click', handler, true)
    return () => window.removeEventListener('click', handler, true)
  }, [navigate])

  return null
}

export default function App() {
  const [isInitialized, setIsInitialized] = useState(false)
  const [isFadingOut, setIsFadingOut] = useState(false)

  useEffect(() => {
    // Initialize WebSocket connection
    const initializeApp = async () => {
      try {
        // Connect to WebSocket for real-time updates
        if (authService.isAuthenticated()) {
          await websocketService.connect()
        }
      } catch (error) {
        console.error('Failed to initialize app:', error)
      } finally {
        // Start fade out effect after 4 seconds
        setTimeout(() => {
          setIsFadingOut(true)
          // Complete initialization after fade out animation
          setTimeout(() => {
            setIsInitialized(true)
          }, 4000)
        }, 4000)
      }
    }

    initializeApp()

    // Cleanup on unmount
    return () => {
      websocketService.disconnect()
    }
  }, [])

  if (!isInitialized) {
    return (
      <>
        <style>{`
          @keyframes fadeOutLoader {
            0% { opacity: 1; }
            100% { opacity: 0; }
          }
          .loader-screen {
            animation: ${isFadingOut ? 'fadeOutLoader 4s ease-out forwards' : 'none'};
          }
        `}</style>
        <div className="loader-screen fixed inset-0 flex items-center justify-center min-h-screen bg-gradient-to-br from-slate-950 via-dark-900 to-slate-900 z-50">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500 mx-auto mb-4"></div>
            <p className="text-cyan-500 text-lg font-medium">Initializing J.A.R.V.I.S...</p>
          </div>
        </div>
      </>
    )
  }

  return (
    <Provider store={store}>
      <QueryClientProvider client={queryClient}>
        <GlobalErrorOverlay />
        <Router>
          <LocationLogger />
          <LogoutListener />
          <DebugClickListener />
          <InternalLinkInterceptor />
          <ErrorBoundary>
            <Routes>
              <Route path="/" element={<LoginPage />} />
              <Route path="/login" element={<LoginPage />} />

              {/* Explicit top-level route for PASM to ensure direct navigation works */}
              <Route
                path="/pasm"
                element={
                  <PrivateRoute>
                    <Layout>
                      <PasmPage />
                    </Layout>
                  </PrivateRoute>
                }
              />

              {/* Explicit top-level route for Policies */}
              <Route
                path="/policies"
                element={
                  <PrivateRoute>
                    <Layout>
                      <PoliciesPage />
                    </Layout>
                  </PrivateRoute>
                }
              />

              {/* Explicit top-level route for ModelOps */}
              <Route
                path="/modelops"
                element={
                  <PrivateRoute>
                    <Layout>
                      <ModelOpsPage />
                    </Layout>
                  </PrivateRoute>
                }
              />

              {/* Explicit top-level route for Edge Devices */}
              <Route
                path="/edge"
                element={
                  <PrivateRoute>
                    <Layout>
                      <EdgeDevices />
                    </Layout>
                  </PrivateRoute>
                }
              />

              {/* Explicit top-level route for Deception Grid */}
              <Route
                path="/deception"
                element={
                  <PrivateRoute>
                    <Layout>
                      <DeceptionGrid />
                    </Layout>
                  </PrivateRoute>
                }
              />

              {/* Explicit top-level route for Dashboard (default after login) */}
              <Route
                path="/dashboard"
                element={
                  <PrivateRoute>
                    <Layout>
                      <Dashboard />
                    </Layout>
                  </PrivateRoute>
                }
              />

              {/* Explicit top-level route for Military Overview */}
              <Route
                path="/military"
                element={
                  <PrivateRoute>
                    <Layout>
                      <MilitaryOverview />
                    </Layout>
                  </PrivateRoute>
                }
              />

              {/* Explicit top-level route for Self-Healing Monitor */}
              <Route
                path="/self-healing"
                element={
                  <PrivateRoute>
                    <Layout>
                      <SelfHealingPage />
                    </Layout>
                  </PrivateRoute>
                }
              />

              {/* Explicit top-level route for Forensics */}
              <Route
                path="/forensics"
                element={
                  <PrivateRoute>
                    <Layout>
                      <ForensicsPage />
                    </Layout>
                  </PrivateRoute>
                }
              />

              {/* Explicit top-level route for Incidents */}
              <Route
                path="/incidents"
                element={
                  <PrivateRoute>
                    <Layout>
                      <IncidentsPage />
                    </Layout>
                  </PrivateRoute>
                }
              />

              {/* Explicit top-level route for Incident Detail */}
              <Route
                path="/incidents/:id"
                element={
                  <PrivateRoute>
                    <Layout>
                      <IncidentDetail />
                    </Layout>
                  </PrivateRoute>
                }
              />

              {/* Explicit top-level route for Federation */}
              <Route
                path="/federation"
                element={
                  <PrivateRoute>
                    <Layout>
                      <FederationPage />
                    </Layout>
                  </PrivateRoute>
                }
              />

              {/* Explicit top-level route for Network Security */}
              <Route
                path="/network-security"
                element={
                  <PrivateRoute>
                    <Layout>
                      <NetworkSecurityPage />
                    </Layout>
                  </PrivateRoute>
                }
              />

              {/* Explicit top-level route for Settings */}
              <Route
                path="/settings"
                element={
                  <PrivateRoute>
                    <Layout>
                      <SettingsPage />
                    </Layout>
                  </PrivateRoute>
                }
              />

              {/* Explicit top-level route for Admin Console - Admin Only (new safe console) */}
              <Route path="/admin/login" element={<AdminLogin />} />
              <Route
                path="/admin"
                element={
                  <AdminRoute>
                    <Layout>
                      <AdminConsole />
                    </Layout>
                  </AdminRoute>
                }
              />

              {/* Protected catch-all route for NotFound */}
              <Route
                path="*"
                element={
                  <PrivateRoute>
                    <Layout>
                      <NotFoundPage />
                    </Layout>
                  </PrivateRoute>
                }
              />
            </Routes>
          </ErrorBoundary>
          {/* No future flags needed for React Router v6+ */}
          {/* Remove deprecated usage if present */}
        </Router>
      </QueryClientProvider>
    </Provider>
  )
}

// Enable aggressive location tracer when requested
if (typeof window !== 'undefined') {
  try {
    const shouldEnable = localStorage.getItem('jarvis_debug_location') === '1' || new URL(window.location.href).searchParams.get('debug') === 'location'
    if (shouldEnable) {
      import('./utils/debugLocationTracer').then((m) => {
        m.default()
        console.info('[App] DebugLocationTracer activated')
      }).catch((err) => console.error('[App] Failed to activate DebugLocationTracer', err))
    }
  } catch (err) {
    // ignore
  }
}

// Global beforeunload listener to detect real page unloads (full reloads)
if (typeof window !== 'undefined') {
  window.addEventListener('beforeunload', (_e) => {
    try {
      console.debug('[Global] beforeunload detected', { href: window.location.href })
      console.debug(new Error('beforeunload stack').stack)
    } catch (err) {
      // ignore
    }
  })
}
