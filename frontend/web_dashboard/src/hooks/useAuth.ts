import { useState, useCallback, useEffect } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import authService from '../services/auth.service'
import { AuthToken, User } from '../types/index'
import { RootState } from '../store/index'

interface UseAuthReturn {
  user: User | null
  token: AuthToken | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
  login: (username: string, password: string) => Promise<void>
  logout: () => void
  refreshToken: () => Promise<void>
  getProfile: () => Promise<void>
  clearError: () => void
}

/**
 * Hook for authentication management
 * Provides user state, token management, and auth operations
 * Integrates with Redux store for state persistence
 */
export function useAuth(): UseAuthReturn {
  const dispatch = useDispatch()
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Get auth state from Redux
  const authState = useSelector((state: RootState) => state.auth)
  const user = authState?.user || null
  const token = authState?.token || null
  const isAuthenticated = authState?.isAuthenticated || false

  /**
   * Login with username and password
   */
  const login = useCallback(async (username: string, password: string) => {
    try {
      setIsLoading(true)
      setError(null)

      const authToken = await authService.login(username, password)

      // Dispatch to Redux store
      dispatch({
        type: 'auth/loginSuccess',
        payload: {
          token: authToken,
          user: authService.getUser(),
        },
      })
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Login failed'
      setError(message)
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [dispatch])

  /**
   * Logout and clear all session data
   */
  const logout = useCallback(() => {
    try {
      authService.logout()

      // Dispatch to Redux store
      dispatch({
        type: 'auth/logout',
      })

      setError(null)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Logout failed'
      setError(message)
    }
  }, [dispatch])

  /**
   * Refresh authentication token
   */
  const refreshToken = useCallback(async () => {
    try {
      setIsLoading(true)
      setError(null)

      const newToken = await authService.refreshToken()

      // Dispatch to Redux store
      dispatch({
        type: 'auth/tokenRefreshed',
        payload: { token: newToken },
      })
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Token refresh failed'
      setError(message)

      // Logout on refresh failure
      logout()
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [dispatch, logout])

  /**
   * Fetch user profile
   */
  const getProfile = useCallback(async () => {
    try {
      setIsLoading(true)
      setError(null)

      const profile = await authService.getProfile()

      // Dispatch to Redux store
      dispatch({
        type: 'auth/profileFetched',
        payload: { user: profile },
      })
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch profile'
      setError(message)
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [dispatch])

  /**
   * Clear error message
   */
  const clearError = useCallback(() => {
    setError(null)
  }, [])

  /**
   * Check authentication on mount
   */
  useEffect(() => {
    if (authService.isAuthenticated() && !user) {
      getProfile().catch(() => {
        // Profile fetch failed, logout
        logout()
      })
    }
  }, [user, getProfile, logout])

  return {
    user,
    token,
    isAuthenticated,
    isLoading,
    error,
    login,
    logout,
    refreshToken,
    getProfile,
    clearError,
  }
}

export default useAuth
