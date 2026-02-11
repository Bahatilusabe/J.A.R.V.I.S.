import 'package:flutter/material.dart';
import '../theme.dart';

/// Widget to display uncertainty estimates with confidence intervals
class UncertaintyIndicator extends StatelessWidget {
  final double mean;
  final double std;
  final String label;

  const UncertaintyIndicator({
    required this.mean,
    required this.std,
    this.label = 'Risk Estimate',
    super.key,
  });

  @override
  Widget build(BuildContext context) {
    final lowerBound = ((mean - std).clamp(0, 1) as double);
    final upperBound = ((mean + std).clamp(0, 1) as double);

    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.04),
        border: Border.all(color: Colors.white10, width: 0.5),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            label,
            style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: Colors.white70),
          ),
          const SizedBox(height: 8),
          // Main value with CI
          Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '${(mean * 100).toStringAsFixed(1)}%',
                      style: TextStyle(
                        fontSize: 24,
                        fontWeight: FontWeight.w700,
                        color: mean > 0.65 ? const Color(0xFFFF6B6B) : neonCyan,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      '[${(lowerBound * 100).toStringAsFixed(1)}% - ${(upperBound * 100).toStringAsFixed(1)}%]',
                      style: const TextStyle(fontSize: 10, color: Colors.white54),
                    ),
                  ],
                ),
              ),
              // Confidence bar visualization
              Expanded(
                child: _buildConfidenceBand(lowerBound, mean, upperBound),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildConfidenceBand(double lower, double mid, double upper) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.end,
      children: [
        const Text('CI 95%', style: TextStyle(fontSize: 9, color: Colors.white54)),
        const SizedBox(height: 6),
        // Horizontal confidence interval bar
        Container(
          height: 20,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(10),
            color: Colors.white.withValues(alpha: 0.02),
            border: Border.all(color: Colors.white10, width: 0.5),
          ),
          child: Stack(
            children: [
              // Background range
              Positioned(
                left: lower * 100,
                right: (1 - upper) * 100,
                child: Container(
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(8),
                    color: neonCyan.withValues(alpha: 0.2),
                  ),
                ),
              ),
              // Center point
              Positioned(
                left: mid * 100 - 2,
                top: 0,
                bottom: 0,
                child: Container(
                  width: 4,
                  decoration: BoxDecoration(
                    color: neonCyan,
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

/// Risk band visualization showing confidence intervals
class RiskBandChart extends StatelessWidget {
  final List<double> means;
  final List<double> stds;
  final List<String> labels;

  const RiskBandChart({
    required this.means,
    required this.stds,
    required this.labels,
    super.key,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: List.generate(means.length, (i) {
        final mean = means[i];
        final std = stds[i];
        return Padding(
          padding: const EdgeInsets.only(bottom: 12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                labels[i],
                style: const TextStyle(fontSize: 10, color: Colors.white70),
              ),
              const SizedBox(height: 4),
              _buildRiskBar(mean, std),
            ],
          ),
        );
      }),
    );
  }

  Widget _buildRiskBar(double mean, double std) {
    final lower = (mean - std).clamp(0, 1);
    final upper = (mean + std).clamp(0, 1);
    final isHighRisk = mean > 0.65;

    return Container(
      height: 24,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(6),
        color: Colors.white.withValues(alpha: 0.02),
        border: Border.all(
          color: (isHighRisk ? const Color(0xFFFF6B6B) : neonCyan).withValues(alpha: 0.3),
          width: 0.5,
        ),
      ),
      child: Stack(
        children: [
          // CI band
          Positioned(
            left: lower * 100,
            right: (1 - upper) * 100,
            top: 0,
            bottom: 0,
            child: Container(
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(5),
                color: (isHighRisk ? const Color(0xFFFF6B6B) : neonCyan).withValues(alpha: 0.15),
              ),
            ),
          ),
          // Mean line
          Positioned(
            left: mean * 100,
            top: 0,
            bottom: 0,
            child: Container(
              width: 2,
              color: isHighRisk ? const Color(0xFFFF6B6B) : neonCyan,
            ),
          ),
          // Label
          Positioned(
            left: 8,
            top: 0,
            bottom: 0,
            child: Align(
              alignment: Alignment.centerLeft,
              child: Text(
                '${(mean * 100).toStringAsFixed(0)}%',
                style: TextStyle(
                  fontSize: 10,
                  fontWeight: FontWeight.w600,
                  color: isHighRisk ? const Color(0xFFFF6B6B) : neonCyan,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
