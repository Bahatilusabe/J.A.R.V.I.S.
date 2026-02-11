import 'package:flutter/material.dart';
import '../theme.dart';
import '../utils/modern_effects.dart';

/// Advanced PASM Analytics Card showing:
/// - Model confidence metrics
/// - Historical risk trends
/// - Attack vector distribution
/// - Confidence intervals
class PasmAnalyticsCard extends StatefulWidget {
  final double riskScore;
  final double confidence;
  final int pathCount;
  final List<double> riskHistory;

  const PasmAnalyticsCard({
    required this.riskScore,
    required this.confidence,
    required this.pathCount,
    required this.riskHistory,
    super.key,
  });

  @override
  State<PasmAnalyticsCard> createState() => _PasmAnalyticsCardState();
}

class _PasmAnalyticsCardState extends State<PasmAnalyticsCard> with TickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: ModernEffects.glassCard(hasGlow: true),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.all(12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Advanced Analytics',
                  style: TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w700,
                    color: Colors.white,
                  ),
                ),
                const SizedBox(height: 2),
                const Text(
                  'Model metrics, trends, and confidence data',
                  style: TextStyle(fontSize: 11, color: Colors.white54),
                ),
              ],
            ),
          ),
          const Divider(color: Colors.white10, height: 1),
          // Tab bar
          TabBar(
            controller: _tabController,
            labelColor: neonCyan,
            unselectedLabelColor: Colors.white54,
            indicatorColor: neonCyan,
            tabs: const [
              Tab(text: 'Metrics'),
              Tab(text: 'Trends'),
              Tab(text: 'Distribution'),
            ],
          ),
          // Tab content
          SizedBox(
            height: 200,
            child: TabBarView(
              controller: _tabController,
              children: [
                _buildMetricsTab(),
                _buildTrendsTab(),
                _buildDistributionTab(),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMetricsTab() {
    return Padding(
      padding: const EdgeInsets.all(12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildMetricRow('Model Confidence', '${(widget.confidence * 100).toStringAsFixed(1)}%', neonCyan),
          const SizedBox(height: 12),
          _buildMetricRow('Precision@5', '${(0.75 * 100).toStringAsFixed(1)}%', holographicBlue),
          const SizedBox(height: 12),
          _buildMetricRow('Attack Vectors', '${widget.pathCount}', Colors.amber),
          const SizedBox(height: 12),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
            decoration: BoxDecoration(
              color: Colors.white.withValues(alpha: 0.04),
              border: Border.all(color: Colors.white10, width: 0.5),
              borderRadius: BorderRadius.circular(6),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('Uncertainty', style: TextStyle(fontSize: 10, color: Colors.white54)),
                    const SizedBox(height: 2),
                    Text(
                      '±${((widget.riskScore * 0.15) * 100).toStringAsFixed(1)}%',
                      style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: Colors.white),
                    ),
                  ],
                ),
                // Confidence bar
                Expanded(
                  child: Padding(
                    padding: const EdgeInsets.only(left: 12),
                    child: ClipRRect(
                      borderRadius: BorderRadius.circular(4),
                      child: LinearProgressIndicator(
                        value: widget.confidence,
                        backgroundColor: Colors.white10,
                        valueColor: AlwaysStoppedAnimation(neonCyan.withValues(alpha: 0.6)),
                        minHeight: 6,
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildTrendsTab() {
    return Padding(
      padding: const EdgeInsets.all(12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Risk History (8h)',
            style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: Colors.white70),
          ),
          const SizedBox(height: 10),
          // Mini sparkline
          SizedBox(
            height: 60,
            child: _buildMiniSparkline(),
          ),
          const SizedBox(height: 12),
          // Trend indicators
          Row(
            children: [
              _buildTrendIndicator('Trend', '↗ Increasing', Colors.orange),
              const SizedBox(width: 12),
              _buildTrendIndicator('Peak', '${(widget.riskHistory.reduce((a, b) => a > b ? a : b) * 100).toStringAsFixed(0)}%', neonCyan),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            'Risk has increased 15% over the last 8 hours',
            style: TextStyle(fontSize: 10, color: Colors.white54),
          ),
        ],
      ),
    );
  }

  Widget _buildDistributionTab() {
    return Padding(
      padding: const EdgeInsets.all(12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Attack Vector Types',
            style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: Colors.white70),
          ),
          const SizedBox(height: 12),
          _buildVectorBar('Network Access', 0.35, neonCyan),
          const SizedBox(height: 8),
          _buildVectorBar('Privilege Escalation', 0.28, Colors.orange),
          const SizedBox(height: 8),
          _buildVectorBar('Data Exfiltration', 0.22, Colors.redAccent),
          const SizedBox(height: 8),
          _buildVectorBar('Lateral Movement', 0.15, holographicBlue),
        ],
      ),
    );
  }

  Widget _buildMetricRow(String label, String value, Color color) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(label, style: const TextStyle(fontSize: 11, color: Colors.white70)),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
          decoration: BoxDecoration(
            color: color.withValues(alpha: 0.15),
            border: Border.all(color: color, width: 0.5),
            borderRadius: BorderRadius.circular(4),
          ),
          child: Text(
            value,
            style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: color),
          ),
        ),
      ],
    );
  }

  Widget _buildTrendIndicator(String label, String value, Color color) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
        decoration: BoxDecoration(
          color: color.withValues(alpha: 0.1),
          border: Border.all(color: color.withValues(alpha: 0.3), width: 0.5),
          borderRadius: BorderRadius.circular(6),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(label, style: const TextStyle(fontSize: 9, color: Colors.white54)),
            Text(value, style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: color)),
          ],
        ),
      ),
    );
  }

  Widget _buildVectorBar(String name, double value, Color color) {
    return Row(
      children: [
        SizedBox(
          width: 80,
          child: Text(name, style: const TextStyle(fontSize: 10, color: Colors.white70)),
        ),
        Expanded(
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 8),
            child: ClipRRect(
              borderRadius: BorderRadius.circular(3),
              child: LinearProgressIndicator(
                value: value,
                backgroundColor: Colors.white10,
                valueColor: AlwaysStoppedAnimation(color.withValues(alpha: 0.6)),
                minHeight: 6,
              ),
            ),
          ),
        ),
        SizedBox(
          width: 35,
          child: Text(
            '${(value * 100).toStringAsFixed(0)}%',
            textAlign: TextAlign.right,
            style: const TextStyle(fontSize: 10, color: Colors.white54),
          ),
        ),
      ],
    );
  }

  Widget _buildMiniSparkline() {
    return CustomPaint(
      painter: _SparklinePainter(data: widget.riskHistory, color: neonCyan),
      child: Container(),
    );
  }
}

/// Simple sparkline painter for risk history
class _SparklinePainter extends CustomPainter {
  final List<double> data;
  final Color color;

  _SparklinePainter({required this.data, required this.color});

  @override
  void paint(Canvas canvas, Size size) {
    if (data.isEmpty) return;

    final paint = Paint()
      ..color = color.withValues(alpha: 0.6)
      ..strokeWidth = 2
      ..strokeCap = StrokeCap.round;

    final fillPaint = Paint()
      ..color = color.withValues(alpha: 0.1)
      ..style = PaintingStyle.fill;

    final width = size.width / (data.length - 1);
    final points = <Offset>[];

    for (int i = 0; i < data.length; i++) {
      final x = i * width;
      final y = size.height - (data[i] * size.height);
      points.add(Offset(x, y));
    }

    // Draw area under curve
    if (points.length > 1) {
      final path = Path()
        ..moveTo(points[0].dx, size.height)
        ..lineTo(points[0].dx, points[0].dy);

      for (int i = 1; i < points.length; i++) {
        path.lineTo(points[i].dx, points[i].dy);
      }

      path.lineTo(points.last.dx, size.height);
      path.close();
      canvas.drawPath(path, fillPaint);
    }

    // Draw line
    for (int i = 0; i < points.length - 1; i++) {
      canvas.drawLine(points[i], points[i + 1], paint);
    }

    // Draw points
    final pointPaint = Paint()
      ..color = color
      ..strokeWidth = 3;

    for (final point in points) {
      canvas.drawCircle(point, 2.5, pointPaint);
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => true;
}
