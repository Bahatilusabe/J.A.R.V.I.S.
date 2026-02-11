import 'package:flutter/material.dart';
import '../services/pasm_service.dart';
import '../theme.dart';
import '../utils/modern_effects.dart';
import '../widgets/uncertainty_display.dart';

/// Interactive bottom sheet for viewing detailed attack path information
class AttackPathDetailsModal extends StatefulWidget {
  final AttackPath path;
  final Map<String, String> nodeLabels;
  final VoidCallback? onExplore;

  const AttackPathDetailsModal({
    required this.path,
    required this.nodeLabels,
    this.onExplore,
    super.key,
  });

  @override
  State<AttackPathDetailsModal> createState() => _AttackPathDetailsModalState();
}

class _AttackPathDetailsModalState extends State<AttackPathDetailsModal> with TickerProviderStateMixin {
  late TabController _tabController;
  late AnimationController _expandController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
    _expandController = AnimationController(duration: const Duration(milliseconds: 400), vsync: this);
    _expandController.forward();
  }

  @override
  void dispose() {
    _tabController.dispose();
    _expandController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final pathLabels = widget.path.nodes.map((id) => widget.nodeLabels[id] ?? id).toList();

    return AnimatedBuilder(
      animation: _expandController,
      builder: (ctx, _) {
        return Transform.scale(
          scale: 0.9 + (0.1 * _expandController.value),
          child: Opacity(
            opacity: _expandController.value,
            child: Dialog(
              elevation: 0,
              backgroundColor: Colors.transparent,
              child: Container(
                constraints: BoxConstraints(maxHeight: MediaQuery.of(context).size.height * 0.85),
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: [
                      const Color(0x1A0f1724),
                      const Color(0x2A0f1724),
                    ],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  border: Border.all(color: neonCyan.withValues(alpha: 0.3), width: 1),
                  borderRadius: BorderRadius.circular(16),
                  boxShadow: [
                    BoxShadow(
                      color: neonCyan.withValues(alpha: 0.2),
                      blurRadius: 32,
                      spreadRadius: 4,
                    ),
                  ],
                ),
                child: SingleChildScrollView(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Header
                      Padding(
                        padding: const EdgeInsets.all(16),
                        child: Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  const Text(
                                    'Attack Path Details',
                                    style: TextStyle(
                                      fontSize: 18,
                                      fontWeight: FontWeight.w700,
                                      color: Colors.white,
                                    ),
                                  ),
                                  const SizedBox(height: 4),
                                  Container(
                                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                                    decoration: BoxDecoration(
                                      color: neonCyan.withValues(alpha: 0.15),
                                      border: Border.all(color: neonCyan, width: 0.5),
                                      borderRadius: BorderRadius.circular(4),
                                    ),
                                    child: Text(
                                      'Risk: ${(widget.path.score * 100).toStringAsFixed(1)}%',
                                      style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: neonCyan),
                                    ),
                                  ),
                                ],
                              ),
                            ),
                            GestureDetector(
                              onTap: () => Navigator.pop(context),
                              child: Container(
                                width: 32,
                                height: 32,
                                decoration: BoxDecoration(
                                  color: Colors.white.withValues(alpha: 0.1),
                                  shape: BoxShape.circle,
                                ),
                                child: const Icon(Icons.close, size: 18, color: Colors.white70),
                              ),
                            ),
                          ],
                        ),
                      ),
                      const Divider(color: Colors.white10, height: 1),

                      // Tab bar
                      Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 8),
                        child: TabBar(
                          controller: _tabController,
                          labelColor: neonCyan,
                          unselectedLabelColor: Colors.white54,
                          indicatorColor: neonCyan,
                          tabs: const [
                            Tab(text: 'Path'),
                            Tab(text: 'Exploits'),
                            Tab(text: 'Remediation'),
                          ],
                        ),
                      ),

                      // Tab content
                      SizedBox(
                        height: 400,
                        child: TabBarView(
                          controller: _tabController,
                          children: [
                            _buildPathTab(pathLabels),
                            _buildExploitsTab(),
                            _buildRemediationTab(pathLabels),
                          ],
                        ),
                      ),

                      // Action buttons
                      Padding(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          children: [
                            ElevatedButton.icon(
                              onPressed: widget.onExplore ?? () {},
                              icon: const Icon(Icons.analytics),
                              label: const Text('Explore in CED'),
                              style: ElevatedButton.styleFrom(
                                backgroundColor: neonCyan.withValues(alpha: 0.2),
                                foregroundColor: neonCyan,
                                padding: const EdgeInsets.symmetric(vertical: 12),
                                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                              ),
                            ),
                            const SizedBox(height: 8),
                            OutlinedButton.icon(
                              onPressed: () => Navigator.pop(context),
                              icon: const Icon(Icons.close),
                              label: const Text('Close'),
                              style: OutlinedButton.styleFrom(
                                side: BorderSide(color: Colors.white24, width: 1),
                                foregroundColor: Colors.white70,
                                padding: const EdgeInsets.symmetric(vertical: 12),
                                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        );
      },
    );
  }

  Widget _buildPathTab(List<String> pathLabels) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Attack Sequence',
            style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: Colors.white70),
          ),
          const SizedBox(height: 12),
          // Path visualization
          for (int i = 0; i < pathLabels.length; i++) ...[
            _buildPathNode(pathLabels[i], i, pathLabels.length),
            if (i < pathLabels.length - 1) ...[
              const SizedBox(height: 8),
              Center(
                child: Icon(Icons.arrow_downward, size: 20, color: neonCyan.withValues(alpha: 0.5)),
              ),
              const SizedBox(height: 8),
            ],
          ],
          const SizedBox(height: 16),
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Colors.white.withValues(alpha: 0.04),
              border: Border.all(color: Colors.white10, width: 0.5),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Risk Score Breakdown', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: Colors.white70)),
                const SizedBox(height: 8),
                RiskBandChart(
                  means: [widget.path.score, 0.6, 0.45],
                  stds: [0.08, 0.1, 0.06],
                  labels: ['Overall Risk', 'Impact', 'Likelihood'],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildPathNode(String label, int index, int total) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [neonCyan.withValues(alpha: 0.15), holographicBlue.withValues(alpha: 0.08)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        border: Border.all(color: neonCyan, width: 1),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        children: [
          Container(
            width: 32,
            height: 32,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              gradient: LinearGradient(
                colors: [neonCyan, holographicBlue],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
            ),
            child: Center(
              child: Text(
                '${index + 1}',
                style: const TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.w700,
                  fontSize: 13,
                ),
              ),
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  label,
                  style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: Colors.white),
                ),
                Text(
                  'Step ${index + 1} of $total',
                  style: const TextStyle(fontSize: 10, color: Colors.white54),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildExploitsTab() {
    final exploits = [
      {
        'name': 'CVE-2024-0001',
        'title': 'Network Access Vulnerability',
        'severity': 'CRITICAL',
        'cvss': 9.8,
      },
      {
        'name': 'CVE-2024-0002',
        'title': 'Privilege Escalation',
        'severity': 'HIGH',
        'cvss': 8.2,
      },
      {
        'name': 'CVE-2024-0003',
        'title': 'Data Access',
        'severity': 'MEDIUM',
        'cvss': 6.5,
      },
    ];

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Associated Exploits',
            style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: Colors.white70),
          ),
          const SizedBox(height: 12),
          ...exploits.map((e) => Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.white.withValues(alpha: 0.04),
                border: Border.all(color: Colors.white10, width: 0.5),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              e['name'] as String,
                              style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: Colors.white),
                            ),
                            const SizedBox(height: 2),
                            Text(
                              e['title'] as String,
                              style: const TextStyle(fontSize: 10, color: Colors.white54),
                            ),
                          ],
                        ),
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                        decoration: BoxDecoration(
                          color: (e['severity'] == 'CRITICAL' ? Colors.red : (e['severity'] == 'HIGH' ? Colors.orange : Colors.yellow)).withValues(alpha: 0.2),
                          borderRadius: BorderRadius.circular(4),
                        ),
                        child: Text(
                          e['severity'] as String,
                          style: TextStyle(
                            fontSize: 9,
                            fontWeight: FontWeight.bold,
                            color: e['severity'] == 'CRITICAL' ? Colors.red : (e['severity'] == 'HIGH' ? Colors.orange : Colors.yellow),
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      const Text('CVSS: ', style: TextStyle(fontSize: 9, color: Colors.white54)),
                      Text(
                        '${e['cvss']}',
                        style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: Colors.white),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          )).toList(),
        ],
      ),
    );
  }

  Widget _buildRemediationTab(List<String> pathLabels) {
    final remediations = [
      {
        'step': 1,
        'title': 'Update network access controls',
        'description': 'Restrict network access to ${pathLabels.first}',
        'priority': 'CRITICAL',
      },
      {
        'step': 2,
        'title': 'Apply security patches',
        'description': 'Update software components to latest versions',
        'priority': 'HIGH',
      },
      {
        'step': 3,
        'title': 'Implement monitoring',
        'description': 'Add detection rules for this attack pattern',
        'priority': 'MEDIUM',
      },
    ];

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Recommended Actions',
            style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: Colors.white70),
          ),
          const SizedBox(height: 12),
          ...remediations.map((r) => Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.white.withValues(alpha: 0.04),
                border: Border.all(color: Colors.white10, width: 0.5),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Step ${r['step']}: ${r['title']}',
                              style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: Colors.white),
                            ),
                            const SizedBox(height: 2),
                            Text(
                              r['description'] as String,
                              style: const TextStyle(fontSize: 10, color: Colors.white54),
                            ),
                          ],
                        ),
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                        decoration: BoxDecoration(
                          color: (r['priority'] == 'CRITICAL' ? Colors.red : (r['priority'] == 'HIGH' ? Colors.orange : Colors.yellow)).withValues(alpha: 0.2),
                          borderRadius: BorderRadius.circular(4),
                        ),
                        child: Text(
                          r['priority'] as String,
                          style: TextStyle(
                            fontSize: 9,
                            fontWeight: FontWeight.bold,
                            color: r['priority'] == 'CRITICAL' ? Colors.red : (r['priority'] == 'HIGH' ? Colors.orange : Colors.yellow),
                          ),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          )).toList(),
        ],
      ),
    );
  }
}

/// Helper function to show path details modal
void showPathDetailsModal(
  BuildContext context, {
  required AttackPath path,
  required Map<String, String> nodeLabels,
  VoidCallback? onExplore,
}) {
  showDialog(
    context: context,
    builder: (ctx) => AttackPathDetailsModal(
      path: path,
      nodeLabels: nodeLabels,
      onExplore: onExplore,
    ),
  );
}
