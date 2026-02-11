import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import '../utils/modern_effects.dart';

/// Enhanced Self-Healing Monitor for Mobile
///
/// Features:
/// - Real-time metrics with auto-refresh
/// - Multi-tab interface (Overview, Agents, Timeline, Analytics)
/// - Interactive agent selection
/// - Recovery action execution
/// - Live status indicators
/// - Performance visualizations

// Data Models
class AgentMetrics {
  final String name;
  final double accuracy;
  final double confidence;
  final int actionsTaken;
  final double successRate;
  final double learningProgress;
  final AgentStatus status;
  final double performanceScore;
  final int errorCount;

  AgentMetrics({
    required this.name,
    required this.accuracy,
    required this.confidence,
    required this.actionsTaken,
    required this.successRate,
    required this.learningProgress,
    required this.status,
    required this.performanceScore,
    required this.errorCount,
  });
}

class RecoveryAction {
  final String id;
  final String type;
  final String target;
  final double confidence;
  final ActionResult result;
  final DateTime timestamp;
  final String impact;

  RecoveryAction({
    required this.id,
    required this.type,
    required this.target,
    required this.confidence,
    required this.result,
    required this.timestamp,
    required this.impact,
  });
}

enum AgentStatus { active, idle, error }

enum ActionResult { success, failed, pending }

// Riverpod Providers for State Management
final selectedAgentProvider = StateProvider<String>((ref) => 'recovery_coordinator');

final autoRefreshProvider = StateProvider<bool>((ref) => true);

final activeTabProvider = StateProvider<Tab>((ref) => Tab.overview);

final expandedActionProvider = StateProvider<String?>((ref) => null);

// Mock data providers
final agentMetricsProvider = FutureProvider<Map<String, AgentMetrics>>((ref) async {
  // Simulate API call with delay
  await Future.delayed(const Duration(milliseconds: 500));

  return {
    'recovery_coordinator': AgentMetrics(
      name: 'Recovery Coordinator',
      accuracy: 0.94,
      confidence: 0.88,
      actionsTaken: 42,
      successRate: 0.96,
      learningProgress: 0.87,
      status: AgentStatus.active,
      performanceScore: 0.91,
      errorCount: 2,
    ),
    'threat_analyzer': AgentMetrics(
      name: 'Threat Analyzer',
      accuracy: 0.91,
      confidence: 0.85,
      actionsTaken: 38,
      successRate: 0.94,
      learningProgress: 0.82,
      status: AgentStatus.active,
      performanceScore: 0.88,
      errorCount: 1,
    ),
    'policy_engine': AgentMetrics(
      name: 'Policy Engine',
      accuracy: 0.89,
      confidence: 0.82,
      actionsTaken: 35,
      successRate: 0.92,
      learningProgress: 0.79,
      status: AgentStatus.idle,
      performanceScore: 0.86,
      errorCount: 0,
    ),
  };
});

final systemMetricsProvider = FutureProvider<SystemMetrics>((ref) async {
  await Future.delayed(const Duration(milliseconds: 300));

  return SystemMetrics(
    systemHealth: 94,
    overallConfidence: 0.88,
    successRate: 0.95,
    recoveryRate: 0.92,
    avgResponseTime: 1.8,
    totalActionsToday: 115,
  );
});

final recentActionsProvider = FutureProvider<List<RecoveryAction>>((ref) async {
  await Future.delayed(const Duration(milliseconds: 600));

  return [
    RecoveryAction(
      id: 'action_001',
      type: 'isolation',
      target: 'workstation-42',
      confidence: 0.92,
      result: ActionResult.success,
      timestamp: DateTime.now().subtract(const Duration(minutes: 5)),
      impact: 'Isolated compromised endpoint from network to prevent lateral movement',
    ),
    RecoveryAction(
      id: 'action_002',
      type: 'remediation',
      target: 'file-server-03',
      confidence: 0.88,
      result: ActionResult.success,
      timestamp: DateTime.now().subtract(const Duration(minutes: 15)),
      impact: 'Applied security patches and removed malware signatures',
    ),
    RecoveryAction(
      id: 'action_003',
      type: 'policy_update',
      target: 'firewall-001',
      confidence: 0.85,
      result: ActionResult.success,
      timestamp: DateTime.now().subtract(const Duration(minutes: 30)),
      impact: 'Updated ingress rules to block known threat actors',
    ),
  ];
});

class SystemMetrics {
  final int systemHealth;
  final double overallConfidence;
  final double successRate;
  final double recoveryRate;
  final double avgResponseTime;
  final int totalActionsToday;

  SystemMetrics({
    required this.systemHealth,
    required this.overallConfidence,
    required this.successRate,
    required this.recoveryRate,
    required this.avgResponseTime,
    required this.totalActionsToday,
  });
}

enum Tab { overview, agents, timeline, analytics }

class SelfHealingMonitorScreen extends ConsumerStatefulWidget {
  const SelfHealingMonitorScreen({super.key});

  @override
  ConsumerState<SelfHealingMonitorScreen> createState() =>
      _SelfHealingMonitorScreenState();
}

class _SelfHealingMonitorScreenState
    extends ConsumerState<SelfHealingMonitorScreen> {
  late ScrollController _scrollController;

  @override
  void initState() {
    super.initState();
    _scrollController = ScrollController();
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final selectedAgent = ref.watch(selectedAgentProvider);
    final activeTab = ref.watch(activeTabProvider);
    final autoRefresh = ref.watch(autoRefreshProvider);
    final agentsAsync = ref.watch(agentMetricsProvider);
    final metricsAsync = ref.watch(systemMetricsProvider);
    final actionsAsync = ref.watch(recentActionsProvider);

    return Scaffold(
      backgroundColor: const Color(0xFF0A0E27),
      appBar: AppBar(
        backgroundColor: const Color(0xFF0A0E27),
        elevation: 0,
        title: Row(
          children: [
            Icon(Icons.flash_on, color: Colors.cyan[300]),
            const SizedBox(width: 12),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Self-Healing Monitor',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        color: Colors.white,
                        fontWeight: FontWeight.bold,
                      ),
                ),
                Text(
                  'RL Agent Performance',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: Colors.grey[400],
                      ),
                ),
              ],
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () {
              ref.invalidate(systemMetricsProvider);
              ref.invalidate(agentMetricsProvider);
              ref.invalidate(recentActionsProvider);
            },
            tooltip: 'Refresh',
          ),
          PopupMenuButton(
            itemBuilder: (context) => [
              PopupMenuItem(
                child: StatefulBuilder(
                  builder: (context, setState) => CheckboxListTile(
                    title: const Text('Auto Refresh'),
                    value: autoRefresh,
                    onChanged: (value) {
                      ref.read(autoRefreshProvider.notifier).state =
                          value ?? false;
                      Navigator.pop(context);
                    },
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
      body: SafeArea(
        child: CustomScrollView(
          controller: _scrollController,
          slivers: [
            // Tab Navigation
            SliverToBoxAdapter(
              child: Container(
                color: const Color(0xFF0A0E27),
                child: SingleChildScrollView(
                  scrollDirection: Axis.horizontal,
                  child: Row(
                    children: Tab.values.map((tab) {
                      final isSelected = activeTab == tab;
                      return Padding(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 4.0, vertical: 12.0),
                        child: GestureDetector(
                          onTap: () =>
                              ref.read(activeTabProvider.notifier).state = tab,
                          child: Container(
                            padding: const EdgeInsets.symmetric(
                                horizontal: 16, vertical: 8),
                            decoration: BoxDecoration(
                              border: Border(
                                bottom: BorderSide(
                                  color: isSelected
                                      ? Colors.cyan[300]!
                                      : Colors.transparent,
                                  width: 2,
                                ),
                              ),
                            ),
                            child: Text(
                              tab.name.toUpperCase(),
                              style: TextStyle(
                                color: isSelected
                                    ? Colors.cyan[300]
                                    : Colors.grey[400],
                                fontWeight: isSelected
                                    ? FontWeight.bold
                                    : FontWeight.normal,
                              ),
                            ),
                          ),
                        ),
                      );
                    }).toList(),
                  ),
                ),
              ),
            ),
            // Content based on active tab
            SliverToBoxAdapter(
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: _buildTabContent(
                  context,
                  ref,
                  activeTab,
                  selectedAgent,
                  agentsAsync,
                  metricsAsync,
                  actionsAsync,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTabContent(
    BuildContext context,
    WidgetRef ref,
    Tab activeTab,
    String selectedAgent,
    AsyncValue<Map<String, AgentMetrics>> agentsAsync,
    AsyncValue<SystemMetrics> metricsAsync,
    AsyncValue<List<RecoveryAction>> actionsAsync,
  ) {
    return switch (activeTab) {
      Tab.overview => _buildOverviewTab(
          context,
          ref,
          selectedAgent,
          agentsAsync,
          metricsAsync,
          actionsAsync,
        ),
      Tab.agents => _buildAgentsTab(context, ref, selectedAgent, agentsAsync),
      Tab.timeline => _buildTimelineTab(context, actionsAsync),
      Tab.analytics => _buildAnalyticsTab(context, agentsAsync),
    };
  }

  Widget _buildOverviewTab(
    BuildContext context,
    WidgetRef ref,
    String selectedAgent,
    AsyncValue<Map<String, AgentMetrics>> agentsAsync,
    AsyncValue<SystemMetrics> metricsAsync,
    AsyncValue<List<RecoveryAction>> actionsAsync,
  ) {
    return SingleChildScrollView(
      child: Column(
        spacing: 16,
        children: [
          // Status Cards
          metricsAsync.when(
            data: (metrics) => Column(
              spacing: 12,
              children: [
                _buildStatusCard(
                  title: 'System Health',
                  value: '${metrics.systemHealth}%',
                  progress: metrics.systemHealth / 100,
                  icon: Icons.shield,
                  color: Colors.cyan,
                ),
                _buildStatusCard(
                  title: 'RL Confidence',
                  value: '${(metrics.overallConfidence * 100).toStringAsFixed(0)}%',
                  progress: metrics.overallConfidence,
                  icon: Icons.flash_on,
                  color: Colors.amber,
                ),
                _buildStatusCard(
                  title: 'Success Rate',
                  value: '${(metrics.successRate * 100).toStringAsFixed(0)}%',
                  progress: metrics.successRate,
                  icon: Icons.check_circle,
                  color: Colors.green,
                ),
                _buildStatusCard(
                  title: 'Recovery Rate',
                  value: '${(metrics.recoveryRate * 100).toStringAsFixed(0)}%',
                  progress: metrics.recoveryRate,
                  icon: Icons.trending_up,
                  color: Colors.orange,
                ),
              ],
            ),
            loading: () => const SizedBox(
              height: 300,
              child: Center(child: CircularProgressIndicator()),
            ),
            error: (err, stack) => Text('Error: $err'),
          ),

          const SizedBox(height: 12),

          // Last Action Card
          actionsAsync.when(
            data: (actions) => actions.isNotEmpty
                ? _buildActionCard(context, actions.first)
                : const SizedBox.shrink(),
            loading: () => const SizedBox.shrink(),
            error: (err, stack) => const SizedBox.shrink(),
          ),

          // Agent Selector
          agentsAsync.when(
            data: (agents) => _buildAgentSelector(
              context,
              ref,
              selectedAgent,
              agents,
            ),
            loading: () => const SizedBox.shrink(),
            error: (err, stack) => const SizedBox.shrink(),
          ),

          // Recovery Actions
          _buildRecoveryActionsPanel(context, ref),
        ],
      ),
    );
  }

  Widget _buildAgentsTab(
    BuildContext context,
    WidgetRef ref,
    String selectedAgent,
    AsyncValue<Map<String, AgentMetrics>> agentsAsync,
  ) {
    return agentsAsync.when(
      data: (agents) {
        final agent = agents[selectedAgent];
        if (agent == null) return const Text('Agent not found');

        return SingleChildScrollView(
          child: Column(
            spacing: 16,
            children: [
              Text(
                agent.name.toUpperCase(),
                style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                      color: Colors.white,
                      fontWeight: FontWeight.bold,
                    ),
              ),
              // Agent metrics grid
              GridView.count(
                crossAxisCount: 2,
                mainAxisSpacing: 12,
                crossAxisSpacing: 12,
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                children: [
                  _buildMetricTile(
                    'Accuracy',
                    '${(agent.accuracy * 100).toStringAsFixed(1)}%',
                    '✓',
                  ),
                  _buildMetricTile(
                    'Confidence',
                    '${(agent.confidence * 100).toStringAsFixed(1)}%',
                    '⚡',
                  ),
                  _buildMetricTile(
                    'Actions',
                    agent.actionsTaken.toString(),
                    '→',
                  ),
                  _buildMetricTile(
                    'Success Rate',
                    '${(agent.successRate * 100).toStringAsFixed(1)}%',
                    '✓',
                  ),
                ],
              ),
              // Learning progress
              Container(
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(
                    color: Colors.cyan.withOpacity(0.3),
                  ),
                  boxShadow: ModernEffects.glassCardShadows(),
                ),
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    spacing: 12,
                    children: [
                      Text(
                        'Learning Progress',
                        style: Theme.of(context).textTheme.titleMedium?.copyWith(
                              color: Colors.white,
                            ),
                      ),
                      ClipRRect(
                        borderRadius: BorderRadius.circular(8),
                        child: LinearProgressIndicator(
                          value: agent.learningProgress,
                          minHeight: 8,
                          backgroundColor: Colors.cyan.withOpacity(0.2),
                          valueColor: AlwaysStoppedAnimation(
                            Colors.cyan[300],
                          ),
                        ),
                      ),
                      Text(
                        '${(agent.learningProgress * 100).toStringAsFixed(1)}% trained',
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                              color: Colors.grey[400],
                            ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        );
      },
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (err, stack) => Center(child: Text('Error: $err')),
    );
  }

  Widget _buildTimelineTab(
    BuildContext context,
    AsyncValue<List<RecoveryAction>> actionsAsync,
  ) {
    return actionsAsync.when(
      data: (actions) {
        if (actions.isEmpty) {
          return Center(
            child: Text(
              'No actions recorded',
              style: Theme.of(context)
                  .textTheme
                  .bodyMedium
                  ?.copyWith(color: Colors.grey[400]),
            ),
          );
        }

        return SingleChildScrollView(
          child: Column(
            spacing: 12,
            children: actions
                .asMap()
                .entries
                .map((entry) {
                  final idx = entry.key;
                  final action = entry.value;
                  final isLatest = idx == 0;

                  return _buildTimelineActionItem(
                    context,
                    action,
                    isLatest,
                    ref,
                  );
                })
                .toList(),
          ),
        );
      },
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (err, stack) => Center(child: Text('Error: $err')),
    );
  }

  Widget _buildAnalyticsTab(
    BuildContext context,
    AsyncValue<Map<String, AgentMetrics>> agentsAsync,
  ) {
    return agentsAsync.when(
      data: (agents) {
        return SingleChildScrollView(
          child: Column(
            spacing: 16,
            children: [
              // Agent Performance
              Container(
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: Colors.cyan.withOpacity(0.3)),
                  boxShadow: ModernEffects.glassCardShadows(),
                ),
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    spacing: 12,
                    children: [
                      Text(
                        'Agent Performance',
                        style: Theme.of(context).textTheme.titleMedium?.copyWith(
                              color: Colors.white,
                              fontWeight: FontWeight.bold,
                            ),
                      ),
                      ...agents.entries.map((entry) {
                        final agent = entry.value;
                        return Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          spacing: 4,
                          children: [
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Text(
                                  agent.name,
                                  style: TextStyle(
                                    color: Colors.grey[300],
                                    fontSize: 12,
                                  ),
                                ),
                                Text(
                                  '${(agent.performanceScore * 100).toStringAsFixed(0)}%',
                                  style: const TextStyle(
                                    color: Colors.white,
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                              ],
                            ),
                            ClipRRect(
                              borderRadius: BorderRadius.circular(4),
                              child: LinearProgressIndicator(
                                value: agent.performanceScore,
                                minHeight: 4,
                                backgroundColor:
                                    Colors.cyan.withOpacity(0.2),
                                valueColor:
                                    AlwaysStoppedAnimation(Colors.cyan[300]),
                              ),
                            ),
                          ],
                        );
                      }).toList(),
                    ],
                  ),
                ),
              ),
            ],
          ),
        );
      },
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (err, stack) => Center(child: Text('Error: $err')),
    );
  }

  Widget _buildStatusCard({
    required String title,
    required String value,
    required double progress,
    required IconData icon,
    required MaterialColor color,
  }) {
    return Container(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withOpacity(0.3)),
        boxShadow: ModernEffects.glassCardShadows(),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          spacing: 12,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  title,
                  style: const TextStyle(
                    color: Colors.grey,
                    fontSize: 12,
                    fontWeight: FontWeight.w500,
                  ),
                ),
                Icon(icon, color: color[300], size: 20),
              ],
            ),
            Text(
              value,
              style: const TextStyle(
                color: Colors.white,
                fontSize: 28,
                fontWeight: FontWeight.bold,
              ),
            ),
            ClipRRect(
              borderRadius: BorderRadius.circular(4),
              child: LinearProgressIndicator(
                value: progress,
                minHeight: 6,
                backgroundColor: color.withOpacity(0.2),
                valueColor: AlwaysStoppedAnimation(color[300]),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildActionCard(BuildContext context, RecoveryAction action) {
    return Container(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.cyan.withOpacity(0.3)),
        boxShadow: ModernEffects.glassCardShadows(),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          spacing: 12,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'Latest Recovery Action',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        color: Colors.white,
                        fontWeight: FontWeight.bold,
                      ),
                ),
                Icon(Icons.access_time, color: Colors.cyan[300], size: 20),
              ],
            ),
            Container(
              color: Colors.cyan.withOpacity(0.1),
              padding: const EdgeInsets.all(12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                spacing: 8,
                children: [
                  Text(
                    action.type.replaceAll('_', ' ').toUpperCase(),
                    style: const TextStyle(
                      color: Colors.cyan,
                      fontFamily: 'monospace',
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  Text(
                    'Target: ${action.target}',
                    style: TextStyle(
                      color: Colors.grey[300],
                      fontSize: 12,
                    ),
                  ),
                ],
              ),
            ),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Chip(
                  label: Text(
                    '${(action.confidence * 100).toStringAsFixed(0)}% confidence',
                    style: const TextStyle(fontSize: 12),
                  ),
                  backgroundColor: Colors.cyan.withOpacity(0.2),
                ),
                Chip(
                  label: Text(
                    action.result.name.toUpperCase(),
                    style: const TextStyle(fontSize: 12),
                  ),
                  backgroundColor: action.result == ActionResult.success
                      ? Colors.green.withOpacity(0.2)
                      : Colors.red.withOpacity(0.2),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildAgentSelector(
    BuildContext context,
    WidgetRef ref,
    String selectedAgent,
    Map<String, AgentMetrics> agents,
  ) {
    return Container(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.cyan.withOpacity(0.3)),
        boxShadow: ModernEffects.glassCardShadows(),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          spacing: 12,
          children: [
            Text(
              'Active Agents',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                  ),
            ),
            ...agents.entries.map((entry) {
              final isSelected = selectedAgent == entry.key;
              return GestureDetector(
                onTap: () =>
                    ref.read(selectedAgentProvider.notifier).state = entry.key,
                child: Container(
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(
                      color: isSelected
                          ? Colors.cyan[300]!
                          : Colors.cyan.withOpacity(0.2),
                    ),
                    color: isSelected
                        ? Colors.cyan.withOpacity(0.1)
                        : Colors.transparent,
                  ),
                  padding: const EdgeInsets.all(12),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        spacing: 4,
                        children: [
                          Text(
                            entry.value.name,
                            style: TextStyle(
                              color: isSelected
                                  ? Colors.cyan[300]
                                  : Colors.white,
                              fontWeight: isSelected
                                  ? FontWeight.bold
                                  : FontWeight.normal,
                            ),
                          ),
                          Text(
                            'Confidence: ${(entry.value.confidence * 100).toStringAsFixed(0)}%',
                            style: TextStyle(
                              color: Colors.grey[400],
                              fontSize: 12,
                            ),
                          ),
                        ],
                      ),
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.end,
                        spacing: 4,
                        children: [
                          Text(
                            '${(entry.value.accuracy * 100).toStringAsFixed(0)}%',
                            style: const TextStyle(
                              color: Colors.white,
                              fontWeight: FontWeight.bold,
                              fontSize: 16,
                            ),
                          ),
                          Text(
                            'accuracy',
                            style: TextStyle(
                              color: Colors.grey[400],
                              fontSize: 10,
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              );
            }).toList(),
          ],
        ),
      ),
    );
  }

  Widget _buildRecoveryActionsPanel(BuildContext context, WidgetRef ref) {
    return Container(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.cyan.withOpacity(0.3)),
        boxShadow: ModernEffects.glassCardShadows(),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          spacing: 12,
          children: [
            Text(
              'Execute Recovery Actions',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                  ),
            ),
            GridView.count(
              crossAxisCount: 2,
              mainAxisSpacing: 8,
              crossAxisSpacing: 8,
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              children: [
                _buildActionButton(
                  '🔒',
                  'Isolate Threat',
                  'Network isolation',
                  () => _showActionConfirmation(context, 'isolation'),
                ),
                _buildActionButton(
                  '🔧',
                  'Remediate',
                  'Apply patches',
                  () => _showActionConfirmation(context, 'remediation'),
                ),
                _buildActionButton(
                  '📋',
                  'Update Policy',
                  'Security rules',
                  () => _showActionConfirmation(context, 'policy_update'),
                ),
                _buildActionButton(
                  '↩️',
                  'Rollback',
                  'Restore state',
                  () => _showActionConfirmation(context, 'rollback'),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildActionButton(
    String emoji,
    String title,
    String subtitle,
    VoidCallback onPressed,
  ) {
    return GestureDetector(
      onTap: onPressed,
      child: Container(
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: Colors.cyan.withOpacity(0.3)),
          color: Colors.cyan.withOpacity(0.05),
        ),
        child: Padding(
          padding: const EdgeInsets.all(12.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            spacing: 8,
            children: [
              Text(emoji, style: const TextStyle(fontSize: 24)),
              Text(
                title,
                textAlign: TextAlign.center,
                style: const TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.bold,
                  fontSize: 12,
                ),
              ),
              Text(
                subtitle,
                textAlign: TextAlign.center,
                style: TextStyle(
                  color: Colors.grey[400],
                  fontSize: 10,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildTimelineActionItem(
    BuildContext context,
    RecoveryAction action,
    bool isLatest,
    WidgetRef ref,
  ) {
    final expandedAction = ref.watch(expandedActionProvider);
    final isExpanded = expandedAction == action.id;

    return GestureDetector(
      onTap: () => ref.read(expandedActionProvider.notifier).state =
          isExpanded ? null : action.id,
      child: Column(
        children: [
          Container(
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(8),
              border: Border.all(
                color: isExpanded
                    ? Colors.cyan[300]!
                    : Colors.cyan.withOpacity(0.2),
              ),
              color: Colors.cyan.withOpacity(isExpanded ? 0.1 : 0.05),
            ),
            padding: const EdgeInsets.all(12),
            child: Row(
              spacing: 12,
              children: [
                Container(
                  width: 8,
                  height: 8,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: isLatest ? Colors.green : Colors.cyan[300],
                    boxShadow: isLatest
                        ? [
                            BoxShadow(
                              color: Colors.green.withOpacity(0.5),
                              blurRadius: 4,
                              spreadRadius: 1,
                            ),
                          ]
                        : [],
                  ),
                ),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    spacing: 4,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text(
                            action.type.replaceAll('_', ' ').toUpperCase(),
                            style: const TextStyle(
                              color: Colors.white,
                              fontWeight: FontWeight.bold,
                              fontSize: 12,
                            ),
                          ),
                          Text(
                            DateFormat('HH:mm:ss').format(action.timestamp),
                            style: TextStyle(
                              color: Colors.grey[400],
                              fontSize: 10,
                            ),
                          ),
                        ],
                      ),
                      Text(
                        'Target: ${action.target}',
                        style: TextStyle(
                          color: Colors.grey[400],
                          fontSize: 11,
                        ),
                      ),
                      Row(
                        spacing: 8,
                        children: [
                          Chip(
                            label: Text(
                              '${(action.confidence * 100).toStringAsFixed(0)}% confidence',
                              style: const TextStyle(fontSize: 10),
                            ),
                            backgroundColor: Colors.cyan.withOpacity(0.2),
                            materialTapTargetSize:
                                MaterialTapTargetSize.shrinkWrap,
                          ),
                          Chip(
                            label: Text(
                              action.result.name.toUpperCase(),
                              style: const TextStyle(fontSize: 10),
                            ),
                            backgroundColor:
                                action.result == ActionResult.success
                                    ? Colors.green.withOpacity(0.2)
                                    : Colors.red.withOpacity(0.2),
                            materialTapTargetSize:
                                MaterialTapTargetSize.shrinkWrap,
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          if (isExpanded)
            Padding(
              padding: const EdgeInsets.only(top: 8.0),
              child: Container(
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(8),
                  border:
                      Border.all(color: Colors.cyan.withOpacity(0.2)),
                  color: Colors.cyan.withOpacity(0.05),
                ),
                padding: const EdgeInsets.all(12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  spacing: 8,
                  children: [
                    Text(
                      'Impact',
                      style: Theme.of(context).textTheme.labelMedium?.copyWith(
                            color: Colors.cyan[300],
                          ),
                    ),
                    Text(
                      action.impact,
                      style: TextStyle(
                        color: Colors.grey[300],
                        fontSize: 12,
                        height: 1.5,
                      ),
                    ),
                  ],
                ),
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildMetricTile(String label, String value, String icon) {
    return Container(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Colors.cyan.withOpacity(0.3)),
        color: Colors.cyan.withOpacity(0.05),
      ),
      padding: const EdgeInsets.all(12),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        spacing: 8,
        children: [
          Text(
            label,
            style: const TextStyle(
              color: Colors.grey,
              fontSize: 11,
              fontWeight: FontWeight.w500,
            ),
          ),
          Text(
            value,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 16,
              fontWeight: FontWeight.bold,
            ),
          ),
          Text(
            icon,
            style: const TextStyle(fontSize: 16),
          ),
        ],
      ),
    );
  }

  void _showActionConfirmation(BuildContext context, String actionType) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: const Color(0xFF1a1f3a),
        title: Text(
          'Confirm Action',
          style: Theme.of(context).textTheme.titleMedium?.copyWith(
                color: Colors.white,
              ),
        ),
        content: Text(
          'Execute $actionType recovery action?',
          style: TextStyle(color: Colors.grey[300]),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () {
              Navigator.pop(context);
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(
                  content: Text('$actionType executed successfully'),
                  backgroundColor: Colors.green,
                ),
              );
            },
            child: const Text('Confirm'),
          ),
        ],
      ),
    );
  }
}
