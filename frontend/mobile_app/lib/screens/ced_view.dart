import 'dart:convert';

import 'package:flutter/material.dart';
import '../config.dart';
import '../services/http_client.dart';
import '../theme.dart';
import '../utils/modern_effects.dart';
import 'package:http/http.dart' as http;

class CedView extends StatefulWidget {
  /// Accepts route arguments as either:
  /// - String eventId
  /// - Map {'eventId': '...', 'summary': {...}} (optional)
  const CedView({super.key});

  @override
  State<CedView> createState() => _CedViewState();
}

class _CedViewState extends State<CedView> {
  String? _eventId;
  bool _loading = true;
  String? _error;

  // fetched explanation
  String _rootCause = '';
  List<String> _causalChain = [];
  List<String> _interventions = [];

  // chosen intervention(s)
  final Set<int> _selectedInterventions = {};

  // predicted outcome after simulation
  String? _predictedOutcome;
  bool _simulating = false;

  final http.Client _client = AuthenticatedClient();

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (_eventId != null) return; // already initialized
    final args = ModalRoute.of(context)?.settings.arguments;
    if (args is String) _eventId = args;
    if (args is Map && args['eventId'] is String) _eventId = args['eventId'] as String;
    if (_eventId == null) {
      setState(() {
        _loading = false;
        _error = 'No event id provided';
      });
      return;
    }

    _fetchExplain();
  }

  Future<void> _fetchExplain() async {
    setState(() { _loading = true; _error = null; });
    try {
      final uri = Uri.parse('${Config.baseUrl}/ced/explain?event=${Uri.encodeComponent(_eventId!)}');
      final res = await _client.get(uri);
      if (res.statusCode != 200) throw Exception('Failed to fetch explanation (${res.statusCode})');
      final Map<String, dynamic> body = json.decode(res.body) as Map<String, dynamic>;
      setState(() {
        _rootCause = (body['root_cause'] ?? body['cause'] ?? '').toString();
        final chain = body['causal_chain'] ?? body['chain'] ?? body['path'] ?? [];
        _causalChain = (chain is List) ? chain.map((e) => e.toString()).toList() : [chain.toString()];
        final mi = body['minimal_intervention'] ?? body['intervention'] ?? body['recommendations'] ?? [];
        _interventions = (mi is List) ? mi.map((e) => e.toString()).toList() : [mi.toString()];
        _predictedOutcome = (body['predicted_outcome'] ?? body['outcome'])?.toString();
        _loading = false;
      });
    } catch (e) {
      setState(() { _loading = false; _error = e.toString(); });
    }
  }

  Future<void> _simulate() async {
    if (_eventId == null) return;
    if (_selectedInterventions.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Select at least one intervention')));
      return;
    }
    setState(() { _simulating = true; _predictedOutcome = null; });
    try {
      final chosen = _selectedInterventions.map((i) => _interventions[i]).toList();
      final uri = Uri.parse('${Config.baseUrl}/ced/simulate');
      final res = await _client.post(uri, headers: {'Content-Type': 'application/json'}, body: json.encode({
        'event_id': _eventId,
        'interventions': chosen,
      }));
      if (res.statusCode != 200) throw Exception('Simulation failed (${res.statusCode})');
      final Map<String, dynamic> body = json.decode(res.body) as Map<String, dynamic>;
      setState(() {
        _predictedOutcome = body['predicted_outcome']?.toString() ?? body['outcome']?.toString() ?? 'No outcome provided';
        _simulating = false;
      });
    } catch (e) {
      setState(() { _simulating = false; _predictedOutcome = 'Simulation error: $e'; });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('CED — Explainability'),
        elevation: 0,
      ),
      body: Padding(
        padding: const EdgeInsets.all(12),
        child: _loading
            ? const Center(child: CircularProgressIndicator(strokeWidth: 2))
            : _error != null
                ? Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.error_outline, size: 32, color: Colors.white54),
                        const SizedBox(height: 12),
                        Text(
                          'Error: $_error',
                          textAlign: TextAlign.center,
                          style: const TextStyle(color: Colors.white70),
                        ),
                      ],
                    ),
                  )
                : SingleChildScrollView(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        // Root cause
                        _buildSectionHeader('Root Cause', Icons.trending_down),
                        const SizedBox(height: 10),
                        Container(
                          decoration: ModernEffects.glassCard(hasGlow: false),
                          padding: const EdgeInsets.all(12),
                          child: Text(
                            _rootCause.isNotEmpty ? _rootCause : 'No root cause identified',
                            style: const TextStyle(
                              fontSize: 13,
                              color: Colors.white70,
                              height: 1.5,
                            ),
                          ),
                        ),
                        const SizedBox(height: 20),

                        // Causal chain
                        _buildSectionHeader('Causal Chain', Icons.schema),
                        const SizedBox(height: 10),
                        if (_causalChain.isEmpty)
                          Container(
                            decoration: ModernEffects.glassCard(hasGlow: false),
                            padding: const EdgeInsets.all(12),
                            child: const Center(
                              child: Text(
                                'No causal chain available',
                                style: TextStyle(color: Colors.white54),
                              ),
                            ),
                          )
                        else
                          ListView.builder(
                            shrinkWrap: true,
                            physics: const NeverScrollableScrollPhysics(),
                            itemCount: _causalChain.length,
                            itemBuilder: (context, i) => Padding(
                              padding: const EdgeInsets.only(bottom: 8),
                              child: Container(
                                decoration: ModernEffects.glassCard(hasGlow: false),
                                padding: const EdgeInsets.all(12),
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
                                        boxShadow: ModernEffects.neonGlowShadows(color: neonCyan),
                                      ),
                                      child: Center(
                                        child: Text(
                                          '${i + 1}',
                                          style: const TextStyle(
                                            color: Colors.white,
                                            fontWeight: FontWeight.bold,
                                            fontSize: 11,
                                          ),
                                        ),
                                      ),
                                    ),
                                    const SizedBox(width: 12),
                                    Expanded(
                                      child: Text(
                                        _causalChain[i],
                                        style: const TextStyle(
                                          fontSize: 12,
                                          color: Colors.white70,
                                        ),
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            ),
                          ),
                        const SizedBox(height: 20),

                        // Interventions
                        _buildSectionHeader('Recommended Interventions', Icons.build),
                        const SizedBox(height: 10),
                        if (_interventions.isEmpty)
                          Container(
                            decoration: ModernEffects.glassCard(hasGlow: false),
                            padding: const EdgeInsets.all(12),
                            child: const Center(
                              child: Text(
                                'No recommended interventions',
                                style: TextStyle(color: Colors.white54),
                              ),
                            ),
                          )
                        else
                          Container(
                            decoration: ModernEffects.glassCard(hasGlow: false),
                            padding: const EdgeInsets.all(12),
                            child: Wrap(
                              spacing: 8,
                              runSpacing: 8,
                              children: [
                                for (var i = 0; i < _interventions.length; i++)
                                  _buildInterventionChip(i),
                              ],
                            ),
                          ),
                        const SizedBox(height: 20),

                        // Simulate button
                        SizedBox(
                          width: double.infinity,
                          child: Container(
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
                                onTap: _simulating ? null : _simulate,
                                borderRadius: BorderRadius.circular(8),
                                child: Padding(
                                  padding: const EdgeInsets.symmetric(vertical: 12),
                                  child: _simulating
                                      ? const SizedBox(
                                          width: 18,
                                          height: 18,
                                          child: CircularProgressIndicator(strokeWidth: 2),
                                        )
                                      : Row(
                                          mainAxisAlignment: MainAxisAlignment.center,
                                          children: [
                                            const Icon(Icons.play_arrow, color: Colors.white, size: 18),
                                            const SizedBox(width: 8),
                                            const Text(
                                              'Simulate Interventions',
                                              style: TextStyle(
                                                color: Colors.white,
                                                fontWeight: FontWeight.w600,
                                                fontSize: 13,
                                              ),
                                            ),
                                          ],
                                        ),
                                ),
                              ),
                            ),
                          ),
                        ),
                        const SizedBox(height: 20),

                        // Predicted outcome
                        _buildSectionHeader('Predicted Outcome', Icons.visibility),
                        const SizedBox(height: 10),
                        Container(
                          decoration: ModernEffects.glassCard(hasGlow: _predictedOutcome != null),
                          padding: const EdgeInsets.all(12),
                          child: _predictedOutcome != null
                              ? Text(
                                  _predictedOutcome!,
                                  style: const TextStyle(
                                    fontSize: 13,
                                    color: Colors.white70,
                                    height: 1.5,
                                  ),
                                )
                              : Row(
                                  children: [
                                    Icon(Icons.info_outline, size: 16, color: Colors.white54),
                                    const SizedBox(width: 8),
                                    const Expanded(
                                      child: Text(
                                        'Run simulation to see predicted outcome',
                                        style: TextStyle(
                                          fontSize: 12,
                                          color: Colors.white54,
                                          fontStyle: FontStyle.italic,
                                        ),
                                      ),
                                    ),
                                  ],
                                ),
                        ),
                        const SizedBox(height: 20),
                      ],
                    ),
                  ),
      ),
    );
  }

  Widget _buildSectionHeader(String title, IconData icon) {
    return Row(
      children: [
        Icon(icon, size: 18, color: neonCyan),
        const SizedBox(width: 8),
        Text(
          title,
          style: Theme.of(context).textTheme.titleMedium?.copyWith(
            color: Colors.white,
          ),
        ),
      ],
    );
  }

  Widget _buildInterventionChip(int idx) {
    final isSelected = _selectedInterventions.contains(idx);
    return GestureDetector(
      onTap: () {
        setState(() {
          if (isSelected) {
            _selectedInterventions.remove(idx);
          } else {
            _selectedInterventions.add(idx);
          }
        });
      },
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        decoration: BoxDecoration(
          color: isSelected ? neonCyan.withValues(alpha: 0.2) : Colors.transparent,
          border: Border.all(
            color: isSelected ? neonCyan : Colors.white24,
            width: 1,
          ),
          borderRadius: BorderRadius.circular(16),
          boxShadow: isSelected ? ModernEffects.neonGlowShadows(color: neonCyan) : [],
        ),
        child: Text(
          _interventions[idx],
          style: TextStyle(
            fontSize: 11,
            color: isSelected ? neonCyan : Colors.white70,
            fontWeight: isSelected ? FontWeight.w600 : FontWeight.w400,
          ),
        ),
      ),
    );
  }
}
