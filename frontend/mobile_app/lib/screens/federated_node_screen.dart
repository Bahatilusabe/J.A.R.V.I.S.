import 'package:flutter/material.dart';
import '../services/http_client.dart';
import '../services/federation_service.dart';
import 'node_detail_screen.dart';

class FederatedNodeScreen extends StatefulWidget {
  final AuthenticatedClient client;
  final FederationService? serviceOverride;

  const FederatedNodeScreen({super.key, required this.client, this.serviceOverride});

  @override
  State<FederatedNodeScreen> createState() => _FederatedNodeScreenState();
}

class _FederatedNodeScreenState extends State<FederatedNodeScreen> {
  late final FederationService service;
  Map<String, dynamic>? _status;
  Map<String, dynamic>? _models;
  // ignore: unused_field
  bool _loading = false;
  bool _actionInProgress = false;

  @override
  void initState() {
    super.initState();
    service = widget.serviceOverride ?? FederationService(widget.client);
    _refresh();
  }

  Future<void> _refresh() async {
    setState(() => _loading = true);
    try {
      final s = await service.getStatus();
      final m = await service.getModels();
      setState(() {
        _status = s;
        _models = m;
      });
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Federated fetch failed: $e')));
    } finally {
      setState(() => _loading = false);
    }
  }

  Future<void> _triggerNodeSync(String nodeId) async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Confirm Sync'),
        content: Text('Trigger sync for node $nodeId?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Sync'),
          ),
        ],
      ),
    );

    if (confirm != true) return;

    setState(() => _actionInProgress = true);
    try {
      final result = await service.triggerNodeSync(nodeId);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Sync triggered: ${result['message'] ?? "Success"}')),
        );
        _refresh();
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Sync failed: $e'), backgroundColor: Colors.red),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _actionInProgress = false);
      }
    }
  }

  Future<void> _triggerAggregate() async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Confirm Aggregation'),
        content: const Text('Trigger global model aggregation?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Aggregate'),
          ),
        ],
      ),
    );

    if (confirm != true) return;

    setState(() => _actionInProgress = true);
    try {
      final result = await service.triggerAggregate();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Aggregation completed: ${result['message'] ?? "Success"}')),
        );
        _refresh();
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Aggregation failed: $e'), backgroundColor: Colors.red),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _actionInProgress = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final nodes = (_status != null ? List<dynamic>.from(_status!['nodes'] ?? []) : []).cast<Map<String, dynamic>>();
    final models = (_models != null ? List<dynamic>.from(_models!['models'] ?? []) : []).cast<Map<String, dynamic>>();
    final latestModel = _models != null ? _models!['latest_model'] : null;
    final networkHealth = _status != null ? (_status!['network_health'] ?? 0.0) as double : 0.0;
    final networkTrust = _status != null ? (_status!['network_trust'] ?? 0.0) as double : 0.0;

    return Scaffold(
      appBar: AppBar(title: const Text('Federated XDR Nodes')),
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
                    const Text('Network Health', style: TextStyle(fontWeight: FontWeight.bold)),
                    const SizedBox(height: 6),
                    Text('${(networkHealth * 100).toStringAsFixed(1)}%', style: const TextStyle(fontSize: 18, color: Colors.greenAccent)),
                  ]),
                ),
                Expanded(
                  child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    const Text('Network Trust', style: TextStyle(fontWeight: FontWeight.bold)),
                    const SizedBox(height: 6),
                    Text('${(networkTrust * 100).toStringAsFixed(1)}%', style: const TextStyle(fontSize: 18, color: Colors.blueAccent)),
                  ]),
                ),
              ]),
            ),
          ),
          const SizedBox(height: 12),
          const Text('Node List', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
          const SizedBox(height: 8),
          if (nodes.isEmpty)
            const Text('No nodes')
          else
            Column(
              children: nodes.map<Widget>((node) {
                final nodeId = node['id'] ?? 'unknown';
                final country = node['country'] ?? 'unknown';
                final tag = node['tag'] ?? '';
                final health = (node['sync_health'] ?? 0.0) as double;
                final trust = (node['trust_score'] ?? 0.0) as double;
                final lastLedger = node['last_ledger'] ?? '-';
                return Card(
                  margin: const EdgeInsets.symmetric(vertical: 6),
                  child: Column(
                    children: [
                      ListTile(
                        leading: CircleAvatar(child: Text(country.substring(0, 1))),
                        title: Text('$country ($tag)'),
                        subtitle: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                          Text('Health: ${(health * 100).toStringAsFixed(0)}%'),
                          Text('Trust: ${(trust * 100).toStringAsFixed(0)}%'),
                          Text('Ledger: $lastLedger'),
                        ]),
                        trailing: const Icon(Icons.arrow_forward_ios, size: 16),
                        onTap: () {
                          Navigator.of(context).push(
                            MaterialPageRoute(
                              builder: (context) => NodeDetailScreen(
                                nodeId: nodeId,
                                federationService: service,
                              ),
                            ),
                          );
                        },
                      ),
                      Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                        child: SizedBox(
                          width: double.infinity,
                          child: ElevatedButton.icon(
                            onPressed: _actionInProgress ? null : () => _triggerNodeSync(nodeId),
                            icon: const Icon(Icons.sync, size: 16),
                            label: const Text('Sync'),
                          ),
                        ),
                      ),
                    ],
                  ),
                );
              }).toList(),
            ),
          const SizedBox(height: 20),
          const Text('Model Provenance', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
          const SizedBox(height: 8),
          if (latestModel != null) ...[
            Card(
              child: Padding(
                padding: const EdgeInsets.all(12.0),
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  const Text('Latest Model', style: TextStyle(fontWeight: FontWeight.bold)),
                  const SizedBox(height: 6),
                  Text('Version: ${latestModel['version'] ?? '-'}'),
                  Text('Node: ${latestModel['node_id'] ?? '-'}'),
                  Text('Status: ${latestModel['status'] ?? '-'}'),
                  Text('Created: ${latestModel['created_at'] ?? '-'}'),
                  const SizedBox(height: 12),
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton.icon(
                      onPressed: _actionInProgress ? null : _triggerAggregate,
                      icon: const Icon(Icons.merge, size: 16),
                      label: const Text('Trigger Aggregation'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.purpleAccent,
                      ),
                    ),
                  ),
                ]),
              ),
            ),
            const SizedBox(height: 12),
          ],
          if (models.isEmpty)
            const Text('No models')
          else
            Column(
              children: models.take(5).map<Widget>((model) {
                return ListTile(
                  dense: true,
                  title: Text('${model['id']} (v${model['version']})'),
                  subtitle: Text('${model['status']} @ ${model['node_id']}'),
                );
              }).toList(),
            ),
        ]),
      ),
    );
  }
}
