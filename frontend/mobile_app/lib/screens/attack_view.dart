import 'package:flutter/material.dart';
import '../theme.dart';
import '../utils/modern_effects.dart';

class AttackView extends StatefulWidget {
  const AttackView({super.key});

  @override
  State<AttackView> createState() => _AttackViewState();
}

class _AttackViewState extends State<AttackView> {
  int _selectedThreatLevel = 0; // 0=all, 1=critical, 2=high, 3=medium, 4=low
  bool _gridView = true;

  final List<Map<String, dynamic>> _mockThreats = [
    {'title': 'SSH Brute Force', 'severity': 'CRITICAL', 'sources': 3, 'status': 'Active', 'color': neonRed},
    {'title': 'SQL Injection', 'severity': 'CRITICAL', 'sources': 1, 'status': 'Contained', 'color': neonRed},
    {'title': 'DDoS Attack', 'severity': 'HIGH', 'sources': 12, 'status': 'Mitigating', 'color': neonOrange},
    {'title': 'Privilege Escalation', 'severity': 'HIGH', 'sources': 2, 'status': 'Investigating', 'color': neonOrange},
    {'title': 'Lateral Movement', 'severity': 'MEDIUM', 'sources': 5, 'status': 'Monitored', 'color': quantumGreen},
    {'title': 'Data Exfiltration', 'severity': 'HIGH', 'sources': 1, 'status': 'Blocked', 'color': neonOrange},
    {'title': 'Malware Detected', 'severity': 'CRITICAL', 'sources': 4, 'status': 'Isolated', 'color': neonRed},
    {'title': 'Policy Violation', 'severity': 'MEDIUM', 'sources': 2, 'status': 'Flagged', 'color': quantumGreen},
  ];

  List<Map<String, dynamic>> get filteredThreats {
    if (_selectedThreatLevel == 0) return _mockThreats;
    final levels = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'];
    return _mockThreats.where((t) => t['severity'] == levels[_selectedThreatLevel - 1]).toList();
  }

  @override
  Widget build(BuildContext context) {
    final isMobile = MediaQuery.of(context).size.width < 600;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Attack Landscape'),
        elevation: 0,
        actions: [
          Padding(
            padding: const EdgeInsets.all(8),
            child: Center(
              child: Chip(
                label: Text('${filteredThreats.length} Threats'),
                backgroundColor: Theme.of(context).colorScheme.surface.withValues(alpha: 0.7),
                labelStyle: const TextStyle(color: Colors.white70, fontSize: 12),
              ),
            ),
          ),
        ],
      ),
      body: Column(
        children: [
          // Filter bar
          Padding(
            padding: const EdgeInsets.all(12.0),
            child: Column(
              children: [
                Row(
                  children: [
                    Expanded(
                      child: SingleChildScrollView(
                        scrollDirection: Axis.horizontal,
                        child: Row(
                          children: [
                            _buildFilterChip('All', 0),
                            const SizedBox(width: 8),
                            _buildFilterChip('🔴 Critical', 1),
                            const SizedBox(width: 8),
                            _buildFilterChip('🟠 High', 2),
                            const SizedBox(width: 8),
                            _buildFilterChip('🟡 Medium', 3),
                            const SizedBox(width: 8),
                            _buildFilterChip('🟢 Low', 4),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      'Threat Grid (${filteredThreats.length})',
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: Colors.white70,
                      ),
                    ),
                    IconButton(
                      icon: Icon(_gridView ? Icons.grid_view : Icons.list),
                      onPressed: () => setState(() => _gridView = !_gridView),
                      tooltip: 'Toggle view',
                    ),
                  ],
                ),
              ],
            ),
          ),
          // Threats grid/list
          Expanded(
            child: _gridView
                ? _buildGridView(isMobile)
                : _buildListView(),
          ),
        ],
      ),
    );
  }

  Widget _buildFilterChip(String label, int level) {
    final isSelected = _selectedThreatLevel == level;
    return GestureDetector(
      onTap: () => setState(() => _selectedThreatLevel = level),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        decoration: BoxDecoration(
          color: isSelected ? neonCyan.withValues(alpha: 0.2) : Colors.transparent,
          border: Border.all(
            color: isSelected ? neonCyan : Colors.white24,
            width: 1.5,
          ),
          borderRadius: BorderRadius.circular(20),
        ),
        child: Text(
          label,
          style: TextStyle(
            fontSize: 12,
            color: isSelected ? neonCyan : Colors.white70,
            fontWeight: isSelected ? FontWeight.w600 : FontWeight.w400,
          ),
        ),
      ),
    );
  }

  Widget _buildGridView(bool isMobile) {
    return GridView.builder(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: isMobile ? 2 : 3,
        mainAxisSpacing: 12,
        crossAxisSpacing: 12,
        childAspectRatio: 1.1,
      ),
      itemCount: filteredThreats.length,
      itemBuilder: (context, index) => _buildThreatCard(filteredThreats[index]),
    );
  }

  Widget _buildListView() {
    return ListView.builder(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      itemCount: filteredThreats.length,
      itemBuilder: (context, index) {
        final threat = filteredThreats[index];
        return Padding(
          padding: const EdgeInsets.only(bottom: 8),
          child: Container(
            decoration: ModernEffects.glassCard(hasGlow: true),
            child: ListTile(
              leading: Container(
                width: 12,
                height: 48,
                decoration: BoxDecoration(
                  color: threat['color'] as Color,
                  borderRadius: BorderRadius.circular(2),
                  boxShadow: ModernEffects.neonGlowShadows(color: threat['color'] as Color),
                ),
              ),
              title: Text(threat['title']),
              subtitle: Text('${threat['sources']} sources • ${threat['status']}'),
              trailing: Chip(
                label: Text(threat['severity'], style: const TextStyle(fontSize: 11)),
                backgroundColor: threat['color'].withValues(alpha: 0.2),
                labelStyle: TextStyle(color: threat['color']),
              ),
              onTap: () => _showThreatDetail(threat),
            ),
          ),
        );
      },
    );
  }

  Widget _buildThreatCard(Map<String, dynamic> threat) {
    return GestureDetector(
      onTap: () => _showThreatDetail(threat),
      child: MouseRegion(
        cursor: SystemMouseCursors.click,
        child: TweenAnimationBuilder<double>(
          tween: Tween<double>(begin: 1.0, end: 1.0),
          duration: const Duration(milliseconds: 300),
          builder: (context, scale, child) {
            return Transform.scale(
              scale: scale,
              child: Container(
                decoration: ModernEffects.glassCard(hasGlow: true),
                child: Padding(
                  padding: const EdgeInsets.all(12.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Severity indicator
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                            decoration: BoxDecoration(
                              color: (threat['color'] as Color).withValues(alpha: 0.15),
                              border: Border.all(color: threat['color'] as Color, width: 0.5),
                              borderRadius: BorderRadius.circular(4),
                              boxShadow: ModernEffects.neonGlowShadows(color: threat['color'] as Color),
                            ),
                            child: Text(
                              threat['severity'],
                              style: TextStyle(
                                fontSize: 10,
                                fontWeight: FontWeight.bold,
                                color: threat['color'],
                              ),
                            ),
                          ),
                          Container(
                            width: 8,
                            height: 8,
                            decoration: BoxDecoration(
                              color: threat['status'] == 'Active' ? neonRed : quantumGreen,
                              shape: BoxShape.circle,
                              boxShadow: ModernEffects.neonGlowShadows(
                                color: threat['status'] == 'Active' ? neonRed : quantumGreen,
                              ),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      // Title
                      Text(
                        threat['title'],
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(
                          fontSize: 13,
                          fontWeight: FontWeight.w600,
                          color: Colors.white,
                        ),
                      ),
                      const Spacer(),
                      // Footer
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text(
                            '${threat['sources']} sources',
                            style: const TextStyle(
                              fontSize: 11,
                              color: Colors.white54,
                            ),
                          ),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                            decoration: BoxDecoration(
                              color: Colors.white.withValues(alpha: 0.05),
                              border: Border.all(color: Colors.white24, width: 0.5),
                              borderRadius: BorderRadius.circular(3),
                            ),
                            child: Text(
                              threat['status'],
                              style: const TextStyle(
                                fontSize: 10,
                                color: Colors.white70,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
            );
          },
        ),
      ),
    );
  }

  void _showThreatDetail(Map<String, dynamic> threat) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: deepSpaceNavy,
        title: Text(threat['title']),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Severity: ${threat['severity']}'),
            const SizedBox(height: 8),
            Text('Status: ${threat['status']}'),
            const SizedBox(height: 8),
            Text('Attack Sources: ${threat['sources']}'),
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: threat['color'].withValues(alpha: 0.1),
                border: Border.all(color: threat['color'].withValues(alpha: 0.3)),
                borderRadius: BorderRadius.circular(4),
              ),
              child: const Text(
                'Real-time threat monitoring active. Containment strategies deployed.',
                style: TextStyle(fontSize: 12, color: Colors.white70),
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Close'),
          ),
          ElevatedButton(
            onPressed: () {
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(content: Text('Threat action: ${threat['title']}')),
              );
              Navigator.pop(context);
            },
            child: const Text('Take Action'),
          ),
        ],
      ),
    );
  }
}
