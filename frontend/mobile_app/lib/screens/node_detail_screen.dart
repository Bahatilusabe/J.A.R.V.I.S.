import 'package:flutter/material.dart';
import '../services/federation_service.dart';

class SimpleLineChart extends StatelessWidget {
  final List<double> values;
  final String title;
  final Color color;
  final double height;

  const SimpleLineChart({
    required this.values,
    required this.title,
    required this.color,
    this.height = 200,
  });

  @override
  Widget build(BuildContext context) {
    if (values.isEmpty) {
      return SizedBox(
        height: height,
        child: Center(
          child: Text('No data for $title'),
        ),
      );
    }

    // Find min/max for scaling
    final maxVal = values.reduce((a, b) => a > b ? a : b);
    final minVal = values.reduce((a, b) => a < b ? a : b);
    final range = maxVal - minVal;
    final padding = range * 0.1;
    final scaledMax = maxVal + padding;
    final scaledMin = minVal - padding;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 8),
        SizedBox(
          height: height,
          child: CustomPaint(
            painter: LineChartPainter(
              values: values,
              maxValue: scaledMax,
              minValue: scaledMin,
              color: color,
            ),
            size: Size.infinite,
          ),
        ),
      ],
    );
  }
}

class LineChartPainter extends CustomPainter {
  final List<double> values;
  final double maxValue;
  final double minValue;
  final Color color;

  LineChartPainter({
    required this.values,
    required this.maxValue,
    required this.minValue,
    required this.color,
  });

  @override
  void paint(Canvas canvas, Size size) {
    if (values.isEmpty) return;

    final paint = Paint()
      ..color = color
      ..strokeWidth = 2.0
      ..strokeCap = StrokeCap.round
      ..strokeJoin = StrokeJoin.round;

    final gridPaint = Paint()
      ..color = Colors.grey.withValues(alpha: 0.2)
      ..strokeWidth = 0.5;

    // Draw grid lines
    for (int i = 0; i <= 4; i++) {
      final y = (size.height / 4) * i;
      canvas.drawLine(Offset(0, y), Offset(size.width, y), gridPaint);
    }

    // Calculate points
    final range = maxValue - minValue;
    final pointSpacing = size.width / (values.length - 1);

    final points = <Offset>[];
    for (int i = 0; i < values.length; i++) {
      final x = pointSpacing * i;
      final normalizedValue = (values[i] - minValue) / range;
      final y = size.height * (1 - normalizedValue);
      points.add(Offset(x, y));
    }

    // Draw line
    for (int i = 0; i < points.length - 1; i++) {
      canvas.drawLine(points[i], points[i + 1], paint);
    }

    // Draw points
    final pointPaint = Paint()
      ..color = color
      ..strokeWidth = 4.0;
    for (final point in points) {
      canvas.drawCircle(point, 3, pointPaint);
    }

    // Draw axis labels
    final textPainter = TextPainter(
      textDirection: TextDirection.ltr,
    );

    // Min label
    textPainter.text = TextSpan(
      text: minValue.toStringAsFixed(2),
      style: const TextStyle(color: Colors.grey, fontSize: 10),
    );
    textPainter.layout();
    textPainter.paint(canvas, Offset(2, size.height - 12));

    // Max label
    textPainter.text = TextSpan(
      text: maxValue.toStringAsFixed(2),
      style: const TextStyle(color: Colors.grey, fontSize: 10),
    );
    textPainter.layout();
    textPainter.paint(canvas, Offset(2, -5));
  }

  @override
  bool shouldRepaint(LineChartPainter oldDelegate) {
    return oldDelegate.values != values || oldDelegate.color != color;
  }
}

class NodeDetailScreen extends StatefulWidget {
  final String nodeId;
  final FederationService federationService;

  const NodeDetailScreen({
    required this.nodeId,
    required this.federationService,
  });

  @override
  State<NodeDetailScreen> createState() => _NodeDetailScreenState();
}

class _NodeDetailScreenState extends State<NodeDetailScreen> {
  late Future<Map<String, dynamic>> _detailFuture;
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    _loadNodeDetail();
  }

  void _loadNodeDetail() {
    setState(() {
      _isLoading = true;
      _detailFuture = widget.federationService.getNodeDetail(widget.nodeId, limit: 100);
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Node: ${widget.nodeId}'),
        elevation: 0,
      ),
      body: FutureBuilder<Map<String, dynamic>>(
        future: _detailFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting && _isLoading) {
            return const Center(
              child: CircularProgressIndicator(),
            );
          }

          if (snapshot.hasError) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.error_outline, size: 64, color: Colors.red),
                  const SizedBox(height: 16),
                  Text(
                    'Error: ${snapshot.error}',
                    textAlign: TextAlign.center,
                    style: const TextStyle(fontSize: 16),
                  ),
                  const SizedBox(height: 16),
                  ElevatedButton(
                    onPressed: _loadNodeDetail,
                    child: const Text('Retry'),
                  ),
                ],
              ),
            );
          }

          if (!snapshot.hasData || snapshot.data == null) {
            return const Center(
              child: Text('No data available'),
            );
          }

          final data = snapshot.data!;
          final stats = (data['stats'] as Map<String, dynamic>?) ?? {};
          final history = (data['history'] as List<dynamic>?) ?? [];

          // Extract trend data
          final healthTrend = history.map<double>((e) => ((e as Map<String, dynamic>)['sync_health'] as num?)?.toDouble() ?? 0.0).toList();
          final trustTrend = history.map<double>((e) => ((e as Map<String, dynamic>)['trust_score'] as num?)?.toDouble() ?? 0.0).toList();

          return RefreshIndicator(
            onRefresh: () async {
              _loadNodeDetail();
              await _detailFuture;
            },
            child: ListView(
              padding: const EdgeInsets.all(16),
              children: [
                // Node ID card
                Card(
                  elevation: 2,
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          'Node Information',
                          style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                        ),
                        const SizedBox(height: 12),
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            const Text('Node ID:', style: TextStyle(fontSize: 14)),
                            Text(
                              widget.nodeId,
                              style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold),
                            ),
                          ],
                        ),
                        const SizedBox(height: 8),
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            const Text('History Entries:', style: TextStyle(fontSize: 14)),
                            Text(
                              '${history.length}',
                              style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 20),

                // Statistics card
                Card(
                  elevation: 2,
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          'Health & Trust Statistics',
                          style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                        ),
                        const SizedBox(height: 16),
                        _buildStatRow(
                          'Avg Health',
                          (stats['avg_health'] as num?)?.toStringAsFixed(2) ?? 'N/A',
                          Colors.blue,
                        ),
                        const SizedBox(height: 12),
                        _buildStatRow(
                          'Min Health',
                          (stats['min_health'] as num?)?.toStringAsFixed(2) ?? 'N/A',
                          Colors.orange,
                        ),
                        const SizedBox(height: 12),
                        _buildStatRow(
                          'Max Health',
                          (stats['max_health'] as num?)?.toStringAsFixed(2) ?? 'N/A',
                          Colors.green,
                        ),
                        const SizedBox(height: 16),
                        const Divider(),
                        const SizedBox(height: 16),
                        _buildStatRow(
                          'Avg Trust',
                          (stats['avg_trust'] as num?)?.toStringAsFixed(2) ?? 'N/A',
                          Colors.blue,
                        ),
                        const SizedBox(height: 12),
                        _buildStatRow(
                          'Min Trust',
                          (stats['min_trust'] as num?)?.toStringAsFixed(2) ?? 'N/A',
                          Colors.orange,
                        ),
                        const SizedBox(height: 12),
                        _buildStatRow(
                          'Max Trust',
                          (stats['max_trust'] as num?)?.toStringAsFixed(2) ?? 'N/A',
                          Colors.green,
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 20),

                // Trend charts
                Card(
                  elevation: 2,
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          'Trends',
                          style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                        ),
                        const SizedBox(height: 16),
                        if (healthTrend.isNotEmpty)
                          SimpleLineChart(
                            values: healthTrend,
                            title: 'Sync Health Trend',
                            color: Colors.blue,
                          )
                        else
                          const Text('No health data'),
                        const SizedBox(height: 24),
                        if (trustTrend.isNotEmpty)
                          SimpleLineChart(
                            values: trustTrend,
                            title: 'Trust Score Trend',
                            color: Colors.green,
                          )
                        else
                          const Text('No trust data'),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 20),

                // History list
                Card(
                  elevation: 2,
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          'Recent History',
                          style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                        ),
                        const SizedBox(height: 12),
                        if (history.isEmpty)
                          const Text('No history entries available')
                        else
                          ListView.separated(
                            shrinkWrap: true,
                            physics: const NeverScrollableScrollPhysics(),
                            itemCount: history.length > 10 ? 10 : history.length,
                            separatorBuilder: (_, __) => const Divider(height: 1),
                            itemBuilder: (context, index) {
                              final entry = history[history.length - 1 - index] as Map<String, dynamic>;
                              return Padding(
                                padding: const EdgeInsets.symmetric(vertical: 8),
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      entry['timestamp'] ?? 'Unknown',
                                      style: const TextStyle(fontSize: 12, color: Colors.grey),
                                    ),
                                    const SizedBox(height: 4),
                                    Row(
                                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                      children: [
                                        Text(
                                          'Health: ${(entry['sync_health'] as num?)?.toStringAsFixed(2) ?? "N/A"}',
                                          style: const TextStyle(fontSize: 13),
                                        ),
                                        Text(
                                          'Trust: ${(entry['trust_score'] as num?)?.toStringAsFixed(2) ?? "N/A"}',
                                          style: const TextStyle(fontSize: 13),
                                        ),
                                      ],
                                    ),
                                  ],
                                ),
                              );
                            },
                          ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 20),
              ],
            ),
          );
        },
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: _loadNodeDetail,
        child: const Icon(Icons.refresh),
      ),
    );
  }

  Widget _buildStatRow(String label, String value, Color color) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(
          label,
          style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w500),
        ),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
          decoration: BoxDecoration(
            color: color.withValues(alpha: 0.2),
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: color, width: 1),
          ),
          child: Text(
            value,
            style: TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.bold,
              color: color,
            ),
          ),
        ),
      ],
    );
  }
}
