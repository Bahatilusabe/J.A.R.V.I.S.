import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'services/ws_client.dart';
import 'services/dashboard_service.dart';
import 'services/auth_service.dart';
import 'config.dart';
import 'theme.dart';
import 'utils/modern_effects.dart';

class RealTimeFeed extends StatefulWidget {
  final List<Map<String, dynamic>>? initialAlerts;
  final dynamic wsClient; // allow injection of a test ws client

  const RealTimeFeed({super.key, this.initialAlerts, this.wsClient});

  @override
  State<RealTimeFeed> createState() => _RealTimeFeedState();
}

class _RealTimeFeedState extends State<RealTimeFeed> {
  WsClient? _ws;
  final List<Map<String, dynamic>> _alerts = [];
  StreamSubscription<String>? _sub;

  @override
  void initState() {
    super.initState();
    _initFeed();
  }

  Future<void> _initFeed() async {
    // load history (unless initial provided)
    if (widget.initialAlerts != null) {
      setState(() => _alerts.addAll(widget.initialAlerts!.reversed));
    } else {
      debugPrint('[feed] fetching history start');
      final t0 = DateTime.now();
      final history = await DashboardService.getTelemetryHistory(limit: 50);
      debugPrint('[feed] fetching history took ${DateTime.now().difference(t0).inMilliseconds}ms');
      setState(() => _alerts.addAll(history.reversed)); // oldest first then we'll prepend live
    }

    // setup websocket (unless wsClient injected)
    if (widget.wsClient != null) {
      // assume wsClient exposes stream
      _sub = widget.wsClient.stream.listen(_onWs, onError: (e) => debugPrint('ws feed error $e'));
      return;
    }

  final token = await AuthService.getStoredToken();
  final url = Config.wsPath('/ws/telemetry');
  debugPrint('[feed] setting up ws url=$url');
  final ws = WsClient(url, token: token);
  _ws = ws;
  ws.connect();
  debugPrint('[feed] ws connect called');
  _sub = ws.stream.listen((m) {
    debugPrint('[feed] ws first message (raw)');
    _onWs(m);
  }, onError: (e) => debugPrint('ws feed error $e'));
  }

  void _onWs(String msg) {
    try {
      final data = json.decode(msg);
      if (data is Map<String, dynamic>) {
        setState(() {
          _alerts.insert(0, data);
          if (_alerts.length > 200) _alerts.removeLast();
        });
      }
    } catch (e) {
      debugPrint('ws parse fallback: $e');
      // fallback: try to create a simple alert from string
      setState(() {
        _alerts.insert(0, {'id': DateTime.now().millisecondsSinceEpoch.toString(), 'message': msg, 'severity': 'info', 'timestamp': DateTime.now().toIso8601String()});
        if (_alerts.length > 200) _alerts.removeLast();
      });
    }
  }

  @override
  void dispose() {
    _sub?.cancel();
    _ws?.dispose();
    super.dispose();
  }

  Color _severityColor(String s) {
    switch (s.toLowerCase()) {
      case 'critical':
        return neonRed;
      case 'high':
        return neonOrange;
      case 'medium':
        return quantumGreen;
      case 'low':
        return holographicBlue;
      default:
        return Colors.white70;
    }
  }

  Widget _buildCard(Map<String, dynamic> a) {
    final severity = (a['severity'] ?? 'info').toString();
    final asset = (a['asset'] ?? a['asset_name'] ?? a['asset_id'] ?? 'Unknown').toString();
    final desc = (a['description'] ?? a['message'] ?? '').toString();
    final prob = (a['pasm_probability'] ?? a['probability'] ?? a['score'] ?? 0.0);
    final ts = (a['timestamp'] ?? a['time'] ?? DateTime.now().toIso8601String()).toString();
    final severityColor = _severityColor(severity);

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 12),
      child: GestureDetector(
        onTap: () => _openIncident(a),
        child: Container(
          decoration: ModernEffects.glassCard(hasGlow: severity.toLowerCase() == 'critical'),
          child: Padding(
            padding: const EdgeInsets.all(12.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Header with severity and time
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(vertical: 4, horizontal: 8),
                      decoration: BoxDecoration(
                        color: severityColor.withValues(alpha: 0.2),
                        border: Border.all(color: severityColor, width: 0.5),
                        borderRadius: BorderRadius.circular(4),
                        boxShadow: ModernEffects.neonGlowShadows(color: severityColor),
                      ),
                      child: Text(
                        severity.toUpperCase(),
                        style: TextStyle(
                          color: severityColor,
                          fontWeight: FontWeight.bold,
                          fontSize: 10,
                        ),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        asset,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(
                          fontWeight: FontWeight.w600,
                          fontSize: 13,
                          color: Colors.white,
                        ),
                      ),
                    ),
                    Text(
                      _formatTime(ts),
                      style: const TextStyle(
                        fontSize: 11,
                        color: Colors.white54,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 10),
                // Description
                if (desc.isNotEmpty)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 10),
                    child: Text(
                      desc,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        fontSize: 12,
                        color: Colors.white70,
                        height: 1.4,
                      ),
                    ),
                  ),
                // Footer with probability and action button
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Expanded(
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
                        decoration: BoxDecoration(
                          color: Colors.white.withValues(alpha: 0.05),
                          border: Border.all(color: Colors.white24, width: 0.5),
                          borderRadius: BorderRadius.circular(4),
                        ),
                        child: Text(
                          'PASM: ${((prob is num) ? prob * 100 : double.tryParse(prob.toString()) ?? 0.0).toStringAsFixed(0)}%',
                          style: const TextStyle(
                            fontWeight: FontWeight.w600,
                            fontSize: 11,
                            color: Colors.white70,
                          ),
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
                        border: Border.all(color: neonCyan.withValues(alpha: 0.5), width: 0.5),
                        borderRadius: BorderRadius.circular(6),
                        boxShadow: ModernEffects.neonGlowShadows(color: neonCyan),
                      ),
                      child: Material(
                        color: Colors.transparent,
                        child: InkWell(
                          onTap: () => _openIncident(a),
                          borderRadius: BorderRadius.circular(6),
                          child: const Padding(
                            padding: EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                            child: Text(
                              'View',
                              style: TextStyle(
                                fontSize: 11,
                                fontWeight: FontWeight.w600,
                                color: Colors.white,
                              ),
                            ),
                          ),
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

  String _formatTime(String ts) {
    try {
      final d = DateTime.parse(ts).toLocal();
      return '${d.hour.toString().padLeft(2, '0')}:${d.minute.toString().padLeft(2, '0')}';
    } catch (_) {
      return ts;
    }
  }

  void _openIncident(Map<String, dynamic> a) {
    final id = a['id']?.toString() ?? a['incident_id']?.toString();
    if (id != null && id.isNotEmpty) {
      Navigator.of(context).pushNamed('/incident', arguments: id);
    } else {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('No incident id found.')));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Real-Time Threat Feed')),
      body: RefreshIndicator(
        onRefresh: () async {
          final hist = await DashboardService.getTelemetryHistory(limit: 50);
          setState(() {
            _alerts.clear();
            _alerts.addAll(hist.reversed);
          });
        },
        child: ListView.builder(
          padding: const EdgeInsets.only(bottom: 24, top: 8),
          itemCount: _alerts.length,
          itemBuilder: (context, idx) => _buildCard(_alerts[idx]),
        ),
      ),
    );
  }
}
