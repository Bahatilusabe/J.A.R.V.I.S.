import 'package:flutter/material.dart';
import 'dart:math';

import '../theme.dart';
import '../utils/modern_effects.dart';
import '../services/pasm_service.dart';

/// Compact PASM panel widget for embedding in home dashboard
/// Shows top attack risk, threat confidence, and quick drill-down button
class PasmPanelWidget extends StatefulWidget {
  final VoidCallback onDrillDown;

  const PasmPanelWidget({required this.onDrillDown, super.key});

  @override
  State<PasmPanelWidget> createState() => _PasmPanelWidgetState();
}

class _PasmPanelWidgetState extends State<PasmPanelWidget> with TickerProviderStateMixin {
  double _topRiskScore = 0.0;
  double _confidence = 0.0;
  int _pathCount = 0;
  bool _loading = true;
  late AnimationController _pulseController;
  late Animation<double> _pulseAnimation;
  late AnimationController _scoreController;
  late Animation<double> _scoreAnimation;

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
      duration: const Duration(milliseconds: 2000),
      vsync: this,
    )..repeat();
    
    _scoreController = AnimationController(
      duration: const Duration(milliseconds: 1000),
      vsync: this,
    );

    _pulseAnimation = Tween<double>(begin: 0.8, end: 1.2).animate(
      CurvedAnimation(parent: _pulseController, curve: Curves.easeInOut),
    );

    _scoreAnimation = Tween<double>(begin: 0, end: 1).animate(
      CurvedAnimation(parent: _scoreController, curve: Curves.easeOutCubic),
    );

    _loadPasmData();
  }

  @override
  void dispose() {
    _pulseController.dispose();
    _scoreController.dispose();
    super.dispose();
  }

  Future<void> _loadPasmData() async {
    try {
      final service = PasmService();
      // Simulate fetching top risk (in real scenario, call backend /pasm/predict)
      final rng = Random();
      await Future.delayed(const Duration(milliseconds: 800));
      
      setState(() {
        _topRiskScore = 0.3 + rng.nextDouble() * 0.6; // 0.3 - 0.9 range
        _confidence = 0.6 + rng.nextDouble() * 0.35; // 0.6 - 0.95
        _pathCount = 3 + rng.nextInt(8); // 3 - 10 paths
        _loading = false;
      });

      _scoreController.forward();
    } catch (e) {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final isHighRisk = _topRiskScore > 0.65;
    
    return GestureDetector(
      onTap: widget.onDrillDown,
      child: Container(
        decoration: BoxDecoration(
          gradient: LinearGradient(
            colors: isHighRisk
              ? [const Color(0xFF8B0000).withValues(alpha: 0.2), const Color(0xFFFF4444).withValues(alpha: 0.1)]
              : [neonCyan.withValues(alpha: 0.15), holographicBlue.withValues(alpha: 0.08)],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
          border: Border.all(
            color: isHighRisk ? const Color(0xFFFF6B6B) : neonCyan,
            width: 1.2,
          ),
          borderRadius: BorderRadius.circular(12),
          boxShadow: [
            BoxShadow(
              color: (isHighRisk ? const Color(0xFFFF6B6B) : neonCyan).withValues(alpha: 0.25),
              blurRadius: 12,
              spreadRadius: 1,
            ),
          ],
        ),
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header with title and status
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Attack Surface',
                        style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: Colors.white70),
                      ),
                      const SizedBox(height: 2),
                      const Text(
                        'PASM Status',
                        style: TextStyle(fontSize: 11, color: Colors.white54),
                      ),
                    ],
                  ),
                  if (!_loading)
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                      decoration: BoxDecoration(
                        color: (isHighRisk ? const Color(0xFFFF4444) : neonCyan).withValues(alpha: 0.2),
                        border: Border.all(
                          color: isHighRisk ? const Color(0xFFFF4444) : neonCyan,
                          width: 0.5,
                        ),
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: Text(
                        isHighRisk ? '⚠ HIGH RISK' : '✓ MONITORED',
                        style: TextStyle(
                          fontSize: 9,
                          fontWeight: FontWeight.bold,
                          color: isHighRisk ? const Color(0xFFFF4444) : neonCyan,
                          letterSpacing: 0.5,
                        ),
                      ),
                    )
                  else
                    SizedBox(
                      width: 16,
                      height: 16,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        valueColor: AlwaysStoppedAnimation(neonCyan),
                      ),
                    ),
                ],
              ),
              const SizedBox(height: 12),

              // Risk score with animated pulse
              AnimatedBuilder(
                animation: _scoreAnimation,
                builder: (ctx, _) {
                  final score = _topRiskScore * _scoreAnimation.value;
                  return Row(
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text(
                              'Top Risk',
                              style: TextStyle(fontSize: 10, color: Colors.white54),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              '${(score * 100).toStringAsFixed(0)}%',
                              style: TextStyle(
                                fontSize: 24,
                                fontWeight: FontWeight.w700,
                                color: isHighRisk ? const Color(0xFFFF4444) : neonCyan,
                              ),
                            ),
                          ],
                        ),
                      ),
                      // Animated pulse indicator
                      AnimatedBuilder(
                        animation: _pulseAnimation,
                        builder: (ctx, _) {
                          return Transform.scale(
                            scale: _pulseAnimation.value,
                            child: Container(
                              width: 40,
                              height: 40,
                              decoration: BoxDecoration(
                                shape: BoxShape.circle,
                                gradient: RadialGradient(
                                  colors: isHighRisk
                                    ? [const Color(0xFFFF6B6B).withValues(alpha: 0.6), const Color(0xFFFF6B6B).withValues(alpha: 0.1)]
                                    : [neonCyan.withValues(alpha: 0.4), neonCyan.withValues(alpha: 0.05)],
                                ),
                                border: Border.all(
                                  color: isHighRisk ? const Color(0xFFFF6B6B) : neonCyan,
                                  width: 0.8,
                                ),
                              ),
                              child: Center(
                                child: Container(
                                  width: 16,
                                  height: 16,
                                  decoration: BoxDecoration(
                                    shape: BoxShape.circle,
                                    color: isHighRisk ? const Color(0xFFFF6B6B) : neonCyan,
                                  ),
                                ),
                              ),
                            ),
                          );
                        },
                      ),
                    ],
                  );
                },
              ),
              const SizedBox(height: 10),

              // Confidence and path count metrics
              if (!_loading)
                Row(
                  children: [
                    Expanded(
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
                        decoration: BoxDecoration(
                          color: Colors.white.withValues(alpha: 0.04),
                          border: Border.all(color: Colors.white10, width: 0.5),
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text(
                              'Confidence',
                              style: TextStyle(fontSize: 9, color: Colors.white54),
                            ),
                            const SizedBox(height: 2),
                            Text(
                              '${(_confidence * 100).toStringAsFixed(0)}%',
                              style: const TextStyle(
                                fontSize: 12,
                                fontWeight: FontWeight.w600,
                                color: Colors.white,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
                        decoration: BoxDecoration(
                          color: Colors.white.withValues(alpha: 0.04),
                          border: Border.all(color: Colors.white10, width: 0.5),
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text(
                              'Threats',
                              style: TextStyle(fontSize: 9, color: Colors.white54),
                            ),
                            const SizedBox(height: 2),
                            Text(
                              '$_pathCount paths',
                              style: const TextStyle(
                                fontSize: 12,
                                fontWeight: FontWeight.w600,
                                color: Colors.white,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),

              const SizedBox(height: 10),

              // Drill-down button
              SizedBox(
                width: double.infinity,
                child: Material(
                  color: Colors.transparent,
                  child: InkWell(
                    onTap: widget.onDrillDown,
                    borderRadius: BorderRadius.circular(6),
                    child: Container(
                      padding: const EdgeInsets.symmetric(vertical: 8),
                      decoration: BoxDecoration(
                        gradient: LinearGradient(
                          colors: [neonCyan.withValues(alpha: 0.2), holographicBlue.withValues(alpha: 0.1)],
                        ),
                        border: Border.all(color: neonCyan.withValues(alpha: 0.4), width: 0.8),
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: const [
                          Text(
                            'View Full Analysis',
                            style: TextStyle(
                              fontSize: 11,
                              fontWeight: FontWeight.w600,
                              color: Colors.white70,
                            ),
                          ),
                          SizedBox(width: 6),
                          Icon(Icons.arrow_forward, size: 12, color: Colors.white54),
                        ],
                      ),
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
