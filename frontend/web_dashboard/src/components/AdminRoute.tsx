/**
 * AdminRoute Component
 * 
 * Protects admin-only pages from unauthorized access.
 * Checks both authentication status and admin role before rendering.
 * Redirects to login if not authenticated, or to dashboard if not admin.
 */

import { Navigate, useLocation } from 'react-router-dom'
import { useEffect, useState } from 'react'
import useAuth from '../hooks/useAuth'
import authService from '../services/auth.service'

interface AdminRouteProps {
  children: React.ReactNode
}

export default function AdminRoute({ children }: AdminRouteProps) {
  const location = useLocation()

  // Use auth hook to get up-to-date auth/profile state
  const { user, isAuthenticated, isLoading, getProfile } = useAuth()
  // If Redux auth slice isn't present yet (dev/local builds) we may have user info in localStorage.
  // Treat that as the effective user to avoid unnecessary profile fetches and to make the
  // dev backdoor work without requiring the auth reducer to be wired.
  const localUser = authService.getUser()
  const effectiveUser = user || localUser
  const [loadingProfile, setLoadingProfile] = useState(false)

  const hasToken = authService.isAuthenticated()

  useEffect(() => {
    let mounted = true

    // If we have a token (either from hook or local storage) but no user info in either
    // Redux or localStorage, fetch profile. If localStorage already has a user (dev backdoor),
    // skip the network fetch to avoid blocking the SPA navigation.
    if ((isAuthenticated || hasToken) && !effectiveUser && !isLoading) {
      setLoadingProfile(true)
      getProfile()
        .catch(() => {
          // If profile fetch fails, we'll let the hook/logics handle logout
        })
        .finally(() => {
          if (mounted) setLoadingProfile(false)
        })
    }

    return () => {
      mounted = false
    }
  }, [isAuthenticated, effectiveUser, isLoading, getProfile, hasToken])

  // If we don't have a token (no session) and auth state also reports not authenticated, redirect to login
  if (!hasToken && !isAuthenticated) {
    console.debug('[AdminRoute] No token and not authenticated. Redirecting to /admin/login', { hasToken, isAuthenticated })
    return <Navigate to="/admin/login" state={{ from: location }} replace />
  }

  // If we have a token (either stored or via hook) and profile is missing/loading, render a spinner
  if (hasToken && (loadingProfile || isLoading || !effectiveUser)) {
    console.debug('[AdminRoute] Token present and profile loading. Rendering spinner', { hasToken, loadingProfile, isLoading, user })
    return (
      <div className="flex items-center justify-center h-screen bg-slate-900">
        <div className="text-center">
          <div className="animate-spin mb-4">🔄</div>
          <div className="text-gray-300">Loading admin console…</div>
        </div>
      </div>
    )
  }

  // If we have a user and they are not an admin, redirect to dashboard
  if (effectiveUser && effectiveUser.role !== 'admin') {
    console.debug('[AdminRoute] User is not admin - redirecting to /dashboard', { user: effectiveUser })
    return <Navigate to="/dashboard" state={{ from: location }} replace />
  }

  // Admin — render children
  return <>{children}</>
}
