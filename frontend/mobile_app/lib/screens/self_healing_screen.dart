import 'package:flutter/material.dart';
import '../services/http_client.dart';
import '../services/self_healing_service.dart';

class SelfHealingScreen extends StatefulWidget {
  final AuthenticatedClient client;
  const SelfHealingScreen({super.key, required this.client});

  @override
  State<SelfHealingScreen> createState() => _SelfHealingScreenState();
}

class _SelfHealingScreenState extends State<SelfHealingScreen> {
  late final SelfHealingService service;
  Map<String, dynamic>? _metrics;
  Map<String, dynamic>? _actions;
  // ignore: unused_field
  bool _loading = false;

  @override
  void initState() {
    super.initState();
    service = SelfHealingService(widget.client);
    _refresh();
  }

  Future<void> _refresh() async {
    setState(() => _loading = true);
    try {
      final m = await service.getMetrics();
      final a = await service.getActions();
      setState(() {
        _metrics = m;
        _actions = a;
      });
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Self-healing fetch failed: $e')));
    } finally {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final confidence = _metrics != null ? (_metrics!['confidence'] ?? 0.0) as double : 0.0;
    // ignore: unused_local_variable
    final perAgent = _metrics != null ? Map<String, dynamic>.from(_metrics!['per_agent'] ?? {}) : {};
    final timeline = _metrics != null ? List.from(_metrics!['timeline'] ?? []) : [];
    final lastAction = _actions != null ? _actions!['last_action'] : null;

    return Scaffold(
      appBar: AppBar(title: const Text('Self-Healing Engine')),
      body: RefreshIndicator(
        onRefresh: _refresh,
        child: ListView(padding: const EdgeInsets.all(16), children: [
          const SizedBox(height: 8),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(12.0),
              child: Row(children: [
                Expanded(
                  child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    const Text('Current self-healing status', style: TextStyle(fontWeight: FontWeight.bold)),
                    const SizedBox(height: 6),
                    Text('Confidence: ${(confidence * 100).toStringAsFixed(1)}%', style: const TextStyle(fontSize: 18)),
                  ]),
                ),
                ElevatedButton.icon(onPressed: _refresh, icon: const Icon(Icons.refresh), label: const Text('Refresh'))
              ]),
            ),
          ),
          const SizedBox(height: 12),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(12.0),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                const Text('Last action taken', style: TextStyle(fontWeight: FontWeight.bold)),
                const SizedBox(height: 8),
                if (lastAction != null) ...[
                  Text('Action: ${lastAction['action']}'),
                  Text('Snapshot: ${lastAction['snapshot_id'] ?? '-'}'),
                  Text('Time: ${lastAction['created_at'] ?? '-'}'),
                ] else
                  const Text('No recent actions'),
              ]),
            ),
          ),
          const SizedBox(height: 12),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(12.0),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                const Text('Mini policy timeline', style: TextStyle(fontWeight: FontWeight.bold)),
                const SizedBox(height: 8),
                if (timeline.isEmpty) const Text('No timeline available') else
                  Column(
                    children: timeline.take(8).map<Widget>((t) {
                      final step = t['step'];
                      final actions = t['actions'] as Map<String, dynamic>? ?? {};
                      final rewards = t['rewards'] as Map<String, dynamic>? ?? {};
                      return ListTile(
                        dense: true,
                        leading: CircleAvatar(radius: 16, child: Text(step.toString())),
                        title: Text('Actions: ${actions.values.join(', ')}'),
                        subtitle: Text('Rewards: ${rewards.values.join(', ')}'),
                      );
                    }).toList(),
                  ),
              ]),
            ),
          ),
          const SizedBox(height: 12),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(12.0),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                const Text('Recent actions', style: TextStyle(fontWeight: FontWeight.bold)),
                const SizedBox(height: 8),
                if (_actions == null) const Text('No actions loaded') else
                  (_actions!['actions'] as List<dynamic>).isEmpty
                      ? const Text('No recent actions')
                      : Column(
                          children: (_actions!['actions'] as List<dynamic>).take(10).map<Widget>((a) {
                            return ListTile(
                              dense: true,
                              title: Text(a['action'] ?? 'action'),
                              subtitle: Text('${a['snapshot_id'] ?? ''} @ ${a['created_at'] ?? ''}'),
                            );
                          }).toList(),
                        )
              ]),
            ),
          ),
        ]),
      ),
    );
  }
}
