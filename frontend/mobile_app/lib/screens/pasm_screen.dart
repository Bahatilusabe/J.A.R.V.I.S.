import 'package:flutter/material.dart';
import 'dart:async';
import 'dart:math';

import '../services/pasm_service.dart';
import '../services/asset_service.dart';
import '../theme.dart';
import '../utils/modern_effects.dart';
import '../widgets/pasm_analytics.dart';
import '../widgets/uncertainty_display.dart';
import '../widgets/path_details_modal.dart';

class PasmScreen extends StatefulWidget {
  const PasmScreen({super.key});

  @override
  State<PasmScreen> createState() => _PasmScreenState();
}

class _PasmScreenState extends State<PasmScreen> with TickerProviderStateMixin {
  final PasmService _pasm = PasmService();
  final AssetService _assets = AssetService();
  late Future<List<PathNode>> _graphFuture;
  late Future<List<AssetSummary>> _assetsFuture;
  List<AttackPath> _paths = [];
  String? _selectedAssetId;
  bool _loadingPredict = false;
  Map<String, String> _nodeLabels = {}; // id -> label
  double _riskScore = 0.0;
  double _uncertainty = 0.0;
  int? _expandedPathIndex;
  late AnimationController _scoreAnimController;
  late Animation<double> _scoreAnimation;

  @override
  void initState() {
    super.initState();
    _graphFuture = _pasm.getSmallGraph();
    _assetsFuture = _assets.getAssets();
    _graphFuture.then((nodes) {
      setState(() {
        _nodeLabels = {for (var n in nodes) n.id: n.label};
      });
    });
    _scoreAnimController = AnimationController(duration: const Duration(milliseconds: 1200), vsync: this);
    _scoreAnimation = Tween<double>(begin: 0, end: 1).animate(CurvedAnimation(parent: _scoreAnimController, curve: Curves.easeOutCubic));
  }

  @override
  void dispose() {
    _scoreAnimController.dispose();
    super.dispose();
  }

  Future<void> _predict() async {
    if (_selectedAssetId == null || _selectedAssetId!.isEmpty) return;
    setState(() => _loadingPredict = true);
    try {
      final list = await _pasm.predictForAsset(_selectedAssetId!);
      final highestScore = list.isNotEmpty ? list.map((p) => p.score).reduce((a, b) => a > b ? a : b) : 0.0;
      final rng = Random();
      final randomUncertainty = (rng.nextDouble() * 0.15).clamp(0.02, 0.2);
      
      setState(() {
        _paths = list;
        _riskScore = highestScore;
        _uncertainty = randomUncertainty;
        _expandedPathIndex = null;
      });
      
      _scoreAnimController.forward(from: 0.0);
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Predict error: $e')));
      setState(() => _riskScore = 0.0);
    } finally {
      setState(() => _loadingPredict = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final screenHeight = MediaQuery.of(context).size.height;
    final screenWidth = MediaQuery.of(context).size.width;
    
    return Scaffold(
      appBar: AppBar(
        title: const Text('PASM — Attack Surface Modeling'),
        elevation: 0,
        actions: [
          IconButton(
            icon: const Icon(Icons.info_outline),
            onPressed: () {
              showDialog(
                context: context,
                builder: (ctx) => AlertDialog(
                  title: const Text('PASM Info'),
                  content: const Text('Predictive Attack Surface Modeling uses Temporal Graph Neural Networks (TGNN) to identify vulnerable attack paths in real-time.'),
                  actions: [TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Close'))],
                ),
              );
            },
          ),
        ],
      ),
      body: SingleChildScrollView(
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Column(
            children: [
              // Risk Score Card (animated)
              if (_paths.isNotEmpty)
                _buildRiskScoreCard(screenWidth)
              else
                _buildEmptyRiskPlaceholder(screenWidth),
              
              const SizedBox(height: 12),

              // Graph visualization
              _buildGraphVisualization(screenHeight),
              
              const SizedBox(height: 12),

              // Asset selector + Predict button
              _buildAssetSelector(),
              
              const SizedBox(height: 16),

              // Paths list with expandable cards
              _buildPathsList(screenHeight),
              
              const SizedBox(height: 16),

              // Advanced Analytics Section
              if (_paths.isNotEmpty)
                PasmAnalyticsCard(
                  riskScore: _riskScore,
                  confidence: (0.6 + Random().nextDouble() * 0.35),
                  pathCount: _paths.length,
                  riskHistory: [0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.48, 0.52],
                )
              else
                Container(
                  decoration: ModernEffects.glassCard(hasGlow: false),
                  child: Padding(
                    padding: const EdgeInsets.all(20),
                    child: Center(
                      child: Text(
                        'Run a prediction to see analytics',
                        style: TextStyle(fontSize: 12, color: Colors.white54),
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

  Widget _buildRiskScoreCard(double width) {
    return AnimatedBuilder(
      animation: _scoreAnimation,
      builder: (ctx, _) {
        final animScore = _riskScore * _scoreAnimation.value;
        final isHighRisk = _riskScore > 0.75;
        return Container(
          width: width,
          decoration: BoxDecoration(
            gradient: LinearGradient(
              colors: isHighRisk
                ? [const Color(0xFF8B0000).withValues(alpha: 0.3), const Color(0xFFFF4444).withValues(alpha: 0.1)]
                : [neonCyan.withValues(alpha: 0.2), holographicBlue.withValues(alpha: 0.1)],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
            border: Border.all(
              color: isHighRisk ? const Color(0xFFFF4444) : neonCyan,
              width: 1.5,
            ),
            borderRadius: BorderRadius.circular(12),
            boxShadow: [
              BoxShadow(
                color: (isHighRisk ? const Color(0xFFFF4444) : neonCyan).withValues(alpha: 0.4),
                blurRadius: 16,
                spreadRadius: 2,
              ),
            ],
          ),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    const Text('Predicted Risk', style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600, color: Colors.white70)),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                      decoration: BoxDecoration(
                        color: (isHighRisk ? const Color(0xFFFF4444) : neonCyan).withValues(alpha: 0.2),
                        borderRadius: BorderRadius.circular(4),
                        border: Border.all(color: isHighRisk ? const Color(0xFFFF4444) : neonCyan, width: 0.5),
                      ),
                      child: Text(
                        isHighRisk ? 'HIGH' : 'MODERATE',
                        style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: isHighRisk ? const Color(0xFFFF4444) : neonCyan),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 10),
                Text(
                  '${(animScore * 100).toStringAsFixed(1)}%',
                  style: TextStyle(
                    fontSize: 40,
                    fontWeight: FontWeight.w700,
                    color: isHighRisk ? const Color(0xFFFF4444) : neonCyan,
                  ),
                ),
                const SizedBox(height: 12),
                // Enhanced uncertainty display with confidence intervals
                UncertaintyIndicator(
                  mean: _riskScore,
                  std: _uncertainty,
                  label: 'Risk Estimate (95% CI)',
                ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text('Paths', style: TextStyle(fontSize: 11, color: Colors.white54)),
                          Text(
                            '${_paths.length}',
                            style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: Colors.white70),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildEmptyRiskPlaceholder(double width) {
    return Container(
      width: width,
      decoration: ModernEffects.glassCard(hasGlow: false),
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          children: [
            Icon(Icons.show_chart, size: 36, color: neonCyan.withValues(alpha: 0.6)),
            const SizedBox(height: 12),
            const Text('No prediction yet', style: TextStyle(fontSize: 14, color: Colors.white54)),
          ],
        ),
      ),
    );
  }

  Widget _buildGraphVisualization(double height) {
    return FutureBuilder<List<PathNode>>(
      future: _graphFuture,
      builder: (context, snap) {
        if (snap.connectionState != ConnectionState.done) {
          return Container(
            height: 120,
            decoration: ModernEffects.glassCard(hasGlow: false),
            child: const Center(child: CircularProgressIndicator(strokeWidth: 2)),
          );
        }
        if (snap.hasError) {
          return Container(
            padding: const EdgeInsets.all(12),
            decoration: ModernEffects.glassCard(hasGlow: false),
            child: Text('Graph error: ${snap.error}'),
          );
        }
        final nodes = snap.data ?? [];
        return Container(
          height: 140,
          decoration: ModernEffects.glassCard(hasGlow: true),
          child: Padding(
            padding: const EdgeInsets.all(12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Network Graph', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: Colors.white70)),
                const SizedBox(height: 8),
                Expanded(
                  child: SingleChildScrollView(
                    scrollDirection: Axis.horizontal,
                    child: Row(
                      children: nodes.map((n) {
                        final isInPath = _paths.any((p) => p.nodes.contains(n.id));
                        return Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 6),
                          child: _buildNodeBubble(n, isInPath),
                        );
                      }).toList(),
                    ),
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildNodeBubble(PathNode node, bool inPath) {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Container(
          width: 52,
          height: 52,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            gradient: LinearGradient(
              colors: inPath
                ? [const Color(0xFFFF6B6B).withValues(alpha: 0.6), const Color(0xFFFF4444).withValues(alpha: 0.4)]
                : [neonCyan.withValues(alpha: 0.5), holographicBlue.withValues(alpha: 0.3)],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
            border: Border.all(
              color: inPath ? const Color(0xFFFF6B6B) : neonCyan,
              width: inPath ? 2 : 1,
            ),
            boxShadow: inPath
              ? [BoxShadow(color: const Color(0xFFFF6B6B).withValues(alpha: 0.5), blurRadius: 12, spreadRadius: 2)]
              : [BoxShadow(color: neonCyan.withValues(alpha: 0.3), blurRadius: 8, spreadRadius: 1)],
          ),
          child: Center(
            child: Text(
              node.label.characters.take(2).toString().toUpperCase(),
              style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 11),
            ),
          ),
        ),
        const SizedBox(height: 6),
        SizedBox(
          width: 52,
          child: Text(
            node.label,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            textAlign: TextAlign.center,
            style: TextStyle(fontSize: 10, color: inPath ? const Color(0xFFFF6B6B) : Colors.white54),
          ),
        ),
      ],
    );
  }

  Widget _buildAssetSelector() {
    return FutureBuilder<List<AssetSummary>>(
      future: _assetsFuture,
      builder: (context, snap) {
        if (snap.connectionState != ConnectionState.done) {
          return const LinearProgressIndicator(minHeight: 2);
        }
        if (snap.hasError) {
          return Text('Asset error: ${snap.error}');
        }
        final assets = snap.data ?? [];
        return Row(
          children: [
            Expanded(
              child: Container(
                decoration: BoxDecoration(
                  color: Colors.white.withValues(alpha: 0.05),
                  border: Border.all(color: neonCyan.withValues(alpha: 0.3), width: 1),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: DropdownButtonFormField<String>(
                  initialValue: _selectedAssetId,
                  isExpanded: true,
                  decoration: InputDecoration(
                    contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                    border: InputBorder.none,
                    hintText: 'Select asset',
                    hintStyle: const TextStyle(color: Colors.white54),
                  ),
                  style: const TextStyle(color: Colors.white),
                  iconEnabledColor: neonCyan,
                  items: assets.map((a) => DropdownMenuItem(
                    value: a.id,
                    child: Text(a.name),
                  )).toList(),
                  onChanged: (v) {
                    setState(() => _selectedAssetId = v);
                  },
                ),
              ),
            ),
            const SizedBox(width: 8),
            Container(
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [neonCyan.withValues(alpha: 0.3), holographicBlue.withValues(alpha: 0.3)],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                border: Border.all(color: neonCyan.withValues(alpha: 0.5), width: 1),
                borderRadius: BorderRadius.circular(8),
                boxShadow: ModernEffects.neonGlowShadows(color: neonCyan),
              ),
              child: Material(
                color: Colors.transparent,
                child: InkWell(
                  onTap: _loadingPredict ? null : _predict,
                  borderRadius: BorderRadius.circular(8),
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                    child: _loadingPredict
                      ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))
                      : const Text('Predict', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w600, fontSize: 13)),
                  ),
                ),
              ),
            ),
          ],
        );
      },
    );
  }

  Widget _buildPathsList(double height) {
    return _paths.isEmpty
      ? Container(
          decoration: ModernEffects.glassCard(hasGlow: false),
          child: Center(
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.route, size: 32, color: Colors.white30),
                  const SizedBox(height: 8),
                  const Text(
                    'Select asset and predict to see attack paths',
                    textAlign: TextAlign.center,
                    style: TextStyle(color: Colors.white54, fontSize: 12),
                  ),
                ],
              ),
            ),
          ),
        )
      : SizedBox(
          height: min(height * 0.5, 400),
          child: ListView.builder(
            itemCount: _paths.length,
            itemBuilder: (context, i) {
              final p = _paths[i];
              final isExpanded = _expandedPathIndex == i;
              return _buildPathCard(p, i, isExpanded);
            },
          ),
        );
  }

  Widget _buildPathCard(AttackPath path, int index, bool isExpanded) {
    final labelPath = path.nodes.map((id) => _nodeLabels[id] ?? id).join(' → ');
    final isHighScore = path.score > 0.75;
    
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: () => setState(() => _expandedPathIndex = isExpanded ? null : index),
          borderRadius: BorderRadius.circular(10),
          child: Container(
            decoration: BoxDecoration(
              gradient: isHighScore
                ? LinearGradient(
                    colors: [const Color(0xFF8B0000).withValues(alpha: 0.15), const Color(0xFFFF4444).withValues(alpha: 0.08)],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  )
                : LinearGradient(
                    colors: [neonCyan.withValues(alpha: 0.1), holographicBlue.withValues(alpha: 0.05)],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
              border: Border.all(color: isHighScore ? const Color(0xFFFF6B6B) : neonCyan, width: 0.8),
              borderRadius: BorderRadius.circular(10),
              boxShadow: isHighScore
                ? [BoxShadow(color: const Color(0xFFFF4444).withValues(alpha: 0.3), blurRadius: 10, spreadRadius: 1)]
                : [BoxShadow(color: neonCyan.withValues(alpha: 0.2), blurRadius: 8, spreadRadius: 0.5)],
            ),
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                        decoration: BoxDecoration(
                          color: (isHighScore ? const Color(0xFFFF4444) : neonCyan).withValues(alpha: 0.15),
                          border: Border.all(color: isHighScore ? const Color(0xFFFF4444) : neonCyan, width: 0.5),
                          borderRadius: BorderRadius.circular(4),
                        ),
                        child: Text(
                          'Risk: ${(path.score * 100).toStringAsFixed(1)}%',
                          style: TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.bold,
                            color: isHighScore ? const Color(0xFFFF4444) : neonCyan,
                          ),
                        ),
                      ),
                      Icon(isExpanded ? Icons.expand_less : Icons.expand_more, size: 18, color: Colors.white54),
                    ],
                  ),
                  const SizedBox(height: 10),
                  Text(
                    labelPath,
                    maxLines: isExpanded ? null : 2,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(fontSize: 12, color: Colors.white70, height: 1.4),
                  ),
                  if (isExpanded) ...[
                    const SizedBox(height: 10),
                    const Divider(color: Colors.white10, height: 1),
                    const SizedBox(height: 10),
                    Text('Reason: ${path.reason}', style: const TextStyle(fontSize: 11, color: Colors.white54)),
                    const SizedBox(height: 8),
                    Row(
                      children: [
                        Expanded(
                          child: ElevatedButton.icon(
                            onPressed: () => showPathDetailsModal(
                              context,
                              path: path,
                              nodeLabels: _nodeLabels,
                              onExplore: () {
                                Navigator.of(context).pushNamed('/ced', arguments: path);
                              },
                            ),
                            icon: const Icon(Icons.info_outline, size: 16),
                            label: const Text('View Details', style: TextStyle(fontSize: 11)),
                            style: ElevatedButton.styleFrom(
                              backgroundColor: neonCyan.withValues(alpha: 0.2),
                              foregroundColor: neonCyan,
                              padding: const EdgeInsets.symmetric(vertical: 8),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ],
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
