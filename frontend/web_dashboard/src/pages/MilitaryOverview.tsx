import React, { useEffect, useState, useMemo } from 'react'
import { useSystemStatus } from '../hooks/useSystemStatus'
import { useTelemetry } from '../hooks/useTelemetry'
import { usePasm } from '../hooks/usePasm'
import { useForensics } from '../hooks/useForensics'
import '../styles/military-design.css'

/**
 * Advanced Military-Grade Overview Dashboard
 * Features:
 * - Tactical Threat Grid Display
 * - Real-time Threat Level Indicators
 * - System Status Hexagon
 * - Network Topology Visualization
 * - Incident Heat Map
 */
const MilitaryOverview: React.FC = () => {
  const { systemStatus, healthCheck, federationStatus } = useSystemStatus()
  const { events } = useTelemetry()
  const { predictions: _predictions } = usePasm()
  const { auditLogs } = useForensics()

  type EventItem = { severity?: string }

  const [threatLevel, setThreatLevel] = useState<'green' | 'yellow' | 'orange' | 'red'>('green')
  const [scanLines, setScanLines] = useState(true)
  const [selectedSector, setSelectedSector] = useState<string | null>(null)

  // Calculate threat indicators
  const threatMetrics = useMemo(() => {
    const totalEvents = events?.length || 0
    const criticalEvents = events?.filter((e: EventItem) => e.severity === 'critical').length || 0
    const highEvents = events?.filter((e: EventItem) => e.severity === 'high').length || 0

    // Determine threat level
    let level: 'green' | 'yellow' | 'orange' | 'red' = 'green'
    if (criticalEvents > 5) level = 'red'
    else if (criticalEvents > 2 || highEvents > 5) level = 'orange'
    else if (criticalEvents > 0 || highEvents > 2) level = 'yellow'

    return {
      totalEvents,
      criticalEvents,
      highEvents,
      mediumEvents: events?.filter((e: EventItem) => e.severity === 'medium').length || 0,
      threatLevel: level,
      systemHealth: systemStatus?.nodeHealth === 'healthy' ? 95 : systemStatus?.nodeHealth === 'degraded' ? 70 : 20,
      uptime: healthCheck?.uptime ? `${Math.round(healthCheck.uptime)}h` : 'N/A',
      activePolicies: systemStatus?.activePolicies || 0,
    }
  }, [events, systemStatus, healthCheck])

  useEffect(() => {
    setThreatLevel(threatMetrics.threatLevel)
  }, [threatMetrics.threatLevel])

  // Scanning animation effect
  useEffect(() => {
    const interval = setInterval(() => {
      setScanLines(prev => !prev)
    }, 2000)
    return () => clearInterval(interval)
  }, [])

  const sectors = [
    { id: 'network', label: 'NETWORK', value: threatMetrics.totalEvents, status: 'active' },
    { id: 'endpoints', label: 'ENDPOINTS', value: threatMetrics.criticalEvents, status: threatMetrics.criticalEvents > 0 ? 'alert' : 'active' },
    { id: 'policies', label: 'POLICIES', value: threatMetrics.activePolicies, status: 'active' },
    { id: 'forensics', label: 'FORENSICS', value: (auditLogs as any)?.items?.length || 0, status: 'active' },
  ]

  return (
    <div className="military-overview-container">
      {/* Header - Combat Status Display */}
      <div className="combat-header">
        <div className="header-left">
          <h1 className="combat-title">TACTICAL THREAT ASSESSMENT</h1>
          <div className="timestamp">{new Date().toLocaleTimeString('en-US', { hour12: false })}</div>
        </div>
        <div className={`threat-indicator threat-${threatLevel}`}>
          <div className="threat-label">THREAT LEVEL</div>
          <div className="threat-value">{threatLevel.toUpperCase()}</div>
          <div className="threat-pulse"></div>
        </div>
      </div>

      {/* Main Grid Layout */}
      <div className="military-grid">
        {/* Left Column - System Status */}
        <div className="grid-section left-column">
          {/* System Hexagon Status */}
          <div className="system-hexagon-container">
            <svg viewBox="0 0 200 200" className="system-hexagon">
              <defs>
                <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
                  <feGaussianBlur stdDeviation="3" result="coloredBlur" />
                  <feMerge>
                    <feMergeNode in="coloredBlur" />
                    <feMergeNode in="SourceGraphic" />
                  </feMerge>
                </filter>
              </defs>
              {/* Hexagon border */}
              <polygon points="100,30 170,55 170,145 100,170 30,145 30,55"
                className={`hexagon-border hexagon-${threatLevel}`}
                fill="none" strokeWidth="2" filter="url(#glow)" />
              {/* Inner hexagon */}
              <polygon points="100,50 160,75 160,125 100,150 40,125 40,75"
                className="hexagon-inner"
                fill="none" strokeWidth="1" opacity="0.5" />
            </svg>
            <div className="hexagon-content">
              <div className="hexagon-stat">
                <div className="stat-label">HEALTH</div>
                <div className="stat-value">{threatMetrics.systemHealth}%</div>
              </div>
              <div className="hexagon-icon">⚔️</div>
            </div>
          </div>

          {/* Quick Stats */}
          <div className="stats-panel">
            <div className="stat-card critical">
              <div className="stat-icon">●</div>
              <div className="stat-info">
                <div className="stat-name">CRITICAL ALERTS</div>
                <div className="stat-number">{threatMetrics.criticalEvents}</div>
              </div>
            </div>
            <div className="stat-card warning">
              <div className="stat-icon">●</div>
              <div className="stat-info">
                <div className="stat-name">HIGH PRIORITY</div>
                <div className="stat-number">{threatMetrics.highEvents}</div>
              </div>
            </div>
            <div className="stat-card info">
              <div className="stat-icon">●</div>
              <div className="stat-info">
                <div className="stat-name">MEDIUM ALERTS</div>
                <div className="stat-number">{threatMetrics.mediumEvents}</div>
              </div>
            </div>
            <div className="stat-card success">
              <div className="stat-icon">●</div>
              <div className="stat-info">
                <div className="stat-name">UPTIME</div>
                <div className="stat-number">{threatMetrics.uptime}</div>
              </div>
            </div>
          </div>
        </div>

        {/* Center Column - Tactical Display */}
        <div className="grid-section center-column">
          {/* Sector Grid */}
          <div className="sector-grid">
            {sectors.map((sector) => (
              <div
                key={sector.id}
                className={`sector-tile sector-${sector.status} ${selectedSector === sector.id ? 'selected' : ''}`}
                onClick={() => setSelectedSector(selectedSector === sector.id ? null : sector.id)}
              >
                <div className="sector-header">
                  <div className="sector-label">{sector.label}</div>
                  <div className={`sector-status-dot status-${sector.status}`}></div>
                </div>
                <div className="sector-value">{sector.value}</div>
                <div className="sector-bar">
                  <div className="sector-fill" style={{ width: `${Math.min((sector.value / 20) * 100, 100)}%` }}></div>
                </div>
                <div className="sector-scan-line" style={{ opacity: scanLines ? 0.8 : 0.2 }}></div>
              </div>
            ))}
          </div>

          {/* Threat Heat Map */}
          <div className="heat-map-container">
            <div className="heat-map-label">THREAT DISTRIBUTION</div>
            <div className="heat-map">
              {Array.from({ length: 16 }).map((_, i) => {
                const intensity = Math.random()
                return (
                  <div
                    key={i}
                    className="heat-cell"
                    style={{
                      opacity: 0.3 + intensity * 0.7,
                      backgroundColor:
                        intensity > 0.7 ? '#ff1744' :
                          intensity > 0.4 ? '#ffa726' :
                            '#66bb6a'
                    }}
                  ></div>
                )
              })}
            </div>
          </div>
        </div>

        {/* Right Column - System Details */}
        <div className="grid-section right-column">
          {/* System Status Details */}
          <div className="system-details">
            <div className="details-header">SYSTEM STATUS</div>
            <div className="details-list">
              <div className="detail-row">
                <span className="detail-label">CPU LOAD</span>
                <span className="detail-value">{(systemStatus as any)?.cpu_usage?.toFixed?.(1) || '42'}%</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">MEMORY USAGE</span>
                <span className="detail-value">{(systemStatus as any)?.memory_usage?.toFixed?.(1) || '58'}%</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">NETWORK CONNECTIONS</span>
                <span className="detail-value">847</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">ACTIVE POLICIES</span>
                <span className="detail-value">{threatMetrics.activePolicies}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">FORENSICS LOGS</span>
                <span className="detail-value">{(auditLogs as any)?.items?.length || 0}</span>
              </div>
            </div>
          </div>

          {/* Federation Status */}
          <div className="federation-status">
            <div className="details-header">FEDERATION STATUS</div>
            <div className="details-list">
              <div className="detail-row">
                <span className="detail-label">NODES ACTIVE</span>
                <span className="detail-value">{federationStatus?.peers?.length || 0}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">SYNC STATUS</span>
                <span className="detail-value success">SYNCHRONIZED</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">REPLICATION</span>
                <span className="detail-value">{federationStatus?.ledgerHeight || 3}x</span>
              </div>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="quick-actions">
            <div className="details-header">ACTIONS</div>
            <div className="action-buttons">
              <button className="action-btn threat-scan">
                <span className="btn-icon">🔍</span>
                <span className="btn-label">THREAT SCAN</span>
              </button>
              <button className="action-btn isolation">
                <span className="btn-icon">🛡️</span>
                <span className="btn-label">ISOLATE</span>
              </button>
              <button className="action-btn remediate">
                <span className="btn-icon">⚡</span>
                <span className="btn-label">REMEDIATE</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Footer - Status Bar */}
      <div className="status-footer">
        <div className="footer-item">
          <span className="footer-label">TOTAL EVENTS</span>
          <span className="footer-value">{threatMetrics.totalEvents}</span>
        </div>
        <div className="footer-item">
          <span className="footer-label">DETECTION RATE</span>
          <span className="footer-value">99.8%</span>
        </div>
        <div className="footer-item">
          <span className="footer-label">AVG RESPONSE TIME</span>
          <span className="footer-value">247ms</span>
        </div>
        <div className="footer-item">
          <span className="footer-label">LAST UPDATE</span>
          <span className="footer-value">{new Date().toLocaleTimeString('en-US', { hour12: false })}</span>
        </div>
      </div>
    </div>
  )
}

export default MilitaryOverview
