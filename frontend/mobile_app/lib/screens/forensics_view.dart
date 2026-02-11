import 'package:flutter/material.dart';
import '../theme.dart';
import '../utils/modern_effects.dart';

class ForensicsView extends StatefulWidget {
  const ForensicsView({super.key});

  @override
  State<ForensicsView> createState() => _ForensicsViewState();
}

class _ForensicsViewState extends State<ForensicsView> {
  int _currentPage = 0;
  final int _itemsPerPage = 10;
  bool _ascending = false;
  String _sortBy = 'timestamp'; // timestamp, severity, type

  final List<Map<String, dynamic>> _mockLedger = List.generate(
    45,
    (i) => {
      'id': 'LEG-${String.fromCharCodes([65 + (i ~/ 26)]) + String.fromCharCode(65 + (i % 26))}',
      'timestamp': DateTime.now().subtract(Duration(hours: 45 - i)),
      'severity': ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'][i % 4],
      'type': ['Access', 'Modification', 'Deletion', 'Configuration', 'Authentication'][i % 5],
      'entity': 'User-${(i % 12).toString().padLeft(2, '0')} / Asset-${(i % 8) + 1}',
      'action': 'Performed action', 
      'details': 'System audit trail entry #${i + 1}',
    },
  );

  List<Map<String, dynamic>> get sortedLedger {
    final sorted = List.of(_mockLedger);
    if (_sortBy == 'timestamp') {
      sorted.sort((a, b) => _ascending 
          ? a['timestamp'].compareTo(b['timestamp']) 
          : b['timestamp'].compareTo(a['timestamp']));
    } else if (_sortBy == 'severity') {
      const severityOrder = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3};
      sorted.sort((a, b) => _ascending
          ? (severityOrder[a['severity']] ?? 99).compareTo(severityOrder[b['severity']] ?? 99)
          : (severityOrder[b['severity']] ?? 99).compareTo(severityOrder[a['severity']] ?? 99));
    }
    return sorted;
  }

  List<Map<String, dynamic>> get paginatedLedger {
    final sorted = sortedLedger;
    final start = _currentPage * _itemsPerPage;
    final end = (start + _itemsPerPage).clamp(0, sorted.length);
    return sorted.sublist(start, end);
  }

  int get totalPages => (sortedLedger.length / _itemsPerPage).ceil();

  Color _getSeverityColor(String severity) {
    switch (severity) {
      case 'CRITICAL': return neonRed;
      case 'HIGH': return neonOrange;
      case 'MEDIUM': return quantumGreen;
      default: return holographicBlue;
    }
  }

  @override
  Widget build(BuildContext context) {
    final isMobile = MediaQuery.of(context).size.width < 600;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Forensics & Ledger'),
        elevation: 0,
        actions: [
          Padding(
            padding: const EdgeInsets.all(8),
            child: Center(
              child: Chip(
                label: Text('${sortedLedger.length} Entries'),
                backgroundColor: Theme.of(context).colorScheme.surface.withValues(alpha: 0.7),
                labelStyle: const TextStyle(color: Colors.white70, fontSize: 12),
              ),
            ),
          ),
        ],
      ),
      body: Column(
        children: [
          // Sort and filter bar
          Padding(
            padding: const EdgeInsets.all(12.0),
            child: Row(
              children: [
                Expanded(
                  child: PopupMenuButton<String>(
                    initialValue: _sortBy,
                    onSelected: (value) => setState(() => _sortBy = value),
                    itemBuilder: (context) => [
                      const PopupMenuItem(value: 'timestamp', child: Text('Sort by Time')),
                      const PopupMenuItem(value: 'severity', child: Text('Sort by Severity')),
                      const PopupMenuItem(value: 'type', child: Text('Sort by Type')),
                    ],
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                      decoration: BoxDecoration(
                        color: Colors.white.withValues(alpha: 0.05),
                        border: Border.all(color: neonCyan.withValues(alpha: 0.3), width: 1),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          const Icon(Icons.sort, color: Colors.white70, size: 18),
                          const SizedBox(width: 6),
                          Text(
                            'Sort: $_sortBy',
                            style: const TextStyle(fontSize: 12, color: Colors.white70),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                IconButton(
                  icon: Icon(
                    _ascending ? Icons.arrow_upward : Icons.arrow_downward,
                    color: Colors.white70,
                    size: 18,
                  ),
                  onPressed: () => setState(() => _ascending = !_ascending),
                  tooltip: 'Toggle order',
                ),
              ],
            ),
          ),
          // Entries list
          Expanded(
            child: paginatedLedger.isEmpty
                ? Center(
                    child: Text(
                      'No entries found',
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: Colors.white54,
                      ),
                    ),
                  )
                : ListView.builder(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                    itemCount: paginatedLedger.length,
                    itemBuilder: (context, index) => _buildLedgerEntry(
                      paginatedLedger[index],
                      isMobile,
                    ),
                  ),
          ),
          // Pagination controls
          Padding(
            padding: const EdgeInsets.all(12.0),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                IconButton(
                  icon: const Icon(Icons.chevron_left),
                  onPressed: _currentPage > 0 ? () => setState(() => _currentPage--) : null,
                ),
                Text(
                  'Page ${_currentPage + 1} of $totalPages',
                  style: const TextStyle(color: Colors.white70, fontSize: 12),
                ),
                IconButton(
                  icon: const Icon(Icons.chevron_right),
                  onPressed: _currentPage < totalPages - 1 ? () => setState(() => _currentPage++) : null,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildLedgerEntry(Map<String, dynamic> entry, bool isMobile) {
    final color = _getSeverityColor(entry['severity']);
    final time = entry['timestamp'] as DateTime;
    final timeStr = '${time.hour.toString().padLeft(2, '0')}:${time.minute.toString().padLeft(2, '0')}';

    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: GestureDetector(
        onTap: () => _showEntryDetail(entry),
        child: Container(
          decoration: ModernEffects.glassCard(hasGlow: false),
          child: Padding(
            padding: const EdgeInsets.all(12.0),
            child: isMobile
                ? Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Header row
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  entry['id'],
                                  style: const TextStyle(
                                    fontSize: 12,
                                    fontWeight: FontWeight.w600,
                                    color: Colors.white,
                                  ),
                                ),
                                const SizedBox(height: 4),
                                Text(
                                  entry['type'],
                                  style: const TextStyle(
                                    fontSize: 11,
                                    color: Colors.white70,
                                  ),
                                ),
                              ],
                            ),
                          ),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                            decoration: BoxDecoration(
                              color: color.withValues(alpha: 0.15),
                              border: Border.all(color: color, width: 0.5),
                              borderRadius: BorderRadius.circular(4),
                              boxShadow: ModernEffects.neonGlowShadows(color: color),
                            ),
                            child: Text(
                              entry['severity'],
                              style: TextStyle(
                                fontSize: 10,
                                fontWeight: FontWeight.bold,
                                color: color,
                              ),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      // Entity info
                      Row(
                        children: [
                          const Icon(Icons.account_tree, size: 14, color: Colors.white54),
                          const SizedBox(width: 6),
                          Expanded(
                            child: Text(
                              entry['entity'],
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                              style: const TextStyle(
                                fontSize: 11,
                                color: Colors.white70,
                              ),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 6),
                      // Time
                      Text(
                        timeStr,
                        style: const TextStyle(
                          fontSize: 10,
                          color: Colors.white54,
                        ),
                      ),
                    ],
                  )
                : Row(
                    children: [
                      // Severity badge
                      Container(
                        width: 4,
                        height: 60,
                        decoration: BoxDecoration(
                          color: color,
                          borderRadius: BorderRadius.circular(2),
                          boxShadow: ModernEffects.neonGlowShadows(color: color),
                        ),
                      ),
                      const SizedBox(width: 12),
                      // Content
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              entry['id'],
                              style: const TextStyle(
                                fontSize: 12,
                                fontWeight: FontWeight.w600,
                                color: Colors.white,
                              ),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              entry['entity'],
                              style: const TextStyle(
                                fontSize: 11,
                                color: Colors.white70,
                              ),
                            ),
                          ],
                        ),
                      ),
                      // Type + Severity
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.end,
                        children: [
                          Text(
                            entry['type'],
                            style: const TextStyle(
                              fontSize: 11,
                              color: Colors.white70,
                            ),
                          ),
                          const SizedBox(height: 4),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                            decoration: BoxDecoration(
                              color: color.withValues(alpha: 0.15),
                              border: Border.all(color: color, width: 0.5),
                              borderRadius: BorderRadius.circular(3),
                            ),
                            child: Text(
                              entry['severity'],
                              style: TextStyle(
                                fontSize: 9,
                                fontWeight: FontWeight.bold,
                                color: color,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
          ),
        ),
      ),
    );
  }

  void _showEntryDetail(Map<String, dynamic> entry) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: deepSpaceNavy,
        title: Text(entry['id']),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _detailRow('Type:', entry['type']),
            const SizedBox(height: 8),
            _detailRow('Entity:', entry['entity']),
            const SizedBox(height: 8),
            _detailRow('Severity:', entry['severity']),
            const SizedBox(height: 8),
            _detailRow('Time:', 
              '${(entry['timestamp'] as DateTime).hour}:${((entry['timestamp'] as DateTime).minute).toString().padLeft(2, '0')}'),
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: Colors.white.withValues(alpha: 0.05),
                border: Border.all(color: Colors.white24),
                borderRadius: BorderRadius.circular(4),
              ),
              child: Text(
                entry['details'],
                style: const TextStyle(fontSize: 11, color: Colors.white70),
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
                SnackBar(content: Text('Exported entry ${entry['id']}')),
              );
              Navigator.pop(context);
            },
            child: const Text('Export'),
          ),
        ],
      ),
    );
  }

  Widget _detailRow(String label, String value) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.white),
        ),
        const SizedBox(width: 8),
        Expanded(
          child: Text(
            value,
            style: const TextStyle(color: Colors.white70),
          ),
        ),
      ],
    );
  }
}
