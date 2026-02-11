import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:path_provider/path_provider.dart';
import 'package:share_plus/share_plus.dart';
import 'package:http/http.dart' as http;
import '../config.dart';
import '../services/http_client.dart';
import '../utils/ip_utils.dart' as ip_utils;

class IncidentDetailScreen extends StatefulWidget {
  final String incidentId;
  const IncidentDetailScreen({required this.incidentId, super.key});

  @override
  State<IncidentDetailScreen> createState() => _IncidentDetailScreenState();
}

class _IncidentDetailScreenState extends State<IncidentDetailScreen> {
  late Future<Map<String, dynamic>> _incidentFuture;
  late Future<List<dynamic>> _pasmFuture;
  late Future<Map<String, dynamic>> _cedFuture;
  final http.Client _client = AuthenticatedClient();
  bool _actionLoading = false;
  String? _actionResult;
  List<bool> _visibleEvents = [];
  Map<String, dynamic>? _incidentData;

  @override
  void initState() {
    super.initState();
    _incidentFuture = _fetchIncident();
    _pasmFuture = _fetchPasm();
    _cedFuture = _fetchCed();
    // When incident fetch completes, animate timeline entries in
    _incidentFuture.then((incident) {
      _incidentData = incident as Map<String, dynamic>?;
      final timeline = incident['timeline'];
      if (timeline is List) {
        _visibleEvents = List<bool>.filled(timeline.length, false);
        for (var i = 0; i < timeline.length; i++) {
          Future.delayed(Duration(milliseconds: 120 * i), () {
            if (mounted) {
              setState(() {
                _visibleEvents[i] = true;
              });
            }
          });
        }
      }
    }).catchError((_) {});
  }

  Future<Map<String, dynamic>> _fetchIncident() async {
    final uri = Uri.parse('${Config.baseUrl}/incident/${widget.incidentId}');
    final res = await _client.get(uri);
    if (res.statusCode != 200) throw Exception('Failed to load incident');
    return json.decode(res.body) as Map<String, dynamic>;
  }

  Future<List<dynamic>> _fetchPasm() async {
    final uri = Uri.parse('${Config.baseUrl}/pasm/predict?incident=${widget.incidentId}');
    final res = await _client.get(uri);
    if (res.statusCode != 200) return [];
    return json.decode(res.body) as List<dynamic>;
  }

  Future<Map<String, dynamic>> _fetchCed() async {
    final uri = Uri.parse('${Config.baseUrl}/ced/explain?incident=${widget.incidentId}');
    final res = await _client.get(uri);
    if (res.statusCode != 200) return {};
    return json.decode(res.body) as Map<String, dynamic>;
  }

  Future<void> _enforceAction(String action) async {
    setState(() { _actionLoading = true; _actionResult = null; });
    final uri = Uri.parse('${Config.baseUrl}/policy/enforce');
    final body = <String, dynamic>{
      'incident_id': widget.incidentId,
      'action': action,
    };
    final res = await _client.post(uri, body: json.encode(body), headers: {'Content-Type': 'application/json'});
    setState(() {
      _actionLoading = false;
      _actionResult = res.statusCode == 200 ? 'Action succeeded' : 'Action failed: ${res.body}';
    });
    if (_actionResult != null) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(_actionResult!)));
    }
  }

  Future<void> _copyCed(Map<String, dynamic> ced) async {
    final text = ced['explanation']?.toString() ?? '';
    await Clipboard.setData(ClipboardData(text: text));
    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('CED copied to clipboard')));
  }

  Future<void> _exportTimelineCsv(List<dynamic> events) async {
    // Simple CSV: time,message
    final sb = StringBuffer();
    sb.writeln('time,message');
    for (final e in events) {
      String time = '';
      String msg = '';
      if (e is Map) {
        time = (e['time'] ?? e['timestamp'] ?? '').toString();
        msg = (e['message'] ?? e['description'] ?? e.toString()).toString().replaceAll('\n', ' ');
      } else {
        msg = e.toString().replaceAll('\n', ' ');
      }
      sb.writeln('"$time","${msg.replaceAll('"', '""')}"');
    }
    final csvText = sb.toString();

    try {
      // Attempt to write to a temporary file and share it using platform share dialog
      final tmpDir = await getTemporaryDirectory();
      final fileName = 'incident_${widget.incidentId}_timeline.csv';
      final file = File('${tmpDir.path}/$fileName');
      await file.writeAsString(csvText, flush: true);

      // Use share_plus to open native share dialog with the file
      await Share.shareXFiles([XFile(file.path)], text: 'Incident timeline CSV for ${widget.incidentId}');
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Timeline CSV prepared and share sheet opened')));
    } catch (e) {
      // Fallback to clipboard if file writing or share fails
      await Clipboard.setData(ClipboardData(text: csvText));
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Timeline CSV copied to clipboard')));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Incident ${widget.incidentId}'), elevation: 4),
      body: FutureBuilder<Map<String, dynamic>>(
        future: _incidentFuture,
        builder: (context, snap) {
          if (snap.connectionState != ConnectionState.done) return const Center(child: CircularProgressIndicator());
          if (snap.hasError) return Center(child: Text('Error: ${snap.error}'));
          final incident = snap.data ?? {};
          return SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Header card with asset and severity
                Card(
                  elevation: 2,
                  child: Padding(
                    padding: const EdgeInsets.all(12),
                    child: Row(
                      children: [
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text('Asset', style: Theme.of(context).textTheme.labelSmall),
                              Text(incident['asset'] ?? '-', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
                              const SizedBox(height: 8),
                              if (incident['severity'] != null)
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                  decoration: BoxDecoration(
                                    color: _severityColor(incident['severity']),
                                    borderRadius: BorderRadius.circular(4),
                                  ),
                                  child: Text(incident['severity'].toString().toUpperCase(), style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 12)),
                                ),
                            ],
                          ),
                        ),
                        if (_actionLoading) const SizedBox(width: 40, height: 40, child: CircularProgressIndicator(strokeWidth: 2)),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 16),
                // Action buttons
                const Text('Response Actions', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                const SizedBox(height: 8),
                // Quick Action Command Center: big buttons for rapid response
                const SizedBox(height: 8),
                Card(
                  elevation: 2,
                  child: Padding(
                    padding: const EdgeInsets.all(12),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text('Quick-Action Command Center', style: TextStyle(fontWeight: FontWeight.bold)),
                        const SizedBox(height: 12),
                        Wrap(
                          spacing: 12,
                          runSpacing: 12,
                          children: [
                            _quickActionButton('🟥\nContain Node', 'contain_node', Colors.redAccent),
                            _quickActionButton('🔒\nRe-Attest', 'reattest', Colors.deepPurple),
                            _quickActionButton('🛡\nPatch', 'patch', Colors.teal),
                            _quickActionButton('🚫\nBlock IP', 'block_ip', Colors.orange),
                            _quickActionButton('🎭\nDeception', 'trigger_deception', Colors.indigo),
                            _quickActionButton('♻\nSelf-Heal', 'self_heal', Colors.green),
                          ],
                        ),
                        const SizedBox(height: 12),
                        const Divider(),
                        const SizedBox(height: 8),
                        const Text('Other actions', style: TextStyle(fontWeight: FontWeight.bold)),
                        const SizedBox(height: 8),
                        Wrap(
                          spacing: 8,
                          runSpacing: 8,
                          children: [
                            _buildActionButton('Contain', 'contain'),
                            _buildActionButton('Block IP', 'block_ip'),
                            _buildActionButton('Patch', 'patch'),
                            _buildActionButton('Isolate', 'isolate'),
                            _buildActionButton('Forensics', 'forensics'),
                          ],
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 16),
                // Event timeline
                const Text('Event Timeline', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                const SizedBox(height: 12),
                if (incident['timeline'] is List && (incident['timeline'] as List).isNotEmpty)
                  _buildTimeline(incident['timeline'] as List)
                else
                  const Padding(padding: EdgeInsets.all(8), child: Text('No events recorded')),
                const SizedBox(height: 16),
                // Predicted attack chain
                const Text('Predicted Attack Chain', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                const SizedBox(height: 8),
                FutureBuilder<List<dynamic>>(
                  future: _pasmFuture,
                  builder: (context, snap) {
                    if (snap.connectionState != ConnectionState.done) return const LinearProgressIndicator();
                    final paths = snap.data ?? [];
                    if (paths.isEmpty) return const Padding(padding: EdgeInsets.all(8), child: Text('No predicted paths'));
                    return Card(
                      child: Padding(
                        padding: const EdgeInsets.all(12),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            for (final p in paths.take(3))
                              Padding(
                                padding: const EdgeInsets.only(bottom: 12),
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    ClipRRect(
                                      borderRadius: BorderRadius.circular(4),
                                      child: LinearProgressIndicator(
                                        value: ((p['score'] ?? 0) as num).toDouble(),
                                        minHeight: 6,
                                      ),
                                    ),
                                    const SizedBox(height: 6),
                                    Text((p['nodes'] as List).join(' → '), style: const TextStyle(fontSize: 12)),
                                    Text('Confidence: ${(((p['score'] ?? 0) as num) * 100).toStringAsFixed(1)}%', style: Theme.of(context).textTheme.labelSmall),
                                  ],
                                ),
                              )
                          ],
                        ),
                      ),
                    );
                  },
                ),
                const SizedBox(height: 16),
                // CED causal explanation
                const Text('Causal Explanation (CED)', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                const SizedBox(height: 8),
                FutureBuilder<Map<String, dynamic>>(
                    future: _cedFuture,
                  builder: (context, snap) {
                    if (snap.connectionState != ConnectionState.done) return const LinearProgressIndicator();
                    final ced = snap.data ?? {};
                    if (ced.isEmpty) return const Padding(padding: EdgeInsets.all(8), child: Text('No explanation available'));
                    return Card(
                      color: Colors.blue[50],
                      child: Padding(
                        padding: const EdgeInsets.all(12),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      if (ced['confidence'] != null)
                                        Padding(
                                          padding: const EdgeInsets.only(bottom: 8),
                                          child: Row(
                                            children: [
                                              Text('Confidence: ', style: Theme.of(context).textTheme.labelSmall),
                                              Text('${((ced['confidence'] as num) * 100).toStringAsFixed(1)}%', style: const TextStyle(fontWeight: FontWeight.bold)),
                                            ],
                                          ),
                                        ),
                                      Text(ced['explanation']?.toString() ?? 'No explanation text', style: const TextStyle(fontSize: 13, height: 1.6)),
                                      if (ced['factors'] is List && (ced['factors'] as List).isNotEmpty) ...[
                                        const SizedBox(height: 12),
                                        const Text('Key Contributing Factors:', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12)),
                                        const SizedBox(height: 6),
                                        Wrap(spacing: 6, runSpacing: 6, children: (ced['factors'] as List).take(8).map<Widget>((f) => Chip(label: Text(f.toString(), style: const TextStyle(fontSize: 11)))).toList()),
                                      ]
                                    ],
                                  ),
                                ),
                                Column(
                                  children: [
                                    IconButton(onPressed: () => _copyCed(ced), icon: const Icon(Icons.copy)),
                                    IconButton(onPressed: () => _exportTimelineCsv(incident['timeline'] ?? []), icon: const Icon(Icons.download)),
                                    IconButton(
                                      onPressed: () {
                                        // Open full CED explainability panel for this incident/event
                                        Navigator.of(context).pushNamed('/ced', arguments: widget.incidentId);
                                      },
                                      icon: const Icon(Icons.open_in_new),
                                      tooltip: 'Open CED panel',
                                    ),
                                  ],
                                )
                              ],
                            ),
                          ],
                        ),
                      ),
                    );
                  },
                ),
                const SizedBox(height: 24),
              ],
            ),
          );
        },
      ),
    );
  }

  Color _severityColor(dynamic sev) {
    final s = sev?.toString().toLowerCase() ?? 'unknown';
    switch (s) {
      case 'critical': return Colors.red;
      case 'high': return Colors.deepOrange;
      case 'medium': return Colors.orange;
      case 'low': return Colors.green;
      default: return Colors.blueGrey;
    }
  }

  Widget _buildActionButton(String label, String action) {
    return OutlinedButton(
      onPressed: _actionLoading ? null : () => _confirmAndEnforce(action, label),
      child: SizedBox(
        width: 70,
        child: Text(label, textAlign: TextAlign.center, style: const TextStyle(fontSize: 12)),
      ),
    );
  }

  Widget _quickActionButton(String label, String action, Color color) {
    return ElevatedButton(
      onPressed: _actionLoading ? null : () => _confirmAndEnforce(action, label),
      style: ElevatedButton.styleFrom(
        backgroundColor: color,
        minimumSize: const Size(140, 80),
        padding: const EdgeInsets.all(8),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text(label, textAlign: TextAlign.center, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
        ],
      ),
    );
  }

  Future<void> _confirmAndEnforce(String action, String label) async {
    // For destructive actions (contain, contain_node, block_ip) ask for confirmation.
    final lower = action.toString().toLowerCase();
    final destructive = lower == 'contain' || lower == 'contain_node' || lower == 'block_ip';
    if (!destructive) {
      // quick path for non-destructive actions
      await _enforceAction(action);
      return;
    }

    if (lower == 'block_ip') {
      // Prompt for target IP (prefill from incident telemetry if available)
  final candidates = ip_utils.extractAllIpsFromIncident(_incidentData);
      final controller = TextEditingController(text: candidates.isNotEmpty ? candidates.first : '');

      final ipConfirmed = await showDialog<String?>(
        context: context,
        builder: (ctx) {
          String? error;
          return StatefulBuilder(builder: (ctx2, setState2) {
            return AlertDialog(
              title: const Text('Block IP'),
              content: Column(mainAxisSize: MainAxisSize.min, children: [
                const Text('Enter the IP address to block for this incident:'),
                const SizedBox(height: 8),
                TextField(controller: controller, decoration: InputDecoration(labelText: 'Target IP', errorText: error)),
                const SizedBox(height: 8),
                if (candidates.isNotEmpty) Wrap(spacing: 8, children: candidates.map((c) => ActionChip(label: Text(c), onPressed: () { controller.text = c; setState2((){}); })).toList()),
                const SizedBox(height: 8),
                Row(children: [
                  TextButton.icon(onPressed: () async {
                    final clip = await Clipboard.getData('text/plain');
                    if (clip?.text != null) {
                      controller.text = clip!.text!.trim();
                      setState2(() {});
                    }
                  }, icon: const Icon(Icons.paste), label: const Text('Paste')),
                ])
              ]),
              actions: [
                TextButton(onPressed: () => Navigator.of(ctx2).pop(null), child: const Text('Cancel')),
                ElevatedButton(onPressed: () {
                  final candidateIp = controller.text.trim();
                  if (candidateIp.isEmpty) {
                    setState2(() { error = 'Enter an IP address'; });
                    return;
                  }
                  if (!ip_utils.isValidIp(candidateIp)) {
                    setState2(() { error = 'Invalid IP format'; });
                    return;
                  }
                  Navigator.of(ctx2).pop(candidateIp);
                }, child: const Text('Block')),
              ],
            );
          });
        }
      );

      if (ipConfirmed != null && ipConfirmed.isNotEmpty) {
        // include target_ip in payload
        await _enforceActionWithPayload(action, {'target_ip': ipConfirmed});
      }
      return;
    }

    // Generic destructive confirmation for contain/contain_node
    final confirmed = await showDialog<bool?>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text('Confirm ${label.replaceAll('\n', ' ')}'),
        content: Text('This action is potentially disruptive. Are you sure you want to "$label" for incident ${widget.incidentId}?'),
        actions: [
          TextButton(onPressed: () => Navigator.of(ctx).pop(false), child: const Text('Cancel')),
          ElevatedButton(onPressed: () => Navigator.of(ctx).pop(true), child: const Text('Confirm')),
        ],
      ),
    );

    if (confirmed == true) {
      await _enforceAction(action);
    }
  }

  Future<void> _enforceActionWithPayload(String action, Map<String, dynamic> payload) async {
    setState(() { _actionLoading = true; _actionResult = null; });
    final uri = Uri.parse('${Config.baseUrl}/policy/enforce');
    final body = <String, dynamic>{
      'incident_id': widget.incidentId,
      'action': action,
    };
    body.addAll(payload);
    final res = await _client.post(uri, body: json.encode(body), headers: {'Content-Type': 'application/json'});
    setState(() {
      _actionLoading = false;
      _actionResult = res.statusCode == 200 ? 'Action succeeded' : 'Action failed: ${res.body}';
    });
    if (_actionResult != null) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(_actionResult!)));
    }
  }

  Widget _buildTimeline(List<dynamic> events) {
    return SizedBox(
      height: 200,
      child: ListView.builder(
        itemCount: events.length,
        itemBuilder: (context, i) {
          final e = events[i];
          final isLast = i == events.length - 1;
          final time = e is Map ? (e['time'] ?? e['timestamp'] ?? '') : '';
          final msg = e is Map ? (e['message'] ?? e['description'] ?? e.toString()) : e.toString();
          return Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Column(
                children: [
                  Container(
                    width: 12,
                    height: 12,
                    decoration: BoxDecoration(color: Colors.blue, borderRadius: BorderRadius.circular(6)),
                  ),
                  if (!isLast) Container(width: 2, height: 40, color: Colors.blue),
                ],
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    if (time.toString().isNotEmpty) Text(time.toString(), style: Theme.of(context).textTheme.labelSmall),
                    Text(msg.toString(), style: const TextStyle(fontSize: 13)),
                  ],
                ),
              ),
            ],
          );
        },
      ),
    );
  }
}