/**
 * IDS Threats Dashboard Page
 * Real-time threat detection and alert management interface
 * 
 * Features:
 * - Live threat timeline with threat levels
 * - Alert list with filtering and sorting
 * - Threat details with explanations
 * - Alert investigation workflow
 * - Model status monitoring
 * - System metrics and statistics
 */

import React, { useState, useEffect } from "react";
import {
  Container,
  Row,
  Col,
  Card,
  ListGroup,
  Badge,
  Button,
  Modal,
  Form,
  Tab,
  Nav,
  Spinner,
  ProgressBar,
} from "react-bootstrap";
import {
  AlertTriangle,
  AlertOctagon,
  AlertCircle,
  Info,
  TrendingUp,
  Activity,
  Shield,
  Zap,
} from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from "recharts";
import { useWebSocket } from "../hooks/useWebSocket";
import styles from "./IDSThreats.module.scss";

// ============================================================================
// TYPE DEFINITIONS
// ============================================================================

interface ThreatAlert {
  alert_id: string;
  timestamp: string;
  threat_level: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "INFO";
  threat_score: number;
  confidence: number;
  threat_name: string;
  threat_category: string;
  threat_description: string;
  flow_info: {
    src_ip: string;
    dst_ip: string;
    src_port: number;
    dst_port: number;
    protocol: string;
    dpi_app?: string;
  };
  host_risk_context: {
    src_risk_score?: number;
    dst_risk_score?: number;
    src_vulnerabilities?: number;
    dst_vulnerabilities?: number;
  };
  network_context: {
    geographic_distance?: number;
    first_seen?: string;
    last_seen?: string;
    interaction_count?: number;
  };
  recommended_actions: string[];
  status: "open" | "investigating" | "escalated" | "resolved" | "false_positive";
  assigned_analyst?: string;
}

interface Explanation {
  alert_id: string;
  explanation_method: string;
  primary_reasons: string[];
  secondary_reasons: string[];
  confidence: number;
  narrative: string;
  feature_contributions?: Record<string, number>;
}

interface ModelStatus {
  model_id: string;
  model_name: string;
  model_type: string;
  status: string;
  version: string;
  accuracy: number;
  auc_roc: number;
  drift_score: number;
  retraining_required: boolean;
}

interface Metrics {
  engine_id: string;
  uptime_seconds: number;
  total_flows_analyzed: number;
  total_threats_detected: number;
  detection_rate: number;
  threat_distribution: Record<string, number>;
  active_models: number;
  open_alerts: number;
  model_status: Record<string, unknown>;
}

// ============================================================================
// COLOR MAPPING
// ============================================================================

const THREAT_LEVEL_COLORS: Record<string, string> = {
  CRITICAL: "#dc3545",
  HIGH: "#fd7e14",
  MEDIUM: "#ffc107",
  LOW: "#0dcaf0",
  INFO: "#6c757d",
};

const THREAT_LEVEL_ICONS: Record<string, React.ReactNode> = {
  CRITICAL: <AlertOctagon className="text-danger" size={20} />,
  HIGH: <AlertTriangle className="text-warning" size={20} />,
  MEDIUM: <AlertCircle className="text-warning" size={20} />,
  LOW: <Info className="text-info" size={20} />,
  INFO: <Info className="text-muted" size={20} />,
};

// ============================================================================
// ALERT TIMELINE COMPONENT
// ============================================================================

interface AlertTimelineProps {
  alerts: ThreatAlert[];
  _onSelectAlert?: (alert: ThreatAlert) => void;
  _selectedAlertId?: string;
}

const AlertTimeline: React.FC<AlertTimelineProps> = ({
  alerts,
  _onSelectAlert,
  _selectedAlertId,
}) => {
  // mark intentionally unused props as referenced to avoid declared-but-not-used errors
  void _onSelectAlert
  void _selectedAlertId

  // Group alerts by hour for timeline
  const timelineData = React.useMemo(() => {
    const grouped: Record<string, number> = {};

    alerts.forEach((alert) => {
      const hour = new Date(alert.timestamp).toISOString().slice(0, 13);
      grouped[hour] = (grouped[hour] || 0) + 1;
    });

    return Object.entries(grouped)
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([hour, count]) => ({
        hour,
        count,
        timestamp: new Date(hour + ":00:00Z"),
      }));
  }, [alerts]);

  return (
    <Card className={styles.alertTimeline}>
      <Card.Header className="d-flex align-items-center gap-2">
        <TrendingUp size={20} className="text-danger" />
        <Card.Title className="mb-0">Threat Timeline</Card.Title>
      </Card.Header>
      <Card.Body>
        {timelineData.length > 0 ? (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={timelineData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="hour"
                tick={{ fontSize: 12 }}
              />
              <YAxis />
              <Tooltip
                labelFormatter={(value: unknown) => {
                  if (typeof value === "string") return value;
                  return new Date(String(value)).toLocaleString();
                }}
              />
              <Bar
                dataKey="count"
                fill="#dc3545"
                radius={[8, 8, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div className="text-center text-muted py-4">
            No threats detected
          </div>
        )}
      </Card.Body>
    </Card>
  );
};

// ============================================================================
// ALERT DETAILS MODAL
// ============================================================================

interface AlertDetailsModalProps {
  show: boolean;
  alert: ThreatAlert | null;
  explanation: Explanation | null;
  loading: boolean;
  onHide: () => void;
  onStatusUpdate: (alert_id: string, status: string, notes: string) => void;
}

const AlertDetailsModal: React.FC<AlertDetailsModalProps> = ({
  show,
  alert,
  explanation,
  loading,
  onHide,
  onStatusUpdate,
}) => {
  const [investigationNotes, setInvestigationNotes] = useState("");
  const [selectedStatus, setSelectedStatus] = useState("investigating");

  if (!alert) return null;

  return (
    <Modal show={show} onHide={onHide} size="lg" className={styles.alertModal}>
      <Modal.Header closeButton className="bg-light">
        <Modal.Title className="d-flex align-items-center gap-2">
          {THREAT_LEVEL_ICONS[alert.threat_level]}
          {alert.threat_name}
        </Modal.Title>
      </Modal.Header>
      <Modal.Body className={styles.modalBody}>
        <Tab.Container defaultActiveKey="overview">
          <Nav variant="tabs" className="mb-3">
            <Nav.Item>
              <Nav.Link eventKey="overview">Overview</Nav.Link>
            </Nav.Item>
            <Nav.Item>
              <Nav.Link eventKey="explanation">
                Explanation
              </Nav.Link>
            </Nav.Item>
            <Nav.Item>
              <Nav.Link eventKey="investigation">
                Investigation
              </Nav.Link>
            </Nav.Item>
          </Nav>

          <Tab.Content>
            {/* Overview Tab */}
            <Tab.Pane eventKey="overview">
              <Row className="mb-3">
                <Col md={6}>
                  <div className={styles.infoGroup}>
                    <span className="text-muted">Alert ID:</span>
                    <code className="d-block">{alert.alert_id}</code>
                  </div>
                </Col>
                <Col md={6}>
                  <div className={styles.infoGroup}>
                    <span className="text-muted">Timestamp:</span>
                    <div>{new Date(alert.timestamp).toLocaleString()}</div>
                  </div>
                </Col>
              </Row>

              <Row className="mb-3">
                <Col md={6}>
                  <div className={styles.infoGroup}>
                    <span className="text-muted">Threat Score:</span>
                    <ProgressBar
                      now={alert.threat_score * 100}
                      label={`${(alert.threat_score * 100).toFixed(1)}%`}
                      className="mt-2"
                      style={{
                        backgroundColor:
                          THREAT_LEVEL_COLORS[alert.threat_level],
                      }}
                    />
                  </div>
                </Col>
                <Col md={6}>
                  <div className={styles.infoGroup}>
                    <span className="text-muted">Confidence:</span>
                    <ProgressBar
                      now={alert.confidence * 100}
                      label={`${(alert.confidence * 100).toFixed(1)}%`}
                      className="mt-2"
                      variant="success"
                    />
                  </div>
                </Col>
              </Row>

              <div className={styles.infoGroup}>
                <span className="text-muted">Category:</span>
                <Badge bg="secondary" className="mt-2">
                  {alert.threat_category}
                </Badge>
              </div>

              <div className={styles.infoGroup}>
                <span className="text-muted">Description:</span>
                <p className="mt-2">{alert.threat_description}</p>
              </div>

              <div className={styles.flowInfo}>
                <h6 className="mb-3">Network Flow</h6>
                <Row>
                  <Col md={6}>
                    <div className={styles.flowDetail}>
                      <span className="text-muted">Source:</span>
                      <code>
                        {alert.flow_info.src_ip}:{alert.flow_info.src_port}
                      </code>
                    </div>
                  </Col>
                  <Col md={6}>
                    <div className={styles.flowDetail}>
                      <span className="text-muted">Destination:</span>
                      <code>
                        {alert.flow_info.dst_ip}:{alert.flow_info.dst_port}
                      </code>
                    </div>
                  </Col>
                </Row>
                <Row className="mt-2">
                  <Col md={6}>
                    <div className={styles.flowDetail}>
                      <span className="text-muted">Protocol:</span>
                      <Badge bg="info">{alert.flow_info.protocol}</Badge>
                    </div>
                  </Col>
                  {alert.flow_info.dpi_app && (
                    <Col md={6}>
                      <div className={styles.flowDetail}>
                        <span className="text-muted">DPI Application:</span>
                        <Badge bg="warning">{alert.flow_info.dpi_app}</Badge>
                      </div>
                    </Col>
                  )}
                </Row>
              </div>

              <div className={styles.recommendedActions}>
                <h6 className="mb-3">Recommended Actions</h6>
                <div className="d-flex flex-wrap gap-2">
                  {alert.recommended_actions.map((action, idx) => (
                    <Badge key={idx} bg="danger">
                      {action}
                    </Badge>
                  ))}
                </div>
              </div>
            </Tab.Pane>

            {/* Explanation Tab */}
            <Tab.Pane eventKey="explanation">
              {loading ? (
                <div className="text-center py-4">
                  <Spinner animation="border" size="sm" />
                  <p className="mt-2">Loading explanation...</p>
                </div>
              ) : explanation ? (
                <>
                  <div className={styles.infoGroup}>
                    <span className="text-muted">Method:</span>
                    <Badge bg="info" className="mt-2">
                      {explanation.explanation_method}
                    </Badge>
                  </div>

                  <div className={styles.infoGroup}>
                    <span className="text-muted">Confidence:</span>
                    <ProgressBar
                      now={explanation.confidence * 100}
                      label={`${(explanation.confidence * 100).toFixed(1)}%`}
                      className="mt-2"
                      variant="success"
                    />
                  </div>

                  <div className={styles.infoGroup}>
                    <span className="text-muted d-block mb-2">
                      Primary Reasons:
                    </span>
                    <ul className={styles.reasonsList}>
                      {explanation.primary_reasons.map((reason, idx) => (
                        <li key={idx}>{reason}</li>
                      ))}
                    </ul>
                  </div>

                  {explanation.secondary_reasons.length > 0 && (
                    <div className={styles.infoGroup}>
                      <span className="text-muted d-block mb-2">
                        Secondary Evidence:
                      </span>
                      <ul className={styles.reasonsList}>
                        {explanation.secondary_reasons.map((reason, idx) => (
                          <li key={idx}>{reason}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {explanation.feature_contributions && (
                    <div className={styles.infoGroup}>
                      <span className="text-muted d-block mb-2">
                        Feature Contributions:
                      </span>
                      <div className={styles.featureContributions}>
                        {Object.entries(
                          explanation.feature_contributions
                        ).map(([feature, importance]) => (
                          <div key={feature} className={styles.featureBar}>
                            <span className="text-muted">{feature}:</span>
                            <ProgressBar
                              now={Math.abs(importance) * 100}
                              label={`${(importance * 100).toFixed(1)}%`}
                              className="mt-1"
                              variant={importance > 0 ? "danger" : "success"}
                            />
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className={styles.narrative}>
                    <h6 className="mb-3">Analyst Narrative</h6>
                    <p>{explanation.narrative}</p>
                  </div>
                </>
              ) : (
                <div className="text-center text-muted py-4">
                  No explanation available
                </div>
              )}
            </Tab.Pane>

            {/* Investigation Tab */}
            <Tab.Pane eventKey="investigation">
              <Form.Group className="mb-3">
                <Form.Label>Update Status</Form.Label>
                <Form.Select
                  value={selectedStatus}
                  onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setSelectedStatus(e.target.value)}
                >
                  <option value="investigating">Investigating</option>
                  <option value="escalated">Escalated</option>
                  <option value="resolved">Resolved</option>
                  <option value="false_positive">False Positive</option>
                </Form.Select>
              </Form.Group>

              <Form.Group className="mb-3">
                <Form.Label>Investigation Notes</Form.Label>
                <Form.Control
                  as="textarea"
                  rows={4}
                  placeholder="Add investigation findings..."
                  value={investigationNotes}
                  onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setInvestigationNotes(e.target.value)}
                />
              </Form.Group>

              <Button
                variant="primary"
                onClick={() => {
                  onStatusUpdate(alert.alert_id, selectedStatus, investigationNotes);
                  onHide();
                }}
              >
                Update Status
              </Button>
            </Tab.Pane>
          </Tab.Content>
        </Tab.Container>
      </Modal.Body>
    </Modal>
  );
};

// ============================================================================
// ALERT LIST COMPONENT
// ============================================================================

interface AlertListProps {
  alerts: ThreatAlert[];
  loading: boolean;
  onSelectAlert: (alert: ThreatAlert) => void;
  selectedAlertId?: string;
}

const AlertList: React.FC<AlertListProps> = ({
  alerts,
  loading,
  onSelectAlert,
  selectedAlertId,
}) => {
  const [sortBy, setSortBy] = useState<"date" | "score" | "level">("date");
  const [filterLevel, setFilterLevel] = useState<string | null>(null);

  const sortedAlerts = React.useMemo(() => {
    let result = [...alerts];

    if (filterLevel) {
      result = result.filter((a) => a.threat_level === filterLevel);
    }

    result.sort((a, b) => {
      switch (sortBy) {
        case "score":
          return b.threat_score - a.threat_score;
        case "level":
          return (
            Object.values(THREAT_LEVEL_COLORS).indexOf(
              THREAT_LEVEL_COLORS[b.threat_level]
            ) -
            Object.values(THREAT_LEVEL_COLORS).indexOf(
              THREAT_LEVEL_COLORS[a.threat_level]
            )
          );
        default:
          return (
            new Date(b.timestamp).getTime() -
            new Date(a.timestamp).getTime()
          );
      }
    });

    return result;
  }, [alerts, sortBy, filterLevel]);

  return (
    <Card className={styles.alertList}>
      <Card.Header className="d-flex align-items-center justify-content-between">
        <Card.Title className="mb-0 d-flex align-items-center gap-2">
          <AlertTriangle size={20} className="text-danger" />
          Active Alerts ({sortedAlerts.length})
        </Card.Title>
      </Card.Header>
      <Card.Body className="p-0">
        {loading ? (
          <div className="text-center py-4">
            <Spinner animation="border" size="sm" />
          </div>
        ) : sortedAlerts.length > 0 ? (
          <>
            <div className={`${styles.controls} p-3 border-bottom`}>
              <Form.Group className="d-flex gap-3 mb-0">
                <div>
                  <Form.Label className="text-muted small">Sort By:</Form.Label>
                  <Form.Select
                    size="sm"
                    value={sortBy}
                    onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setSortBy(e.target.value as 'date' | 'score' | 'level')}
                    style={{ width: "150px" }}
                  >
                    <option value="date">Date</option>
                    <option value="score">Score</option>
                    <option value="level">Level</option>
                  </Form.Select>
                </div>
                <div>
                  <Form.Label className="text-muted small">
                    Filter Level:
                  </Form.Label>
                  <Form.Select
                    size="sm"
                    value={filterLevel || ""}
                    onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setFilterLevel(e.target.value || null)}
                    style={{ width: "150px" }}
                  >
                    <option value="">All</option>
                    <option value="CRITICAL">Critical</option>
                    <option value="HIGH">High</option>
                    <option value="MEDIUM">Medium</option>
                    <option value="LOW">Low</option>
                  </Form.Select>
                </div>
              </Form.Group>
            </div>

            <ListGroup variant="flush" className={styles.alertItems}>
              {sortedAlerts.slice(0, 20).map((alert) => (
                <ListGroup.Item
                  key={alert.alert_id}
                  className={`${styles.alertItem} ${selectedAlertId === alert.alert_id ? styles.selected : ""
                    }`}
                  onClick={() => onSelectAlert(alert)}
                  style={{ cursor: "pointer" }}
                >
                  <Row className="align-items-center">
                    <Col xs="auto">
                      {THREAT_LEVEL_ICONS[alert.threat_level]}
                    </Col>
                    <Col>
                      <div className={styles.alertName}>{alert.threat_name}</div>
                      <div className={styles.alertDetails}>
                        <span className="text-muted small">
                          {alert.flow_info.src_ip} →{" "}
                          {alert.flow_info.dst_ip}
                        </span>
                      </div>
                    </Col>
                    <Col xs="auto" className="text-end">
                      <Badge
                        style={{
                          backgroundColor:
                            THREAT_LEVEL_COLORS[alert.threat_level],
                        }}
                      >
                        {(alert.threat_score * 100).toFixed(0)}%
                      </Badge>
                      <div className={styles.timestamp}>
                        {new Date(alert.timestamp).toLocaleTimeString()}
                      </div>
                    </Col>
                  </Row>
                </ListGroup.Item>
              ))}
            </ListGroup>
          </>
        ) : (
          <div className="text-center text-muted py-4">
            No alerts detected
          </div>
        )}
      </Card.Body>
    </Card>
  );
};

// ============================================================================
// MODEL STATUS COMPONENT
// ============================================================================

interface ModelStatusProps {
  models: ModelStatus[];
}

const ModelStatusComponent: React.FC<ModelStatusProps> = ({ models }) => {
  return (
    <Card className={styles.modelStatus}>
      <Card.Header className="d-flex align-items-center gap-2">
        <Zap size={20} className="text-warning" />
        <Card.Title className="mb-0">Model Status</Card.Title>
      </Card.Header>
      <Card.Body>
        <ListGroup variant="flush">
          {models.map((model) => (
            <ListGroup.Item key={model.model_id}>
              <Row className="align-items-center">
                <Col>
                  <div className={styles.modelName}>{model.model_name}</div>
                  <small className="text-muted">{model.model_type}</small>
                </Col>
                <Col xs="auto">
                  <Badge
                    bg={
                      model.drift_score > 0.5
                        ? "danger"
                        : model.drift_score > 0.3
                          ? "warning"
                          : "success"
                    }
                  >
                    {model.retraining_required ? "Needs Retrain" : "Active"}
                  </Badge>
                </Col>
              </Row>
              <div className="mt-2">
                <small className="text-muted d-block">
                  Accuracy: {(model.accuracy * 100).toFixed(1)}% | AUC-ROC:{" "}
                  {model.auc_roc.toFixed(3)}
                </small>
                <ProgressBar
                  now={model.drift_score * 100}
                  label={`Drift: ${(model.drift_score * 100).toFixed(1)}%`}
                  className="mt-1"
                  variant={
                    model.drift_score > 0.5
                      ? "danger"
                      : model.drift_score > 0.3
                        ? "warning"
                        : "success"
                  }
                />
              </div>
            </ListGroup.Item>
          ))}
        </ListGroup>
      </Card.Body>
    </Card>
  );
};

// ============================================================================
// METRICS SUMMARY COMPONENT
// ============================================================================

interface MetricsSummaryProps {
  metrics: Metrics | null;
}

const MetricsSummary: React.FC<MetricsSummaryProps> = ({ metrics }) => {
  if (!metrics) return null;

  const _threatDistribution = Object.entries(metrics.threat_distribution).map(
    ([name, count]) => ({ name, value: count })
  )
  void _threatDistribution

  return (
    <Row className="mb-4">
      <Col md={6} lg={3}>
        <Card className={styles.metricCard}>
          <Card.Body>
            <div className="d-flex align-items-center justify-content-between">
              <div>
                <p className="text-muted mb-1">Flows Analyzed</p>
                <h4 className="mb-0">
                  {(metrics.total_flows_analyzed / 1000).toFixed(1)}K
                </h4>
              </div>
              <Activity size={32} className="text-info opacity-50" />
            </div>
          </Card.Body>
        </Card>
      </Col>

      <Col md={6} lg={3}>
        <Card className={styles.metricCard}>
          <Card.Body>
            <div className="d-flex align-items-center justify-content-between">
              <div>
                <p className="text-muted mb-1">Threats Detected</p>
                <h4 className="mb-0">{metrics.total_threats_detected}</h4>
              </div>
              <AlertTriangle size={32} className="text-danger opacity-50" />
            </div>
          </Card.Body>
        </Card>
      </Col>

      <Col md={6} lg={3}>
        <Card className={styles.metricCard}>
          <Card.Body>
            <div className="d-flex align-items-center justify-content-between">
              <div>
                <p className="text-muted mb-1">Detection Rate</p>
                <h4 className="mb-0">
                  {(metrics.detection_rate * 100).toFixed(2)}%
                </h4>
              </div>
              <TrendingUp size={32} className="text-success opacity-50" />
            </div>
          </Card.Body>
        </Card>
      </Col>

      <Col md={6} lg={3}>
        <Card className={styles.metricCard}>
          <Card.Body>
            <div className="d-flex align-items-center justify-content-between">
              <div>
                <p className="text-muted mb-1">Active Alerts</p>
                <h4 className="mb-0">{metrics.open_alerts}</h4>
              </div>
              <Shield size={32} className="text-warning opacity-50" />
            </div>
          </Card.Body>
        </Card>
      </Col>
    </Row>
  );
};

// ============================================================================
// MAIN PAGE COMPONENT
// ============================================================================

const IDSThreats: React.FC = () => {
  const { send: _wsConnect, message: wsMessage } = useWebSocket("/ws/ids");

  const [alerts, setAlerts] = useState<ThreatAlert[]>([]);
  const [selectedAlert, setSelectedAlert] = useState<ThreatAlert | null>(null);
  const [explanation, setExplanation] = useState<Explanation | null>(null);
  const [models, setModels] = useState<ModelStatus[]>([]);
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [loading, setLoading] = useState(false);
  const [showAlertModal, setShowAlertModal] = useState(false);

  // Fetch initial data
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);

        // Fetch alerts
        const alertsRes = await fetch("/api/ids/alerts?limit=100");
        const alertsData = await alertsRes.json();
        setAlerts(alertsData);

        // Fetch models
        const modelsRes = await fetch("/api/ids/models/status");
        const modelsData = await modelsRes.json();
        setModels(modelsData);

        // Fetch metrics
        const metricsRes = await fetch("/api/ids/metrics");
        const metricsData = await metricsRes.json();
        setMetrics(metricsData);
      } catch (err) {
        console.error("Failed to fetch IDS data:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  // Handle WebSocket messages for real-time alerts
  useEffect(() => {
    if (wsMessage && typeof wsMessage === 'string') {
      try {
        const newAlert = JSON.parse(wsMessage) as ThreatAlert;
        setAlerts((prev) => [newAlert, ...prev]);
      } catch (err) {
        // ignore malformed ws payloads
      }
    }
  }, [wsMessage]);

  // Handle alert selection
  const handleSelectAlert = async (alert: ThreatAlert) => {
    setSelectedAlert(alert);
    setShowAlertModal(true);

    // Fetch explanation
    try {
      const res = await fetch(
        `/api/ids/alerts/${alert.alert_id}/explanation`
      );
      const explData = await res.json();
      setExplanation(explData);
    } catch (err) {
      console.error("Failed to fetch explanation:", err);
    }
  };

  // Handle alert status update
  const handleStatusUpdate = async (
    alert_id: string,
    status: string,
    notes: string
  ) => {
    try {
      await fetch(`/api/ids/alerts/${alert_id}/investigate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status, notes }),
      });

      // Update local state
      setAlerts((prev) => prev.map((a) => (a.alert_id === alert_id ? { ...a, status: status as ThreatAlert['status'] } : a)));
    } catch (err) {
      console.error("Failed to update alert:", err);
    }
  };

  return (
    <Container fluid className={styles.container}>
      <div className="mb-4">
        <h2 className="mb-1">Intrusion Detection System (IDS)</h2>
        <p className="text-muted">
          AI-powered threat detection and real-time alert management
        </p>
      </div>

      {/* Metrics Summary */}
      <MetricsSummary metrics={metrics} />

      <Row className="mb-4">
        <Col lg={8}>
          {/* Threat Timeline */}
          <AlertTimeline
            alerts={alerts}
            _onSelectAlert={handleSelectAlert}
            _selectedAlertId={selectedAlert?.alert_id}
          />

          {/* Alert List */}
          <div className="mt-4">
            <AlertList
              alerts={alerts}
              loading={loading}
              onSelectAlert={handleSelectAlert}
              selectedAlertId={selectedAlert?.alert_id}
            />
          </div>
        </Col>

        <Col lg={4}>
          {/* Model Status */}
          <ModelStatusComponent models={models} />

          {/* Threat Distribution */}
          {metrics && (
            <Card className={`${styles.threatDistribution} mt-4`}>
              <Card.Header className="d-flex align-items-center gap-2">
                <Zap size={20} className="text-info" />
                <Card.Title className="mb-0">Threat Distribution</Card.Title>
              </Card.Header>
              <Card.Body>
                <ResponsiveContainer width="100%" height={200}>
                  <PieChart>
                    <Pie
                      data={Object.entries(metrics.threat_distribution).map(
                        ([level, count]) => ({
                          name: level,
                          value: count,
                        })
                      )}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }: { name: string; percent: number }) => ({ name, percent })}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {Object.keys(metrics.threat_distribution).map((level) => (
                        <Cell
                          key={level}
                          fill={THREAT_LEVEL_COLORS[level] || "#6c757d"}
                        />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </Card.Body>
            </Card>
          )}
        </Col>
      </Row>

      {/* Alert Details Modal */}
      <AlertDetailsModal
        show={showAlertModal}
        alert={selectedAlert}
        explanation={explanation}
        loading={loading}
        onHide={() => {
          setShowAlertModal(false);
          setSelectedAlert(null);
          setExplanation(null);
        }}
        onStatusUpdate={handleStatusUpdate}
      />
    </Container>
  );
};

export default IDSThreats;
