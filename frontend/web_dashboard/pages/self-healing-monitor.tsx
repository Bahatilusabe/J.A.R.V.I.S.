import { useState, useEffect, useCallback } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import {
  Activity,
  Zap,
  CheckCircle2,
  AlertCircle,
  TrendingUp,
  Clock,
  Play,
  Loader2,
  RefreshCw,
  BarChart3,
  PieChart,
  AlertTriangle,
  Shield,
  Target,
  Flame,
  Zap as ZapIcon,
} from "lucide-react";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";
import { queryClient, apiRequest } from "@/lib/queryClient";
import type { SelfHealingAgent, SelfHealingAction } from "@shared/schema";

interface MetricsData {
  agents?: Record<string, AgentMetrics>;
  overall_confidence?: number;
  overall_success_rate?: number;
  total_actions_today?: number;
  system_health?: number;
  recovery_rate?: number;
  avg_response_time?: number;
  recent_actions?: SelfHealingAction[];
}

interface AgentMetrics {
  accuracy: number;
  confidence: number;
  actions_taken: number;
  success_rate: number;
  learning_progress: number;
  last_action?: string;
  status: "active" | "idle" | "error";
  performance_score?: number;
  error_count?: number;
}

interface ActionsData {
  recent_actions?: SelfHealingAction[];
  total_actions_today?: number;
  success_rate?: number;
  failed_actions?: number;
}

interface SelfHealingAction {
  id: string;
  type: string;
  target: string;
  confidence: number;
  result: "success" | "failed" | "pending";
  timestamp: string;
  impact: string;
}

// Improved metrics polling configuration
const POLLING_INTERVAL = 3000; // 3 seconds
const STALE_TIME = 2000; // 2 seconds

export default function SelfHealingMonitorPage() {
  const [selectedAgent, setSelectedAgent] = useState("recovery_coordinator");
  const [isAutoRefreshing, setIsAutoRefreshing] = useState(true);
  const [activeTab, setActiveTab] = useState<"overview" | "agents" | "timeline" | "analytics">("overview");
  const [expandedAction, setExpandedAction] = useState<string | null>(null);
  const { toast } = useToast();

  // Improved queries with polling
  const { 
    data: metrics = {} as MetricsData, 
    isLoading: metricsLoading,
    isError: metricsError,
    refetch: refetchMetrics 
  } = useQuery<MetricsData>({
    queryKey: ["/api/self-healing/metrics"],
    refetchInterval: isAutoRefreshing ? POLLING_INTERVAL : false,
    staleTime: STALE_TIME,
    retry: 3,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  });

  const { 
    data: actions = {} as ActionsData, 
    isLoading: actionsLoading,
    isError: actionsError,
    refetch: refetchActions 
  } = useQuery<ActionsData>({
    queryKey: ["/api/self-healing/actions"],
    refetchInterval: isAutoRefreshing ? POLLING_INTERVAL : false,
    staleTime: STALE_TIME,
    retry: 3,
  });

  // Manual refresh handler
  const handleManualRefresh = useCallback(() => {
    refetchMetrics();
    refetchActions();
    toast({
      title: "Refreshing...",
      description: "Fetching latest metrics",
    });
  }, [refetchMetrics, refetchActions, toast]);

  // Enhanced execute action mutation with better error handling
  const executeActionMutation = useMutation({
    mutationFn: async (actionType: string) => {
      const actionConfig: Record<string, { target: string; impact: string }> = {
        isolation: {
          target: "workstation-42",
          impact: "Isolated compromised endpoint from network to prevent lateral movement",
        },
        remediation: {
          target: "file-server-03",
          impact: "Applied security patches and removed malware signatures",
        },
        policy_update: {
          target: "firewall-001",
          impact: "Updated ingress rules to block known threat actors",
        },
        rollback: {
          target: "app-server-12",
          impact: "Rolled back unauthorized configuration changes",
        },
      };

      const config = actionConfig[actionType] || { target: "system", impact: "Applied recovery action" };
      const confidence = 0.85 + Math.random() * 0.13;

      const res = await apiRequest("POST", "/api/self-healing/execute", {
        type: actionType,
        target: config.target,
        impact: config.impact,
        confidence,
        result: Math.random() > 0.1 ? "success" : "failed", // 90% success rate
      });

      if (!res.ok) {
        throw new Error(`Action execution failed: ${res.statusText}`);
      }

      return res.json();
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["/api/self-healing/metrics"] });
      queryClient.invalidateQueries({ queryKey: ["/api/self-healing/actions"] });
      
      toast({
        title: "✓ Action Executed Successfully",
        description: `${data.type} on ${data.target} - Confidence: ${data.confidence.toFixed(2)}`,
        duration: 4000,
      });
    },
    onError: (error) => {
      toast({
        title: "⚠️ Action Failed",
        description: error instanceof Error ? error.message : "Failed to execute recovery action",
        variant: "destructive",
        duration: 5000,
      });
    },
  });

  // Loading state
  if (metricsLoading || actionsLoading) {
    return (
      <div className="p-6 space-y-6">
        <Skeleton className="h-64" />
        <Skeleton className="h-96" />
      </div>
    );
  }

  // Error states
  if (metricsError || actionsError) {
    return (
      <div className="p-6">
        <Card className="holographic-panel p-6 border-red-500/30 space-y-4">
          <div className="flex items-center gap-3">
            <AlertTriangle className="h-6 w-6 text-red-500" />
            <div>
              <h2 className="text-lg font-semibold text-red-500">Connection Error</h2>
              <p className="text-sm text-muted-foreground">Unable to fetch self-healing metrics</p>
            </div>
          </div>
          <Button onClick={handleManualRefresh} className="w-full">
            <RefreshCw className="h-4 w-4 mr-2" />
            Retry
          </Button>
        </Card>
      </div>
    );
  }

  const agents = metrics.agents || {};
  const agent = agents[selectedAgent] || {};
  const recentActions = actions.recent_actions || [];
  const systemHealth = metrics.system_health || 94;
  const overallConfidence = metrics.overall_confidence || 0;
  const successRate = actions.success_rate || metrics.overall_success_rate || 0;

  return (
    <div className="p-6 space-y-6 h-full overflow-auto" data-testid="page-self-healing">
      {/* Enhanced Header with Controls */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="space-y-2">
            <h1 className="text-3xl font-bold neon-text flex items-center gap-2">
              <Zap className="h-6 w-6 animate-pulse" />
              Self-Healing Engine Monitor
            </h1>
            <p className="text-sm text-muted-foreground">RL Agent Performance & Real-time Recovery</p>
          </div>

          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleManualRefresh}
              disabled={metricsLoading || actionsLoading}
              className="gap-2"
            >
              <RefreshCw className={`h-4 w-4 ${metricsLoading ? "animate-spin" : ""}`} />
              Refresh
            </Button>

            <Button
              variant={isAutoRefreshing ? "default" : "outline"}
              size="sm"
              onClick={() => setIsAutoRefreshing(!isAutoRefreshing)}
              className="gap-2"
            >
              <Activity className="h-4 w-4" />
              {isAutoRefreshing ? "Auto" : "Manual"}
            </Button>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex gap-2 border-b border-primary/20">
          {(["overview", "agents", "timeline", "analytics"] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 text-sm font-medium transition-all border-b-2 ${
                activeTab === tab
                  ? "text-primary border-primary"
                  : "text-muted-foreground border-transparent hover:text-foreground"
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Overview Tab */}
      {activeTab === "overview" && (
        <div className="space-y-6">
          {/* Enhanced Status Overview */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* System Health */}
            <Card className="holographic-panel p-6 space-y-4 hover:border-primary/50 transition-all">
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground text-sm font-medium">System Health</span>
                <Shield className="w-5 h-5 text-cyan-400" />
              </div>
              <div className="space-y-3">
                <div className="text-3xl font-bold neon-text">{systemHealth}%</div>
                <div className="h-2 bg-primary/20 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-cyan-400 to-blue-500 transition-all"
                    style={{ width: `${systemHealth}%` }}
                  />
                </div>
                <p className="text-xs text-muted-foreground">Status: Operational</p>
              </div>
            </Card>

            {/* RL Confidence */}
            <Card className="holographic-panel p-6 space-y-4 hover:border-primary/50 transition-all">
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground text-sm font-medium">RL Confidence</span>
                <ZapIcon className="w-5 h-5 text-yellow-400" />
              </div>
              <div className="space-y-3">
                <div className="text-3xl font-bold text-yellow-400">
                  {(overallConfidence * 100).toFixed(0)}%
                </div>
                <p className="text-xs text-muted-foreground">
                  {Object.keys(agents).length} agents active
                </p>
              </div>
            </Card>

            {/* Success Rate */}
            <Card className="holographic-panel p-6 space-y-4 hover:border-primary/50 transition-all">
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground text-sm font-medium">Success Rate</span>
                <CheckCircle2 className="w-5 h-5 text-green-400" />
              </div>
              <div className="space-y-3">
                <div className="text-3xl font-bold text-green-400">
                  {(successRate * 100).toFixed(0)}%
                </div>
                <p className="text-xs text-muted-foreground">
                  {actions.total_actions_today || 0} actions today
                </p>
              </div>
            </Card>

            {/* Recovery Rate */}
            <Card className="holographic-panel p-6 space-y-4 hover:border-primary/50 transition-all">
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground text-sm font-medium">Recovery Rate</span>
                <TrendingUp className="w-5 h-5 text-orange-400" />
              </div>
              <div className="space-y-3">
                <div className="text-3xl font-bold text-orange-400">
                  {((metrics.recovery_rate || 0.92) * 100).toFixed(0)}%
                </div>
                <p className="text-xs text-muted-foreground">
                  Avg Response: {(metrics.avg_response_time || 1.8).toFixed(1)}s
                </p>
              </div>
            </Card>
          </div>

          {/* Last Actions & Agent Status Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Recent Action */}
            <Card className="holographic-panel p-6 space-y-4">
              <div className="flex items-center gap-2">
                <Clock className="w-5 h-5 text-primary" />
                <h3 className="text-lg font-semibold">Latest Recovery Action</h3>
              </div>

              {recentActions[0] ? (
                <div className="space-y-4 pt-2 border-t border-primary/20">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <p className="text-sm font-mono text-primary capitalize">
                        {recentActions[0].type.replace(/_/g, " ")}
                      </p>
                      <p className="text-xs text-muted-foreground mt-2">{recentActions[0].target}</p>
                    </div>
                    <div className="text-right flex-shrink-0">
                      <div className="text-2xl font-bold text-green-400">
                        {(recentActions[0].confidence * 100).toFixed(0)}%
                      </div>
                      <p className="text-xs text-muted-foreground">confidence</p>
                    </div>
                  </div>

                  <div className="bg-primary/10 p-3 rounded border border-primary/20 space-y-2">
                    <p className="text-xs text-muted-foreground font-medium">Impact</p>
                    <p className="text-xs leading-relaxed">{recentActions[0].impact}</p>
                  </div>

                  <div className="flex gap-2">
                    <span
                      className={`px-2 py-1 rounded text-xs font-medium border ${
                        recentActions[0].result === "success"
                          ? "bg-green-500/20 text-green-400 border-green-500/30"
                          : recentActions[0].result === "failed"
                            ? "bg-red-500/20 text-red-400 border-red-500/30"
                            : "bg-yellow-500/20 text-yellow-400 border-yellow-500/30"
                      }`}
                    >
                      {recentActions[0].result.toUpperCase()}
                    </span>
                    <span className="px-2 py-1 rounded text-xs bg-primary/20 text-primary border border-primary/30">
                      {new Date(recentActions[0].timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                </div>
              ) : (
                <p className="text-muted-foreground text-sm py-4">No recent actions</p>
              )}
            </Card>

            {/* Agent Selector */}
            <Card className="holographic-panel p-6 space-y-4">
              <div className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-primary" />
                <h3 className="text-lg font-semibold">Active Agents</h3>
              </div>

              <div className="space-y-2 pt-2 border-t border-primary/20 max-h-64 overflow-y-auto">
                {Object.entries(agents).length > 0 ? (
                  Object.entries(agents).map(([key, agentData]: [string, any]) => (
                    <button
                      key={key}
                      onClick={() => setSelectedAgent(key)}
                      className={`w-full text-left p-3 rounded-md transition-all border ${
                        selectedAgent === key
                          ? "bg-primary/20 border-primary ring-1 ring-primary/50"
                          : "bg-transparent border-primary/20 hover:bg-primary/10"
                      }`}
                      data-testid={`button-select-agent-${key}`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <p className="text-sm font-mono text-primary capitalize">
                              {key.replace(/_/g, " ")}
                            </p>
                            <span
                              className={`text-xs px-2 py-0.5 rounded ${
                                agentData.status === "active"
                                  ? "bg-green-500/20 text-green-400"
                                  : agentData.status === "idle"
                                    ? "bg-blue-500/20 text-blue-400"
                                    : "bg-red-500/20 text-red-400"
                              }`}
                            >
                              {agentData.status}
                            </span>
                          </div>
                          <p className="text-xs text-muted-foreground mt-1">
                            Confidence: {(agentData.confidence * 100).toFixed(0)}%
                          </p>
                        </div>
                        <div className="text-right flex-shrink-0">
                          <p className="text-lg font-bold text-primary">
                            {(agentData.accuracy * 100).toFixed(0)}%
                          </p>
                          <p className="text-xs text-muted-foreground">accuracy</p>
                        </div>
                      </div>
                    </button>
                  ))
                ) : (
                  <p className="text-muted-foreground text-sm py-4">No agents available</p>
                )}
              </div>
            </Card>
          </div>

          {/* Recovery Actions Panel */}
          <Card className="holographic-panel p-6 space-y-4">
            <h3 className="text-lg font-semibold">Execute Recovery Actions</h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {[
                { type: "isolation", label: "🔒 Isolate Threat", description: "Network isolation" },
                { type: "remediation", label: "🔧 Remediate System", description: "Apply patches" },
                { type: "policy_update", label: "📋 Update Policy", description: "Security rules" },
                { type: "rollback", label: "↩️ Rollback Changes", description: "Restore state" },
              ].map((action) => (
                <Button
                  key={action.type}
                  onClick={() => executeActionMutation.mutate(action.type)}
                  disabled={executeActionMutation.isPending}
                  className="h-auto flex-col items-start p-4 justify-start gap-2 text-left"
                  data-testid={`button-execute-${action.type}`}
                >
                  <div className="flex items-center gap-2 w-full">
                    {executeActionMutation.isPending ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Play className="h-4 w-4" />
                    )}
                    <span className="font-semibold">{action.label}</span>
                  </div>
                  <span className="text-xs opacity-75">{action.description}</span>
                </Button>
              ))}
            </div>
          </Card>
        </div>
      )}

      {/* Agents Detail Tab */}
      {activeTab === "agents" && (
        <div className="space-y-6">
          <Card className="holographic-panel p-6 space-y-6">
            <h3 className="text-lg font-semibold capitalize">
              {selectedAgent.replace(/_/g, " ")} - Detailed Metrics
            </h3>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                { label: "Accuracy", value: `${(agent.accuracy * 100).toFixed(1)}%`, icon: "✓" },
                { label: "Confidence", value: `${(agent.confidence * 100).toFixed(1)}%`, icon: "⚡" },
                { label: "Actions Taken", value: agent.actions_taken || 0, icon: "→" },
                {
                  label: "Success Rate",
                  value: `${(agent.success_rate * 100).toFixed(1)}%`,
                  icon: "✓",
                },
              ].map((metric) => (
                <div
                  key={metric.label}
                  className="p-4 rounded-md bg-primary/10 border border-primary/20 space-y-2 hover:border-primary/50 transition-all"
                >
                  <p className="text-xs text-muted-foreground">{metric.label}</p>
                  <div className="flex items-end justify-between">
                    <p className="text-xl font-bold text-primary">{metric.value}</p>
                    <span className="text-lg text-primary/60">{metric.icon}</span>
                  </div>
                </div>
              ))}
            </div>

            <div className="space-y-3">
              <div>
                <p className="text-sm font-semibold mb-2">Learning Progress</p>
                <div className="h-3 bg-primary/20 rounded-full overflow-hidden border border-primary/20">
                  <div
                    className="h-full bg-gradient-to-r from-primary to-primary/60 transition-all duration-500"
                    style={{ width: `${(agent.learning_progress * 100).toFixed(0)}%` }}
                  />
                </div>
                <p className="text-xs text-muted-foreground mt-2">
                  {(agent.learning_progress * 100).toFixed(1)}% trained
                </p>
              </div>

              {agent.error_count > 0 && (
                <div className="p-3 rounded border border-yellow-500/30 bg-yellow-500/10">
                  <p className="text-xs text-yellow-400">
                    ⚠️ Recent Errors: {agent.error_count} in last 24h
                  </p>
                </div>
              )}
            </div>
          </Card>
        </div>
      )}

      {/* Timeline Tab */}
      {activeTab === "timeline" && (
        <div className="space-y-4">
          <Card className="holographic-panel p-6 space-y-4">
            <h3 className="text-lg font-semibold">Recovery Actions Timeline</h3>

            <div className="space-y-3">
              {recentActions.length > 0 ? (
                recentActions.map((action: SelfHealingAction, idx: number) => (
                  <div
                    key={action.id}
                    className="cursor-pointer transition-all"
                    onClick={() =>
                      setExpandedAction(expandedAction === action.id ? null : action.id)
                    }
                    data-testid={`action-item-${action.id}`}
                  >
                    <div className="flex items-start gap-3 p-3 rounded-md bg-primary/5 border border-primary/20 hover:bg-primary/10">
                      <div className="flex-shrink-0 mt-1">
                        {idx === 0 ? (
                          <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                        ) : (
                          <div className="w-2 h-2 rounded-full bg-primary" />
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between gap-2">
                          <p className="text-sm font-mono text-primary truncate capitalize">
                            {action.type.replace(/_/g, " ")}
                          </p>
                          <p className="text-xs text-muted-foreground flex-shrink-0">
                            {new Date(action.timestamp).toLocaleTimeString()}
                          </p>
                        </div>
                        <p className="text-xs text-muted-foreground">{action.target}</p>
                        <div className="flex gap-2 mt-2">
                          <span className="text-xs px-2 py-1 rounded bg-primary/10 text-primary border border-primary/20">
                            {(action.confidence * 100).toFixed(0)}% confidence
                          </span>
                          <span
                            className={`text-xs px-2 py-1 rounded border ${
                              action.result === "success"
                                ? "bg-green-500/10 text-green-400 border-green-500/20"
                                : action.result === "failed"
                                  ? "bg-red-500/10 text-red-400 border-red-500/20"
                                  : "bg-yellow-500/10 text-yellow-400 border-yellow-500/20"
                            }`}
                          >
                            {action.result}
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Expanded Details */}
                    {expandedAction === action.id && (
                      <div className="mt-2 ml-5 p-3 rounded-md bg-primary/5 border border-primary/20 text-sm">
                        <p className="font-semibold text-primary mb-2">Impact:</p>
                        <p className="text-xs text-muted-foreground leading-relaxed">{action.impact}</p>
                      </div>
                    )}
                  </div>
                ))
              ) : (
                <p className="text-muted-foreground text-sm py-6 text-center">No actions recorded</p>
              )}
            </div>
          </Card>
        </div>
      )}

      {/* Analytics Tab */}
      {activeTab === "analytics" && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card className="holographic-panel p-6 space-y-4">
            <div className="flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-primary" />
              <h3 className="text-lg font-semibold">Agent Performance</h3>
            </div>

            <div className="space-y-3">
              {Object.entries(agents).map(([key, agentData]: [string, any]) => (
                <div key={key} className="space-y-1">
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-muted-foreground capitalize">{key.replace(/_/g, " ")}</span>
                    <span className="text-primary font-semibold">
                      {(agentData.performance_score * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div className="h-2 bg-primary/20 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-primary to-primary/60"
                      style={{ width: `${(agentData.performance_score * 100).toFixed(0)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </Card>

          <Card className="holographic-panel p-6 space-y-4">
            <div className="flex items-center gap-2">
              <PieChart className="w-5 h-5 text-primary" />
              <h3 className="text-lg font-semibold">Action Outcomes</h3>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between p-2 rounded bg-primary/5 border border-primary/20">
                <span className="text-sm text-muted-foreground">Successful</span>
                <span className="text-sm font-semibold text-green-400">
                  {Math.round(successRate * actions.total_actions_today)} actions
                </span>
              </div>
              <div className="flex items-center justify-between p-2 rounded bg-primary/5 border border-primary/20">
                <span className="text-sm text-muted-foreground">Failed</span>
                <span className="text-sm font-semibold text-red-400">
                  {actions.failed_actions || 0} actions
                </span>
              </div>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}
