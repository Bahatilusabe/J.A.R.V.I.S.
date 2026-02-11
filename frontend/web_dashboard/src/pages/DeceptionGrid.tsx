import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Activity,
  AlertTriangle,
  BarChart3,
  Clock,
  Download,
  Globe,
  Grid3x3,
  Loader,
  MapPin,
  Menu,
  Network,
  RefreshCw,
  Search,
  Server,
  Shield,
  TrendingUp,
  Zap,
} from 'lucide-react';
import deceptionService from '../services/deceptionService';
import './DeceptionGrid.css';

interface Honeypot {
  id: string;
  name: string;
  type: string;
  status: 'running' | 'stopped' | 'error';
  platform: string;
  port: number;
  deployedAt: number;
  threatLevel: 'low' | 'medium' | 'high' | 'critical';
  interactionCount: number;
  lastInteraction?: number;
  config?: Record<string, string>;
}

interface InteractionEvent {
  id: string;
  honeypotId: string;
  honeypotName: string;
  timestamp: number;
  clientIp: string;
  clientPort: number;
  payloadSummary: string;
  severity: 'info' | 'warning' | 'critical';
  notes?: string;
}

interface DeceptionStats {
  totalHoneypots: number;
  activeHoneypots: number;
  totalInteractions: number;
  threatLevel: string;
  avgResponseTime: number;
  decoyModelsDeployed: number;
}

interface Toast {
  id: string;
  message: string;
  type: 'success' | 'error' | 'info';
}

type ViewMode = 'grid' | 'list' | 'analytics' | 'timeline';
type FilterType = 'status' | 'threatLevel' | 'platform' | 'type';

const DeceptionGrid: React.FC = () => {
  // State Management
  const [honeypots, setHoneypots] = useState<Honeypot[]>([]);
  const [events, setEvents] = useState<InteractionEvent[]>([]);
  const [stats, setStats] = useState<DeceptionStats | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>('grid');
  const [selectedHoneypot, setSelectedHoneypot] = useState<Honeypot | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [activeFilters, setActiveFilters] = useState<Record<FilterType, string[]>>({
    status: [],
    threatLevel: [],
    platform: [],
    type: [],
  });
  const [loading, setLoading] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [showDetailPane, setShowDetailPane] = useState(false);
  const [sortBy, setSortBy] = useState<'interactions' | 'threatLevel' | 'timestamp'>('threatLevel');
  const [toasts, setToasts] = useState<Toast[]>([]);
  const [loadingStates, setLoadingStates] = useState<Record<string, boolean>>({});
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newName, setNewName] = useState('');
  const [newServiceType, setNewServiceType] = useState('SSH');
  const [newPort, setNewPort] = useState<number | ''>('');
  const [newConfig, setNewConfig] = useState('');
  const [creating, setCreating] = useState(false);

  // Toast Management
  const addToast = useCallback((message: string, type: 'success' | 'error' | 'info' = 'info') => {
    const id = Math.random().toString(36).substr(2, 9);
    const toast: Toast = { id, message, type };
    setToasts(prev => [...prev, toast]);
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, 4000);
  }, []);

  const removeToast = useCallback((id: string) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  }, []);

  // Data Loading
  // loadHoneypots no longer toggles global `loading` (handled by loadAllData)
  const loadHoneypots = useCallback(async () => {
    try {
      const data = await deceptionService.listHoneypots();
      setHoneypots(data);
    } catch (error) {
      console.error('Failed to load honeypots:', error);
      addToast('Failed to load honeypots', 'error');
    }
  }, [addToast]);

  const loadEvents = useCallback(async (honeypotId?: string) => {
    try {
      const data = await deceptionService.listInteractionEvents(honeypotId);
      setEvents(data);
    } catch (error) {
      console.error('Failed to load events:', error);
    }
  }, []);

  const loadStats = useCallback(async () => {
    try {
      const data = await deceptionService.getDeceptionStats();
      setStats(data);
    } catch (error) {
      console.error('Failed to load stats:', error);
    }
  }, []);

  // Load all data with a single global loading state for smoother transitions.
  const loadAllData = useCallback(async () => {
    setLoading(true);
    try {
      await Promise.all([loadHoneypots(), loadEvents(), loadStats()]);
    } catch (err) {
      // Errors handled by individual loaders where appropriate
      console.error('Error loading deception data:', err);
    } finally {
      // small delay to avoid flicker when operations are fast
      setTimeout(() => setLoading(false), 200);
    }
  }, [loadHoneypots, loadEvents, loadStats]);

  useEffect(() => {
    loadAllData();
    const interval = setInterval(() => {
      if (autoRefresh) loadAllData();
    }, 5000);
    return () => clearInterval(interval);
  }, [autoRefresh, loadAllData]);

  // Honeypot Management
  const startHoneypot = async (honeypot: Honeypot) => {
    try {
      setLoadingStates(prev => ({ ...prev, [honeypot.id]: true }));
      addToast(`Starting honeypot ${honeypot.name}...`, 'info');
      await deceptionService.startHoneypot(honeypot.id);
      addToast(`${honeypot.name} started successfully!`, 'success');
      await loadHoneypots();
    } catch (error) {
      console.error('Failed to start honeypot:', error);
      addToast(`Failed to start ${honeypot.name}`, 'error');
    } finally {
      setLoadingStates(prev => ({ ...prev, [honeypot.id]: false }));
    }
  };

  const stopHoneypot = async (honeypot: Honeypot) => {
    try {
      setLoadingStates(prev => ({ ...prev, [honeypot.id]: true }));
      addToast(`Stopping honeypot ${honeypot.name}...`, 'info');
      await deceptionService.stopHoneypot(honeypot.id);
      addToast(`${honeypot.name} stopped successfully!`, 'success');
      await loadHoneypots();
    } catch (error) {
      console.error('Failed to stop honeypot:', error);
      addToast(`Failed to stop ${honeypot.name}`, 'error');
    } finally {
      setLoadingStates(prev => ({ ...prev, [honeypot.id]: false }));
    }
  };

  // Filtering & Search
  const filteredHoneypots = useMemo(() => {
    return honeypots.filter(hp => {
      const matchesSearch = hp.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           hp.platform.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesStatus = activeFilters.status.length === 0 || activeFilters.status.includes(hp.status);
      const matchesThreat = activeFilters.threatLevel.length === 0 || activeFilters.threatLevel.includes(hp.threatLevel);
      const matchesPlatform = activeFilters.platform.length === 0 || activeFilters.platform.includes(hp.platform);
      const matchesType = activeFilters.type.length === 0 || activeFilters.type.includes(hp.type);

      return matchesSearch && matchesStatus && matchesThreat && matchesPlatform && matchesType;
    }).sort((a, b) => {
      if (sortBy === 'interactions') {
        return b.interactionCount - a.interactionCount;
      } else if (sortBy === 'threatLevel') {
        const threatOrder = { critical: 4, high: 3, medium: 2, low: 1 };
        return threatOrder[b.threatLevel] - threatOrder[a.threatLevel];
      } else {
        return (b.lastInteraction || 0) - (a.lastInteraction || 0);
      }
    });
  }, [honeypots, searchTerm, activeFilters, sortBy]);

  const filteredEvents = useMemo(() => {
    const base = selectedHoneypot
      ? events.filter(e => e.honeypotId === selectedHoneypot.id)
      : events;
    return base.sort((a, b) => b.timestamp - a.timestamp).slice(0, 50);
  }, [events, selectedHoneypot]);

  const toggleFilter = (filterType: FilterType, value: string) => {
    setActiveFilters(prev => ({
      ...prev,
      [filterType]: prev[filterType].includes(value)
        ? prev[filterType].filter(f => f !== value)
        : [...prev[filterType], value],
    }));
  };

  // Export Logs
  const exportLogs = async () => {
    try {
      const path = await deceptionService.exportLogs();
      console.log('Logs exported to:', path);
      // Trigger download
      const link = document.createElement('a');
      link.href = path;
      link.download = 'deception-logs.json';
      link.click();
    } catch (error) {
      console.error('Failed to export logs:', error);
    }
  };

  // Honeypot Creation
  const handleCreateHoneypot = async () => {
    if (!newName.trim()) return addToast('Name is required', 'error');
    setCreating(true);
    try {
      const cfg = newConfig ? JSON.parse(newConfig) : undefined;
      await deceptionService.createHoneypot({
        name: newName,
        type: newServiceType,
        port: typeof newPort === 'number' ? newPort : 0,
        config: cfg,
      } as any);
      addToast('Honeypot deployed', 'success');
      setShowCreateModal(false);
      setNewName('');
      setNewServiceType('SSH');
      setNewPort('');
      setNewConfig('');
      await loadAllData();
    } catch (err: any) {
      console.error('Failed to create honeypot', err);
      addToast(`Failed to deploy honeypot: ${err?.message || 'error'}`, 'error');
    } finally {
      setCreating(false);
    }
  };

  // Utility Functions
  const getThreatColor = (level: string): string => {
    const colors = {
      low: '#10b981',
      medium: '#f59e0b',
      high: '#ef4444',
      critical: '#dc2626',
    };
    return colors[level as keyof typeof colors] || '#6b7280';
  };

  const getThreatClass = (level: string): string => {
    const classes = {
      low: 'threat-low',
      medium: 'threat-medium',
      high: 'threat-high',
      critical: 'threat-critical',
    };
    return classes[level as keyof typeof classes] || 'threat-low';
  };

  const getThreatBadgeClass = (level: string): string => {
    const classes = {
      low: 'threat-badge-low',
      medium: 'threat-badge-medium',
      high: 'threat-badge-high',
      critical: 'threat-badge-critical',
    };
    return classes[level as keyof typeof classes] || 'threat-badge-low';
  };

  const getThreatIndicatorClass = (level: string): string => {
    const classes = {
      low: 'indicator-low',
      medium: 'indicator-medium',
      high: 'indicator-high',
      critical: 'indicator-critical',
    };
    return classes[level as keyof typeof classes] || 'indicator-low';
  };

  const getStatusClass = (status: string): string => {
    if (status === 'running') return 'status-running';
    if (status === 'error') return 'status-error';
    return 'status-stopped';
  };

  const getStatusIcon = (status: string) => {
    return status === 'running' ? (
      <Activity className="w-4 h-4 text-green-500" />
    ) : status === 'error' ? (
      <AlertTriangle className="w-4 h-4 text-red-500" />
    ) : (
      <Server className="w-4 h-4 text-gray-500" />
    );
  };

  const formatTimestamp = (ts: number): string => {
    return new Date(ts * 1000).toLocaleString();
  };

  const formatUptime = (deployedAt: number): string => {
    const seconds = Math.floor((Date.now() / 1000) - deployedAt);
    const hours = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${mins}m`;
  };

  // Render: Statistics Dashboard
  const renderStats = () => {
    if (!stats) return null;

    return (
      <div className="deception-stats-dashboard">
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-header">
              <Server className="w-5 h-5" />
              <span>Active Honeypots</span>
            </div>
            <div className="stat-value">{stats.activeHoneypots}/{stats.totalHoneypots}</div>
            <div className="stat-bar">
              <div
                className="stat-bar-fill"
                style={{
                  width: `${(stats.activeHoneypots / stats.totalHoneypots) * 100}%`,
                }}
              />
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-header">
              <Zap className="w-5 h-5" />
              <span>Total Interactions</span>
            </div>
            <div className="stat-value">{stats.totalInteractions}</div>
            <div className="stat-meta">
              <TrendingUp className="w-4 h-4" />
              {Math.floor(stats.totalInteractions / 24)} per hour avg
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-header">
              <AlertTriangle className="w-5 h-5" />
              <span>Threat Level</span>
            </div>
            <div className={`stat-value threat ${getThreatClass(stats.threatLevel)}`}>
              {stats.threatLevel.toUpperCase()}
            </div>
            <div className="stat-meta">System-wide assessment</div>
          </div>

          <div className="stat-card">
            <div className="stat-header">
              <Network className="w-5 h-5" />
              <span>Decoy Models</span>
            </div>
            <div className="stat-value">{stats.decoyModelsDeployed}</div>
            <div className="stat-meta">AI-driven deception</div>
          </div>
        </div>
      </div>
    );
  };

  // Render: Honeypot Grid
  const renderHoneypotGrid = () => {
    return (
      <div className="honeypot-grid-container">
        <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {filteredHoneypots.map(hp => (
            <div
              key={hp.id}
              className={`honeypot-card ${hp.status === 'running' ? 'active' : ''} ${
                selectedHoneypot?.id === hp.id ? 'selected' : ''
              }`}
              onClick={() => setSelectedHoneypot(hp)}
            >
              <div className="honeypot-card-header">
                <div className="honeypot-title">
                  <div className={`status-indicator ${getThreatIndicatorClass(hp.threatLevel)}`} />
                  <div>
                    <h3>{hp.name}</h3>
                    <p className="type-badge">{hp.type}</p>
                  </div>
                </div>
                {getStatusIcon(hp.status)}
              </div>

              <div className="honeypot-card-body">
                <div className="info-row">
                  <MapPin className="w-4 h-4" />
                  <span>{hp.platform}</span>
                </div>
                <div className="info-row">
                  <Network className="w-4 h-4" />
                  <span>Port {hp.port}</span>
                </div>
                <div className="info-row">
                  <Clock className="w-4 h-4" />
                  <span>Up {formatUptime(hp.deployedAt)}</span>
                </div>
                <div className={`threat-badge ${getThreatBadgeClass(hp.threatLevel)}`}>
                  {hp.threatLevel.toUpperCase()} THREAT
                </div>
              </div>

              <div className="honeypot-card-stats">
                <div className="stat">
                  <div className="stat-label">Interactions</div>
                  <div className="stat-number">{hp.interactionCount}</div>
                </div>
                <div className="stat">
                  <div className="stat-label">Status</div>
                  <div className={`stat-number status ${getStatusClass(hp.status)}`}>
                    {hp.status.toUpperCase()}
                  </div>
                </div>
              </div>

              <div className="honeypot-card-actions">
                {hp.status === 'running' ? (
                  <button
                    className="action-btn stop"
                    disabled={loadingStates[hp.id]}
                    onClick={e => {
                      e.stopPropagation();
                      stopHoneypot(hp);
                    }}
                  >
                    {loadingStates[hp.id] ? (
                      <>
                        <Loader className="w-4 h-4 animate-spin" />
                        Stopping...
                      </>
                    ) : (
                      'Stop'
                    )}
                  </button>
                ) : (
                  <button
                    className="action-btn start"
                    disabled={loadingStates[hp.id]}
                    onClick={e => {
                      e.stopPropagation();
                      startHoneypot(hp);
                    }}
                  >
                    {loadingStates[hp.id] ? (
                      <>
                        <Loader className="w-4 h-4 animate-spin" />
                        Starting...
                      </>
                    ) : (
                      'Start'
                    )}
                  </button>
                )}
                <button
                  className="action-btn details"
                  onClick={e => {
                    e.stopPropagation();
                    setSelectedHoneypot(hp);
                    setShowDetailPane(true);
                  }}
                >
                  Details
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  // Render: Event Timeline
  const renderEventTimeline = () => {
    return (
      <div className="event-timeline-container">
        <div className="timeline">
          {filteredEvents.map((event) => (
            <div key={event.id} className="timeline-item">
              <div className={`timeline-marker ${getThreatIndicatorClass(event.severity)}`} />
              <div className="timeline-content">
                <div className="event-header">
                  <span className="event-honeypot">{event.honeypotName}</span>
                  <span className="event-time">{formatTimestamp(event.timestamp)}</span>
                </div>
                <p className="event-payload">{event.payloadSummary}</p>
                <div className="event-details">
                  <span className="detail-badge">
                    <Globe className="w-3 h-3" />
                    {event.clientIp}:{event.clientPort}
                  </span>
                  <span className={`severity-badge ${event.severity}`}>
                    {event.severity.toUpperCase()}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  // Render: Analytics Dashboard
  const renderAnalytics = () => {
    if (!stats) return null;

    const threatDistribution = honeypots.reduce((acc, hp) => {
      acc[hp.threatLevel] = (acc[hp.threatLevel] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    const platformDistribution = honeypots.reduce((acc, hp) => {
      acc[hp.platform] = (acc[hp.platform] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    return (
      <div className="analytics-dashboard">
        <div className="analytics-row">
          <div className="analytics-card">
            <h3>Threat Distribution</h3>
            <div className="chart-container">
              {Object.entries(threatDistribution).map(([threat, count]) => (
                <div key={threat} className="chart-bar">
                  <div className="bar-label">{threat}</div>
                  <div className="bar-track">
                    <div
                      className="bar-fill"
                      style={{
                        width: `${(count / honeypots.length) * 100}%`,
                        backgroundColor: getThreatColor(threat),
                      }}
                    />
                  </div>
                  <div className="bar-value">{count}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="analytics-card">
            <h3>Platform Distribution</h3>
            <div className="chart-container">
              {Object.entries(platformDistribution).map(([platform, count]) => (
                <div key={platform} className="chart-bar">
                  <div className="bar-label">{platform}</div>
                  <div className="bar-track">
                    <div
                      className="bar-fill"
                      style={{
                        width: `${(count / honeypots.length) * 100}%`,
                        backgroundColor: '#3b82f6',
                      }}
                    />
                  </div>
                  <div className="bar-value">{count}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="analytics-card">
            <h3>Honeypot Type Distribution</h3>
            <div className="chart-container">
              {honeypots.reduce((acc, hp) => {
                const existing = acc.find(x => x.type === hp.type);
                if (existing) existing.count++;
                else acc.push({ type: hp.type, count: 1 });
                return acc;
              }, [] as Array<{ type: string; count: number }>).map(item => (
                <div key={item.type} className="chart-bar">
                  <div className="bar-label">{item.type}</div>
                  <div className="bar-track">
                    <div
                      className="bar-fill"
                      style={{
                        width: `${(item.count / honeypots.length) * 100}%`,
                        backgroundColor: '#8b5cf6',
                      }}
                    />
                  </div>
                  <div className="bar-value">{item.count}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  };

  // Render: Detail Pane
  const renderDetailPane = () => {
    if (!selectedHoneypot || !showDetailPane) return null;

    const hpEvents = events.filter(e => e.honeypotId === selectedHoneypot.id);

    return (
      <div className="detail-pane-overlay" onClick={() => setShowDetailPane(false)}>
        <div className="detail-pane" onClick={e => e.stopPropagation()}>
          <div className="detail-header">
            <h2>{selectedHoneypot.name}</h2>
            <button className="close-btn" onClick={() => setShowDetailPane(false)}>
              ×
            </button>
          </div>

          <div className="detail-content">
            <section className="detail-section">
              <h3>Configuration</h3>
              <div className="detail-grid">
                <div className="detail-item">
                  <label>Type</label>
                  <span>{selectedHoneypot.type}</span>
                </div>
                <div className="detail-item">
                  <label>Platform</label>
                  <span>{selectedHoneypot.platform}</span>
                </div>
                <div className="detail-item">
                  <label>Port</label>
                  <span>{selectedHoneypot.port}</span>
                </div>
                <div className="detail-item">
                  <label>Status</label>
                  <span className={getStatusClass(selectedHoneypot.status)}>
                    {selectedHoneypot.status.toUpperCase()}
                  </span>
                </div>
              </div>
            </section>

            <section className="detail-section">
              <h3>Metrics</h3>
              <div className="detail-grid">
                <div className="detail-item">
                  <label>Interactions</label>
                  <span>{selectedHoneypot.interactionCount}</span>
                </div>
                <div className="detail-item">
                  <label>Threat Level</label>
                  <span className={getThreatClass(selectedHoneypot.threatLevel)}>
                    {selectedHoneypot.threatLevel.toUpperCase()}
                  </span>
                </div>
                <div className="detail-item">
                  <label>Deployed</label>
                  <span>{formatUptime(selectedHoneypot.deployedAt)} ago</span>
                </div>
                <div className="detail-item">
                  <label>Last Activity</label>
                  <span>
                    {selectedHoneypot.lastInteraction
                      ? formatTimestamp(selectedHoneypot.lastInteraction)
                      : 'Never'}
                  </span>
                </div>
              </div>
            </section>

            <section className="detail-section">
              <h3>Recent Events ({hpEvents.length})</h3>
              <div className="events-list">
                {hpEvents.slice(0, 10).map(event => (
                  <div key={event.id} className="event-item">
                    <div className="event-summary">
                      <span className={`event-severity ${event.severity}`}>{event.severity}</span>
                      <span className="event-payload">{event.payloadSummary}</span>
                    </div>
                    <div className="event-meta">
                      <Globe className="w-3 h-3" />
                      {event.clientIp}:{event.clientPort}
                    </div>
                    <div className="event-time">{formatTimestamp(event.timestamp)}</div>
                  </div>
                ))}
              </div>
            </section>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="deception-grid-container">
      {/* Toast Notifications */}
      <div className="toast-container">
        {toasts.map(toast => (
          <div key={toast.id} className={`toast toast-${toast.type}`}>
            <span>{toast.message}</span>
            <button className="toast-close" onClick={() => removeToast(toast.id)}>
              ×
            </button>
          </div>
        ))}
      </div>

      {/* Header */}
      <div className="deception-header">
        <div className="header-left">
          <div className="header-icon">
            <Shield className="w-6 h-6" />
          </div>
          <div className="header-title">
            <h1>Deception Grid</h1>
            <p>Advanced Honeypot & Threat Trap Management</p>
          </div>
        </div>
        <div className="header-controls">
          <button
            className={`control-btn ${autoRefresh ? 'active' : ''}`}
            onClick={() => setAutoRefresh(!autoRefresh)}
          >
            <RefreshCw className="w-4 h-4" />
            {autoRefresh ? 'Auto-refresh' : 'Manual'}
          </button>
          <button className="control-btn" onClick={loadAllData}>
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
          <button className="control-btn" onClick={exportLogs}>
            <Download className="w-4 h-4" />
            Export Logs
          </button>
          <button
            className="control-btn"
            onClick={() => setShowCreateModal(true)}
            title="Deploy honeypot"
          >
            <Zap className="w-4 h-4" />
            Deploy
          </button>
        </div>
      </div>

      {/* Statistics */}
      {renderStats()}

      {/* Controls & Filters */}
      <div className="deception-controls">
        <div className="search-bar">
          <Search className="w-4 h-4" />
          <input
            type="text"
            placeholder="Search honeypots..."
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
          />
        </div>

        <div className="filter-buttons">
          <div className="filter-group">
            <label>Status:</label>
            {['running', 'stopped', 'error'].map(status => (
              <button
                key={status}
                className={`filter-btn ${activeFilters.status.includes(status) ? 'active' : ''}`}
                onClick={() => toggleFilter('status', status)}
              >
                {status}
              </button>
            ))}
          </div>

          <div className="filter-group">
            <label>Threat:</label>
            {['low', 'medium', 'high', 'critical'].map(threat => (
              <button
                key={threat}
                className={`filter-btn ${activeFilters.threatLevel.includes(threat) ? 'active' : ''}`}
                onClick={() => toggleFilter('threatLevel', threat)}
              >
                {threat}
              </button>
            ))}
          </div>

          <div className="filter-group">
            <label>Sort:</label>
            {(['interactions', 'threatLevel', 'timestamp'] as const).map(sort => (
              <button
                key={sort}
                className={`filter-btn ${sortBy === sort ? 'active' : ''}`}
                onClick={() => setSortBy(sort)}
              >
                {sort === 'interactions' ? 'Interactions' : sort === 'threatLevel' ? 'Threat' : 'Recent'}
              </button>
            ))}
          </div>
        </div>

        <div className="view-toggle">
          {(['grid', 'list', 'analytics', 'timeline'] as const).map(mode => (
            <button
              key={mode}
              className={`view-btn ${viewMode === mode ? 'active' : ''}`}
              onClick={() => setViewMode(mode)}
              title={mode}
            >
              {mode === 'grid' && <Grid3x3 className="w-4 h-4" />}
              {mode === 'list' && <Menu className="w-4 h-4" />}
              {mode === 'analytics' && <BarChart3 className="w-4 h-4" />}
              {mode === 'timeline' && <Clock className="w-4 h-4" />}
            </button>
          ))}
        </div>
      </div>

      {/* Main Content */}
      <div className="deception-content">
        {loading ? (
          <div className="loading-state">
            <div className="global-loading-overlay">
              <div className="overlay-card">
                <Loader className="w-10 h-10 animate-spin" />
                <p>Loading deception grid...</p>
              </div>
            </div>
            {/* skeleton grid for quick visual feedback */}
            <div className="honeypot-grid-skeleton">
              {Array.from({ length: 8 }).map((_, i) => (
                <div key={i} className="skeleton-card">
                  <div className="skeleton-header" />
                  <div className="skeleton-body">
                    <div className="skeleton-line short" />
                    <div className="skeleton-line" />
                    <div className="skeleton-line" />
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : viewMode === 'grid' ? (
          renderHoneypotGrid()
        ) : viewMode === 'list' ? (
          <div className="honeypot-list-container">
            <table className="honeypot-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Type</th>
                  <th>Platform</th>
                  <th>Port</th>
                  <th>Status</th>
                  <th>Threat</th>
                  <th>Interactions</th>
                  <th>Uptime</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredHoneypots.map(hp => (
                  <tr key={hp.id} className={hp.status === 'running' ? 'active' : ''}>
                    <td className="name-cell">{hp.name}</td>
                    <td>{hp.type}</td>
                    <td>{hp.platform}</td>
                    <td>{hp.port}</td>
                    <td>
                      <span className={`status-badge ${getStatusClass(hp.status)}`}>
                        {getStatusIcon(hp.status)}
                        {hp.status}
                      </span>
                    </td>
                    <td>
                      <span className={`threat-badge-inline ${getThreatBadgeClass(hp.threatLevel)}`}>
                        {hp.threatLevel}
                      </span>
                    </td>
                    <td className="interactions-cell">{hp.interactionCount}</td>
                    <td>{formatUptime(hp.deployedAt)}</td>
                    <td className="actions-cell">
                      {hp.status === 'running' ? (
                        <button
                          className="action-btn-small stop"
                          disabled={loadingStates[hp.id]}
                          onClick={() => stopHoneypot(hp)}
                        >
                          {loadingStates[hp.id] ? (
                            <>
                              <Loader className="w-3 h-3 animate-spin" />
                              Stopping...
                            </>
                          ) : (
                            'Stop'
                          )}
                        </button>
                      ) : (
                        <button
                          className="action-btn-small start"
                          disabled={loadingStates[hp.id]}
                          onClick={() => startHoneypot(hp)}
                        >
                          {loadingStates[hp.id] ? (
                            <>
                              <Loader className="w-3 h-3 animate-spin" />
                              Starting...
                            </>
                          ) : (
                            'Start'
                          )}
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : viewMode === 'analytics' ? (
          renderAnalytics()
        ) : (
          renderEventTimeline()
        )}
      </div>

      {/* Detail Pane */}
      {renderDetailPane()}
      {/* Create Honeypot Modal */}
      {showCreateModal && (
        <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
          <div className="modal-card" onClick={e => e.stopPropagation()}>
            <h3>Deploy Honeypot</h3>
            <div className="modal-field">
              <label htmlFor="hp-name">Name</label>
              <input id="hp-name" title="honeypot name" placeholder="e.g. SSH Honeypot" value={newName} onChange={e => setNewName(e.target.value)} />
            </div>
            <div className="modal-field">
              <label htmlFor="hp-type">Service Type</label>
              <select id="hp-type" title="service type" value={newServiceType} onChange={e => setNewServiceType(e.target.value)}>
                <option>SSH</option>
                <option>HTTP</option>
                <option>FTP</option>
                <option>SMTP</option>
                <option>PostgreSQL</option>
              </select>
            </div>
            <div className="modal-field">
              <label>Port (optional)</label>
              <input
                id="hp-port"
                title="port"
                placeholder="e.g. 22"
                type="number"
                value={newPort === '' ? '' : newPort}
                onChange={e => setNewPort(e.target.value === '' ? '' : Number(e.target.value))}
              />
            </div>
            <div className="modal-field">
              <label htmlFor="hp-config">Config (JSON)</label>
              <textarea id="hp-config" title="config" placeholder='{"key":"value"}' value={newConfig} onChange={e => setNewConfig(e.target.value)} rows={4} />
            </div>
            <div className="modal-actions">
              <button className="control-btn" onClick={() => setShowCreateModal(false)}>Cancel</button>
              <button className="control-btn" onClick={handleCreateHoneypot} disabled={creating}>
                {creating ? 'Deploying...' : 'Deploy'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DeceptionGrid;
