import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios'
import authService from '../services/auth.service'

/**
 * API Base URL Configuration
 * - From environment: VITE_API_BASE_URL
 * - Default: http://127.0.0.1:8000 (FastAPI backend port)
 * - Backend routes are registered with prefixes: /telemetry, /policy, /forensics, /dpi, etc.
 */
const API_BASE_URL = (import.meta as unknown as { env: Record<string, string> }).env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

/**
 * API client with request/response interceptors
 * Handles:
 * - Authorization header injection
 * - Token refresh on 401 responses
 * - Global error handling
 * - Retry logic for failed requests
 */
class APIClient {
  private instance: AxiosInstance
  private retryCount: Map<string, number> = new Map()
  private readonly MAX_RETRIES = 3
  private readonly RETRY_DELAY_MS = 1000

  constructor() {
    this.instance = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    this.setupInterceptors()
  }

  /**
   * Setup request and response interceptors
   */
  private setupInterceptors(): void {
    // Request interceptor: Add authorization header
    this.instance.interceptors.request.use(
      (config) => {
        const headers = authService.getAuthHeaders()
        if (config.headers) {
          Object.assign(config.headers, headers)
        }
        return config
      },
      (error) => {
        console.error('Request error:', error)
        return Promise.reject(error)
      }
    )

    // Response interceptor: Handle 401 and errors
    this.instance.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        const config = error.config

        if (!config) {
          return Promise.reject(error)
        }

        // Handle 401 Unauthorized
        if (error.response?.status === 401) {
          try {
            // Refresh token
            await authService.refreshToken()

            // Update headers with new token
            const headers = authService.getAuthHeaders()
            if (config.headers) {
              Object.assign(config.headers, headers)
            }

            // Retry request with new token
            return this.instance(config)
          } catch (refreshError) {
            // Token refresh failed - perform SPA-friendly logout
            authService.logout()
            // Dispatch a global event so the React app can react (navigate to /login via router)
            try {
              console.debug('[APIClient] Dispatching jarvis:logout event')
              window.dispatchEvent(new CustomEvent('jarvis:logout'))
            } catch (e) {
              // Ignore if CustomEvent unsupported
            }
            return Promise.reject(refreshError)
          }
        }

        // Retry logic for transient failures (5xx, network errors)
        if (this.shouldRetry(error)) {
          const requestKey = `${config.method} ${config.url}`
          const retries = this.retryCount.get(requestKey) || 0

          if (retries < this.MAX_RETRIES) {
            this.retryCount.set(requestKey, retries + 1)

            // Exponential backoff
            const delay = this.RETRY_DELAY_MS * Math.pow(2, retries)

            await this.sleep(delay)

            return this.instance(config)
          } else {
            this.retryCount.delete(requestKey)
          }
        }

        // Log error
        this.logError(error)

        return Promise.reject(error)
      }
    )
  }

  /**
   * Determine if request should be retried
   */
  private shouldRetry(error: AxiosError): boolean {
    if (!error.response) {
      // Network error
      return true
    }

    const status = error.response.status

    // Retry on 5xx (server errors) or 429 (rate limit)
    return status >= 500 || status === 429
  }

  /**
   * Log error details
   */
  private logError(error: AxiosError): void {
    console.error('API Error:', {
      status: error.response?.status,
      statusText: error.response?.statusText,
      url: error.config?.url,
      method: error.config?.method,
      data: error.response?.data,
    })
  }

  /**
   * Sleep utility for delays
   */
  private sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms))
  }

  /**
   * GET request
   */
  async get<T>(url: string, config = {}): Promise<AxiosResponse<T>> {
    return this.instance.get<T>(url, config)
  }

  /**
   * POST request
   */
  async post<T>(url: string, data?: unknown, config = {}): Promise<AxiosResponse<T>> {
    return this.instance.post<T>(url, data, config)
  }

  /**
   * PUT request
   */
  async put<T>(url: string, data?: unknown, config = {}): Promise<AxiosResponse<T>> {
    return this.instance.put<T>(url, data, config)
  }

  /**
   * PATCH request
   */
  async patch<T>(url: string, data?: unknown, config = {}): Promise<AxiosResponse<T>> {
    return this.instance.patch<T>(url, data, config)
  }

  /**
   * DELETE request
   */
  async delete<T>(url: string, config = {}): Promise<AxiosResponse<T>> {
    return this.instance.delete<T>(url, config)
  }

  /**
   * Get the underlying axios instance (for advanced use cases)
   */
  getInstance(): AxiosInstance {
    return this.instance
  }
}

// Export singleton instance
export const apiClient = new APIClient()

/**
 * Helper function to extract error message from API response
 */
export function getErrorMessage(error: unknown): string {
  if (error instanceof AxiosError) {
    return (
      error.response?.data?.message ||
      error.response?.data?.error ||
      error.message ||
      'An error occurred'
    )
  }

  if (error instanceof Error) {
    return error.message
  }

  return 'An unknown error occurred'
}

/**
 * Helper function to check if error is network-related
 */
export function isNetworkError(error: unknown): boolean {
  if (error instanceof AxiosError) {
    return !error.response // No response means network error
  }
  return false
}

/**
 * Helper function to check if error is 401 unauthorized
 */
export function isUnauthorizedError(error: unknown): boolean {
  if (error instanceof AxiosError) {
    return error.response?.status === 401
  }
  return false
}

export default apiClient
