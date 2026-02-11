import { useCallback, useRef, useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import {
  setPacketStream,
  addPacket,
  setRules,
  setSuspiciousSignatures,
  setVPNSessions,
  addAlert,
  setAnomalyRate,
  setBlockingRate,
  setWSConnected,
  setError,
  setAttestation,
  setAttestationPending,
  addPendingEnforcement,
} from '../store/slices/tdsSlice'
import {
  PacketStreamData,
  PacketEvent,
  DPIRule,
  VPNSession,
  TDSState,
  SecurityAlert,
  ZeroTrustAttestation,
  EnforcementAction,
} from '../types/tds.types'

const API_BASE = 'http://localhost:5000'
const WS_BASE = API_BASE.replace('http', 'ws')

export const useTDS = () => {
  const dispatch = useDispatch()
  const tdsState = useSelector((state: { tds: TDSState }) => state.tds)

  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const latencyMeasureRef = useRef<number>(0)

  const [packetBuffer, setPacketBuffer] = useState<PacketStreamData[]>([])
  const [isConnected, setIsConnected] = useState(false)

  // Initialize WebSocket connection
  const initializeWebSocket = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return
    }

    try {
      const wsUrl = `${WS_BASE}/ws/telemetry`
      wsRef.current = new WebSocket(wsUrl)

      wsRef.current.onopen = () => {
        console.log('[TDS] WebSocket connected')
        setIsConnected(true)
        dispatch(setWSConnected(true))

        // Send connection message
        wsRef.current?.send(
          JSON.stringify({
            type: 'stream_start',
            timestamp: new Date().toISOString(),
          })
        )
      }

      wsRef.current.onmessage = (event) => {
        const message = JSON.parse(event.data)

        switch (message.type) {
          case 'packet_event': {
            const packet = message.payload as PacketEvent
            dispatch(addPacket(packet))
            break
          }

          case 'telemetry_event': {
            const streamData: PacketStreamData = {
              packetId: message.payload.eventId,
              timestamp: message.payload.timestamp,
              source: message.payload.source,
              destination: message.payload.destination,
              protocol: message.payload.protocol || 'unknown',
              bytes: message.payload.payload?.bytes || 0,
              riskScore: message.payload.payload?.riskScore || 0,
              isBlocked: message.payload.payload?.isBlocked || false,
              isAnomalous: message.payload.payload?.isAnomalous || false,
              signature: message.payload.payload?.signature,
              flowState: 'established',
            }
            setPacketBuffer((prev) => [...prev.slice(-99), streamData])
            break
          }

          case 'security_alert': {
            const alert = message.payload as SecurityAlert
            dispatch(addAlert(alert))
            break
          }

          case 'rate_update': {
            const { blockingRate, anomalyRate } = message.payload
            dispatch(setBlockingRate(blockingRate))
            dispatch(setAnomalyRate(anomalyRate))
            break
          }

          case 'error': {
            dispatch(setError(message.payload.message))
            break
          }
        }
      }

      wsRef.current.onerror = (error) => {
        console.error('[TDS] WebSocket error:', error)
        dispatch(setWSConnected(false))
        dispatch(setError('WebSocket connection error'))
      }

      wsRef.current.onclose = () => {
        console.log('[TDS] WebSocket disconnected')
        setIsConnected(false)
        dispatch(setWSConnected(false))

        // Reconnect after 5 seconds
        reconnectTimeoutRef.current = setTimeout(() => {
          initializeWebSocket()
        }, 5000)
      }
    } catch (error) {
      console.error('[TDS] WebSocket init failed:', error)
      dispatch(setError('Failed to initialize telemetry streaming'))
      dispatch(setWSConnected(false))
    }
  }, [dispatch])

  // Fetch DPI rules
  const fetchRules = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/tds/rules`)
      if (!response.ok) throw new Error('Failed to fetch rules')
      const data = await response.json()
      dispatch(setRules(data.rules || []))
      return data.rules as DPIRule[]
    } catch (error) {
      console.error('[TDS] Failed to fetch rules:', error)
      dispatch(setError('Failed to fetch DPI rules'))
      return []
    }
  }, [dispatch])

  // Fetch suspicious signatures
  const fetchSignatures = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/tds/rules`)
      if (!response.ok) throw new Error('Failed to fetch signatures')
      const data = await response.json()
      dispatch(setSuspiciousSignatures(data.suspiciousSignatures || []))
      return data.suspiciousSignatures || []
    } catch (error) {
      console.error('[TDS] Failed to fetch signatures:', error)
      return []
    }
  }, [dispatch])

  // Fetch VPN sessions
  const fetchVPNSessions = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/tds/vpn/sessions`)
      if (!response.ok) throw new Error('Failed to fetch VPN sessions')
      const data = await response.json()
      dispatch(setVPNSessions(data.sessions || []))
      return data.sessions as VPNSession[]
    } catch (error) {
      console.error('[TDS] Failed to fetch VPN sessions:', error)
      dispatch(setError('Failed to fetch VPN sessions'))
      return []
    }
  }, [dispatch])

  // Submit attestation
  const submitAttestation = useCallback(
    async (deviceId: string): Promise<ZeroTrustAttestation | null> => {
      try {
        dispatch(setAttestationPending(true))

        const response = await fetch(`${API_BASE}/tds/attest`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            deviceId,
            timestamp: new Date().toISOString(),
          }),
        })

        if (!response.ok) throw new Error('Attestation failed')
        const data = (await response.json()) as ZeroTrustAttestation
        dispatch(setAttestation(data))
        return data
      } catch (error) {
        console.error('[TDS] Attestation submission failed:', error)
        dispatch(setError('Device attestation failed'))
        return null
      } finally {
        dispatch(setAttestationPending(false))
      }
    },
    [dispatch]
  )

  // Block IP address
  const blockIP = useCallback(
    async (ipAddress: string, reason: string, duration?: number): Promise<boolean> => {
      try {
        const enforcement: EnforcementAction = {
          actionId: `block-${ipAddress}-${Date.now()}`,
          timestamp: new Date().toISOString(),
          actionType: 'block_ip',
          target: ipAddress,
          reason,
          severity: 'high',
          duration,
          confirmed: false,
          status: 'pending',
        }

        dispatch(addPendingEnforcement(enforcement))

        // Call policy enforce endpoint
        const response = await fetch(`${API_BASE}/policy/enforce`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(enforcement),
        })

        if (!response.ok) throw new Error('Block action failed')
        return true
      } catch (error) {
        console.error('[TDS] Block IP failed:', error)
        dispatch(setError('Failed to block IP address'))
        return false
      }
    },
    [dispatch]
  )

  // Isolate endpoint
  const isolateEndpoint = useCallback(
    async (deviceId: string, reason: string): Promise<boolean> => {
      try {
        const enforcement: EnforcementAction = {
          actionId: `isolate-${deviceId}-${Date.now()}`,
          timestamp: new Date().toISOString(),
          actionType: 'isolate_endpoint',
          target: deviceId,
          reason,
          severity: 'critical',
          confirmed: false,
          status: 'pending',
        }

        dispatch(addPendingEnforcement(enforcement))

        // Call policy enforce endpoint
        const response = await fetch(`${API_BASE}/policy/enforce`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(enforcement),
        })

        if (!response.ok) throw new Error('Isolation action failed')
        return true
      } catch (error) {
        console.error('[TDS] Isolate endpoint failed:', error)
        dispatch(setError('Failed to isolate endpoint'))
        return false
      }
    },
    [dispatch]
  )

  // Terminate VPN session
  const terminateVPNSession = useCallback(
    async (sessionId: string): Promise<boolean> => {
      try {
        const response = await fetch(`${API_BASE}/tds/vpn/sessions/${sessionId}`, {
          method: 'DELETE',
        })

        if (!response.ok) throw new Error('Termination failed')
        return true
      } catch (error) {
        console.error('[TDS] VPN session termination failed:', error)
        dispatch(setError('Failed to terminate VPN session'))
        return false
      }
    },
    [dispatch]
  )

  // Measure telemetry latency
  useEffect(() => {
    const measureLatency = () => {
      if (!isConnected) return

      latencyMeasureRef.current = Date.now()
      wsRef.current?.send(
        JSON.stringify({
          type: 'ping',
          timestamp: latencyMeasureRef.current,
        })
      )
    }

    const interval = setInterval(measureLatency, 10000)
    return () => clearInterval(interval)
  }, [isConnected])

  // Update packet stream in Redux
  useEffect(() => {
    if (packetBuffer.length > 0) {
      dispatch(setPacketStream(packetBuffer))
    }
  }, [packetBuffer, dispatch])

  // Initialize on mount
  useEffect(() => {
    initializeWebSocket()
    fetchRules()
    fetchSignatures()
    fetchVPNSessions()

    // Poll for updates every 30 seconds
    const pollInterval = setInterval(() => {
      if (isConnected) {
        fetchVPNSessions()
      }
    }, 30000)

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      if (pollInterval) {
        clearInterval(pollInterval)
      }
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [initializeWebSocket, fetchRules, fetchSignatures, fetchVPNSessions, isConnected])

  return {
    isConnected,
    packetStream: tdsState.packetStream,
    livePackets: tdsState.livePackets,
    rules: tdsState.rules,
    signatures: tdsState.suspiciousSignatures,
    vpnSessions: tdsState.vpnSessions,
    currentAttestation: tdsState.currentAttestation,
    alerts: tdsState.alerts,
    anomalyRate: tdsState.anomalyRate,
    blockingRate: tdsState.blockingRate,
    blockIP,
    isolateEndpoint,
    submitAttestation,
    fetchRules,
    fetchSignatures,
    fetchVPNSessions,
    terminateVPNSession,
  }
}
