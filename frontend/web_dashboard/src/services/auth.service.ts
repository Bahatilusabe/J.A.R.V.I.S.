import { AuthToken, User } from '../types/index'

const API_BASE_URL = (import.meta as unknown as { env: Record<string, string> }).env.VITE_API_URL || 'http://127.0.0.1:8000'
const AUTH_TOKEN_KEY = 'jarvis_access_token'
const REFRESH_TOKEN_KEY = 'jarvis_refresh_token'
const USER_KEY = 'jarvis_user'

interface LoginRequest {
  username: string
  password: string
}

class AuthService {
  private refreshTokenPromise: Promise<AuthToken> | null = null

  /**
   * Login with username and password
   * Returns PQC-backed session token (Dilithium-signed JWT or hybrid)
   */
  async login(username: string, password: string): Promise<AuthToken> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ username, password } as LoginRequest),
      })

      if (!response.ok) {
        const error = await response.json().catch(() => ({ message: response.statusText }))
        throw new Error(`Login failed: ${error.message || response.statusText}`)
      }

      const data = await response.json()

      // Normalize token shape: backend may return { access_token, refresh_token }
      // or { token: { accessToken, refreshToken } } depending on implementation.
      let token: AuthToken
      if (data.token && data.token.accessToken && data.token.refreshToken) {
        token = data.token as AuthToken
      } else if (data.access_token || data.refresh_token) {
        token = {
          accessToken: data.access_token || data.accessToken || '',
          refreshToken: data.refresh_token || data.refreshToken || '',
        } as AuthToken
      } else {
        throw new Error('Login response did not contain tokens')
      }

      // Store tokens securely
      if (token.accessToken) localStorage.setItem(AUTH_TOKEN_KEY, token.accessToken)
      if (token.refreshToken) localStorage.setItem(REFRESH_TOKEN_KEY, token.refreshToken)

      // Store user info if available
      if (data.user) {
        localStorage.setItem(USER_KEY, JSON.stringify(data.user))
      }

      return token
    } catch (error) {
      console.error('Auth service login error:', error)
      throw error
    }
  }

  /**
   * Verify PQC challenge (Dilithium-based)
   * Called after initial login if PQC is enabled
   */
  async verifyPQCChallenge(signature: string): Promise<AuthToken> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/verify-pqc`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ signature }),
      })

      if (!response.ok) {
        throw new Error('PQC verification failed')
      }

      const data = await response.json()
      const token = data.token as AuthToken

      // Update tokens
      localStorage.setItem(AUTH_TOKEN_KEY, token.accessToken)
      localStorage.setItem(REFRESH_TOKEN_KEY, token.refreshToken)

      return token
    } catch (error) {
      console.error('PQC verification failed:', error)
      throw error
    }
  }

  /**
   * Refresh authentication token
   * Automatically called by interceptor on 401 responses
   * Prevents multiple concurrent refresh requests
   */
  async refreshToken(): Promise<AuthToken> {
    // Return existing refresh promise if already in flight
    if (this.refreshTokenPromise) {
      return this.refreshTokenPromise
    }

    this.refreshTokenPromise = this._performTokenRefresh()

    try {
      const token = await this.refreshTokenPromise
      return token
    } finally {
      this.refreshTokenPromise = null
    }
  }

  private async _performTokenRefresh(): Promise<AuthToken> {
    try {
      const refreshToken = this.getRefreshToken()

      if (!refreshToken) {
        throw new Error('No refresh token available')
      }

      const response = await fetch(`${API_BASE_URL}/api/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${refreshToken}`,
        },
        credentials: 'include',
        body: JSON.stringify({ refreshToken }),
      })

      if (!response.ok) {
        if (response.status === 401) {
          this.logout()
        }
        throw new Error('Token refresh failed')
      }

      const data = await response.json()
      const token = data.token as AuthToken

      localStorage.setItem(AUTH_TOKEN_KEY, token.accessToken)
      localStorage.setItem(REFRESH_TOKEN_KEY, token.refreshToken)

      return token
    } catch (error) {
      console.error('Token refresh error:', error)
      this.logout()
      throw error
    }
  }

  /**
   * Get current user profile
   */
  async getProfile(): Promise<User> {
    try {
      const token = this.getAccessToken()

      if (!token) {
        throw new Error('No authentication token')
      }

      const response = await fetch(`${API_BASE_URL}/api/auth/profile`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      })

      if (!response.ok) {
        if (response.status === 401) {
          await this.refreshToken()
          return this.getProfile() // Retry with new token
        }
        throw new Error('Failed to fetch profile')
      }

      const user = await response.json()
      localStorage.setItem(USER_KEY, JSON.stringify(user))
      return user
    } catch (error) {
      console.error('Profile fetch error:', error)
      throw error
    }
  }

  /**
   * Logout and clear all session data
   */
  logout(): void {
    localStorage.removeItem(AUTH_TOKEN_KEY)
    localStorage.removeItem(REFRESH_TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
  }

  /**
   * Get access token from storage
   */
  getAccessToken(): string | null {
    return localStorage.getItem(AUTH_TOKEN_KEY)
  }

  /**
   * Get refresh token from storage
   */
  getRefreshToken(): string | null {
    return localStorage.getItem(REFRESH_TOKEN_KEY)
  }

  /**
   * Get stored user info
   */
  getUser(): User | null {
    const userStr = localStorage.getItem(USER_KEY)
    if (!userStr) return null
    try {
      return JSON.parse(userStr)
    } catch {
      return null
    }
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    const token = this.getAccessToken()
    return !!token && !this.isTokenExpired(token)
  }

  /**
   * Get authorization headers for API requests
   * Used by axios interceptor and fetch calls
   */
  getAuthHeaders(): Record<string, string> {
    const token = this.getAccessToken()
    return {
      'Authorization': token ? `Bearer ${token}` : '',
      'Content-Type': 'application/json',
    }
  }

  /**
   * Check if JWT token is expired
   */
  private isTokenExpired(token: string): boolean {
    try {
      const decoded = this.decodeJWT(token)
      const exp = decoded.exp as number | undefined
      if (!exp) return false
      return exp * 1000 < Date.now()
    } catch {
      return true
    }
  }

  /**
   * Decode JWT without verification (for client-side use only)
   */
  private decodeJWT(token: string): Record<string, unknown> {
    try {
      const parts = token.split('.')
      if (parts.length !== 3) throw new Error('Invalid JWT')

      const decoded = JSON.parse(
        atob(parts[1].replace(/-/g, '+').replace(/_/g, '/'))
      )
      return decoded as Record<string, unknown>
    } catch (error) {
      console.error('Failed to decode JWT:', error)
      return {}
    }
  }
}

// Export singleton instance
export default new AuthService()
