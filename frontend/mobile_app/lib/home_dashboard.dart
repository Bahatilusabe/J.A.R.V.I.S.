// home_dashboard_upgrade.dart
// home_dashboard_upgrade.dart
import 'dart:async';
import 'dart:math';
import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'services/ws_client.dart';
import 'services/dashboard_service.dart';
import 'services/auth_service.dart';
import 'config.dart';
// import 'package:url_launcher/url_launcher.dart'; // Disabled for now
import 'theme.dart';
import 'utils/modern_effects.dart';
import 'widgets/pasm_panel.dart';

/// Upgraded Home Dashboard — Cyber Defense Command Room + Holographic accents
/// Drop this file in place of your old HomeDashboard. It reuses your services:
/// - AuthService.getStoredToken()
/// - WsClient(url, token).connect() and .stream
/// - DashboardService.getLatestAlerts(), getPasmTopRisk(), containAsset(), patchAsset(), blockAsset(), explainAlert()
///
/// Note: To enable file-open of the whitepaper, add url_launcher to pubspec.yaml.
/// Also consider adding Lottie/Rive for advanced animations (placeholders exist).

class HomeDashboardUpgrade extends StatefulWidget {
  const HomeDashboardUpgrade({super.key});

  @override
  State<HomeDashboardUpgrade> createState() => _HomeDashboardUpgradeState();
}

class _HomeDashboardUpgradeState extends State<HomeDashboardUpgrade> with TickerProviderStateMixin {
  WsClient? _ws;
  String _systemState = 'Safe';
  double _riskScore = 0.0; // 0.0 - 1.0
  List<Map<String, dynamic>> _alerts = [];
  Map<String, dynamic>? _topRiskAsset;
  DateTime _now = DateTime.now();
  Timer? _clockTimer;
  AnimationController? _orbController;
  AnimationController? _radarController;

  static const whitepaperPath = '/mnt/data/Jarvis Whitepaper.pdf'; // uploaded file path

  @override
  void initState() {
    super.initState();
    _orbController = AnimationController(vsync: this, duration: const Duration(milliseconds: 2800))
      ..repeat();
    _radarController = AnimationController(vsync: this, duration: const Duration(seconds: 6))
      ..repeat();
    if (!kIsWeb) {
      _initWs();
    }
    _refreshAll();
    _clockTimer = Timer.periodic(const Duration(seconds: 1), (_) {
      if (mounted) {
        setState(() => _now = DateTime.now());
      }
    });
  }

  Future<void> _initWs() async {
    try {
      debugPrint('[upgrade] _initWs start');
      final token = await AuthService.getStoredToken();
      final url = Config.wsPath('/ws/system/status');
      _ws = WsClient(url, token: token);
      _ws!.connect();
      _ws!.stream.listen((m) => _onWsMessage(m), onError: (e) {
        debugPrint('[upgrade] ws error: $e');
        // attempt reconnect after delay
        Future.delayed(const Duration(seconds: 4), () {
          if (_ws != null) _ws!.connect();
        });
      });
      debugPrint('[upgrade] websocket init complete');
    } catch (e) {
      debugPrint('[upgrade] websocket init failed: $e');
    }
  }

  void _onWsMessage(String msg) {
    // more robust parsing while keeping it lightweight
    try {
      final m = msg.toLowerCase();
      if (m.contains('under attack')) {
        setState(() => _systemState = 'Under Attack');
      } else if (m.contains('predictive')) {
        setState(() => _systemState = 'Predictive Mode Active');
      } else if (m.contains('safe')) {
        setState(() => _systemState = 'Safe');
      }
      final rMatch = RegExp(r'"risk"\s*:\s*(0(?:\.\d+)?|1(?:\.0+)?)').firstMatch(msg);
      if (rMatch != null) {
        final val = double.tryParse(rMatch.group(1) ?? '0') ?? 0.0;
        setState(() => _riskScore = val.clamp(0.0, 1.0));
      }
      // optional: parse alerts, top asset updates if provided
      final alertMatch = RegExp(r'"alert":\s*({.*?})').firstMatch(msg);
      if (alertMatch != null) {
        // naive parse: delegate to DashboardService.refresh if needed
        _refreshAll();
      }
    } catch (e) {
      debugPrint('[upgrade] ws parse error: $e');
    }
  }

  Future<void> _refreshAll() async {
    try {
      final alerts = await DashboardService.getLatestAlerts();
      final top = await DashboardService.getPasmTopRisk();
      setState(() {
        _alerts = alerts;
        _topRiskAsset = top;
      });
    } catch (e) {
      debugPrint('[upgrade] refreshAll error: $e');
    }
  }

  @override
  void dispose() {
    _ws?.dispose();
    _clockTimer?.cancel();
    _orbController?.dispose();
    _radarController?.dispose();
    super.dispose();
  }

  // --- UI helpers ---

  Color _severityColor(String severity) {
    switch (severity) {
      case 'critical':
        return const Color(0xFFFF3B30);
      case 'high':
        return const Color(0xFFFF9500);
      case 'medium':
        return const Color(0xFFFFCC00);
      case 'low':
      default:
        return const Color(0xFF00E8FF);
    }
  }

  Future<void> _openWhitepaper() async {
    // TODO: Implement whitepaper opening with url_launcher
    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Whitepaper opening not yet implemented.')));
  }

  Future<void> _onQuickAction(String action) async {
    final assetId = _topRiskAsset?['asset_id']?.toString() ?? '';
    bool ok = false;
    try {
      switch (action) {
        case 'contain':
          ok = await DashboardService.containAsset(assetId);
          break;
        case 'patch':
          ok = await DashboardService.patchAsset(assetId);
          break;
        case 'block':
          ok = await DashboardService.blockAsset(assetId);
          break;
        case 'explain':
          final alertId = _alerts.isNotEmpty ? (_alerts.first['id']?.toString() ?? '') : '';
          ok = await DashboardService.explainAlert(alertId);
          break;
      }
    } catch (e) {
      debugPrint('[upgrade] quickAction error: $e');
      ok = false;
    }
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(ok ? 'Action $action queued' : 'Action $action failed')));
    if (ok) await _refreshAll();
  }

  Widget _buildHeader() {
    // Top bar with system state and time - more cinematic look
    return Row(
      children: [
        Expanded(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text('J.A.R.V.I.S. — Command Room', style: TextStyle(color: Colors.cyanAccent.shade100, fontSize: 14, fontWeight: FontWeight.w700)),
            const SizedBox(height: 6),
            Row(children: [
              _systemStateBadge(),
              const SizedBox(width: 12),
              Text('Latency: 18ms', style: TextStyle(color: Colors.white30, fontSize: 12)),
            ]),
          ]),
        ),
        Column(crossAxisAlignment: CrossAxisAlignment.end, children: [
          Text('${_now.hour.toString().padLeft(2, '0')}:${_now.minute.toString().padLeft(2, '0')}', style: const TextStyle(color: Colors.white70)),
          const SizedBox(height: 4),
          Text('Risk ${( _riskScore * 100 ).toStringAsFixed(0)}%', style: TextStyle(color: _riskScore > 0.7 ? Colors.redAccent : Colors.cyanAccent)),
        ]),
      ],
    );
  }

  Widget _systemStateBadge() {
    Color bg;
    switch (_systemState) {
      case 'Under Attack':
        bg = Colors.redAccent;
        break;
      case 'Predictive Mode Active':
        bg = Colors.orangeAccent;
        break;
      default:
        bg = Colors.greenAccent.shade700;
    }
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(color: bg.withOpacity(0.18), borderRadius: BorderRadius.circular(20), border: Border.all(color: bg.withOpacity(0.4))),
      child: Row(children: [
        Icon(Icons.security, color: bg, size: 14),
        const SizedBox(width: 6),
        Text(_systemState, style: TextStyle(color: Colors.white, fontSize: 12)),
      ]),
    );
  }

  // AI Core holographic orb
  Widget _buildAICore() {
    return SizedBox(
      width: 180,
      height: 180,
      child: AnimatedBuilder(
        animation: _orbController!,
        builder: (context, _) {
          return CustomPaint(
            painter: _OrbPainter(progress: _orbController!.value, pulse: _riskScore),
            child: Center(
              child: Column(mainAxisSize: MainAxisSize.min, children: [
                Icon(Icons.memory, size: 36, color: Colors.black87),
                const SizedBox(height: 6),
                Text('AI CORE', style: TextStyle(fontSize: 12, color: Colors.white70, fontWeight: FontWeight.bold)),
                const SizedBox(height: 2),
                Text('${(_riskScore * 100).toStringAsFixed(0)}%', style: const TextStyle(color: Colors.white54, fontSize: 12)),
              ]),
            ),
          );
        },
      ),
    );
  }

  // Radar / heatmap painter
  Widget _buildRadar() {
    return SizedBox(
      width: 340,
      height: 340,
      child: AnimatedBuilder(
        animation: _radarController!,
        builder: (context, child) {
          return CustomPaint(
            painter: _RadarPainter(progress: _radarController!.value, blips: _sampleBlips()),
            child: Container(),
          );
        },
      ),
    );
  }

  // sample blips for UI demo (should be replaced with live telemetry mapping)
  List<_Blip> _sampleBlips() {
    // map _alerts or top risk asset to radar blips if available
    final now = DateTime.now().millisecondsSinceEpoch;
    final random = Random(now);
    return List.generate(6, (i) {
      final angle = (i / 6) * pi * 2 + random.nextDouble() * 0.4;
      final radius = 0.2 + (i / 6) * 0.6;
      final severity = (i % 3 == 0) ? 'critical' : ((i % 2 == 0) ? 'high' : 'medium');
      final strength = severity == 'critical' ? 1.0 : (severity == 'high' ? 0.7 : 0.45);
      return _Blip(angle: angle, distance: radius, strength: strength, label: 'n-${i + 2}');
    });
  }

  Widget _buildActionTiles() {
    final tiles = [
      {'label': 'Contain', 'icon': Icons.shield, 'action': 'contain', 'color': Colors.redAccent},
      {'label': 'Patch', 'icon': Icons.build, 'action': 'patch', 'color': Colors.orangeAccent},
      {'label': 'Block', 'icon': Icons.block, 'action': 'block', 'color': Colors.amber},
      {'label': 'Explain', 'icon': Icons.psychology, 'action': 'explain', 'color': Colors.cyanAccent},
    ];
    return GridView.count(
      crossAxisCount: 2,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      childAspectRatio: 1.3,
      mainAxisSpacing: 10,
      crossAxisSpacing: 10,
      children: tiles.map((t) {
        return GestureDetector(
          onTap: () => _confirmAndExecute(t['label'] as String, t['action'] as String),
          child: _GlassActionTile(
            label: t['label'] as String,
            icon: t['icon'] as IconData,
            color: t['color'] as Color,
          ),
        );
      }).toList(),
    );
  }

  Future<void> _confirmAndExecute(String label, String action) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (c) => AlertDialog(
        backgroundColor: Colors.grey[900],
        title: Text('Confirm $label', style: const TextStyle(color: Colors.white)),
        content: Text('Execute $label on the top-risk asset?', style: const TextStyle(color: Colors.white70)),
        actions: [
          TextButton(onPressed: () => Navigator.of(c).pop(false), child: const Text('Cancel')),
          ElevatedButton(onPressed: () => Navigator.of(c).pop(true), child: const Text('Confirm')),
        ],
      ),
    );
    if (confirmed == true) {
      await _onQuickAction(action);
    }
  }

  Widget _buildAlertsColumn() {
    return AnimatedSwitcher(
      duration: const Duration(milliseconds: 400),
      child: _alerts.isEmpty
          ? const Center(child: Text('No recent alerts', style: TextStyle(color: Colors.white54)))
          : Column(children: _alerts.take(5).map((a) {
              final id = a['id']?.toString() ?? '-';
              final title = a['title']?.toString() ?? a['message']?.toString() ?? 'Alert';
              final severity = a['severity']?.toString() ?? 'low';
              final color = _severityColor(severity);
              return Card(
                color: Colors.black.withOpacity(0.45),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                child: ListTile(
                  leading: Container(width: 10, height: 10, decoration: BoxDecoration(shape: BoxShape.circle, color: color)),
                  title: Text(title, style: const TextStyle(color: Colors.white)),
                  subtitle: Text('id: $id', style: const TextStyle(color: Colors.white54)),
                  trailing: Text(severity.toUpperCase(), style: const TextStyle(color: Colors.white30, fontSize: 12)),
                  onTap: () => Navigator.of(context).pushNamed('/incident', arguments: {'id': id}),
                ),
              );
            }).toList()),
    );
  }

  Widget _buildCEDPreview() {
    return GestureDetector(
      onTap: () => Navigator.of(context).pushNamed('/ced'),
      child: _GlassCard(
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
            const Text('CED Narrative', style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold)),
            Icon(Icons.open_in_new, size: 18, color: Colors.cyanAccent),
          ]),
          const SizedBox(height: 8),
          const Text('AI explains the likely root cause and minimal intervention.', style: TextStyle(color: Colors.white70)),
          const SizedBox(height: 10),
          Container(
            height: 72,
            decoration: BoxDecoration(borderRadius: BorderRadius.circular(8)),
            child: Center(child: Text('Shortest counterfactual: isolate subnet-3 → -62% risk', style: TextStyle(color: Colors.white60))),
          )
        ]),
      ),
    );
  }

  Widget _buildForensicsPreview() {
    return GestureDetector(
      onTap: () => Navigator.of(context).pushNamed('/forensics'),
      child: _GlassCard(
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
            const Text('Forensics Ledger', style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold)),
            Icon(Icons.open_in_new, size: 18, color: Colors.cyanAccent),
          ]),
          const SizedBox(height: 8),
          const Text('Immutable event log & signed reports', style: TextStyle(color: Colors.white70)),
          const SizedBox(height: 10),
          Row(children: [
            Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: const [
              Text('Last: workstation-42 (Malware)', style: TextStyle(fontWeight: FontWeight.w600)),
              SizedBox(height: 4),
              Text('Severity: High • Signed', style: TextStyle(color: Colors.white60, fontSize: 12)),
            ])),
            Icon(Icons.chevron_right, color: Colors.white24)
          ])
        ]),
      ),
    );
  }

  // Main layout with two columns: left telemetry & controls, right radar & AI core
  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      backgroundColor: const Color(0xFF020617),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        title: _buildHeader(),
        actions: [
          IconButton(onPressed: () => _openWhitepaper(), icon: const Icon(Icons.picture_as_pdf)),
          IconButton(onPressed: () async { await AuthService.clearToken(); Navigator.of(context).pushReplacementNamed('/login'); }, icon: const Icon(Icons.logout)),
        ],
      ),
      drawer: _buildDrawer(),
      body: RefreshIndicator(
        onRefresh: _refreshAll,
        color: Colors.cyanAccent,
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(14),
          physics: const AlwaysScrollableScrollPhysics(),
          child: Column(
            children: [
              // Upper row: Left (Alerts + Actions), Right (Radar + AI core)
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Left column
                  Expanded(
                    flex: 6,
                    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      _GlassCard(
                        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                          const Text('Quick Actions', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                          const SizedBox(height: 8),
                          _buildActionTiles(),
                          const SizedBox(height: 10),
                          _buildCEDPreview(),
                        ]),
                      ),
                      const SizedBox(height: 10),
                      _GlassCard(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                        const Text('Latest Alerts', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                        const SizedBox(height: 8),
                        _buildAlertsColumn(),
                      ])),
                      const SizedBox(height: 10),
                      _buildForensicsPreview(),
                      const SizedBox(height: 10),
                      // PASM Panel
                      PasmPanelWidget(
                        onDrillDown: () => Navigator.pushNamed(context, '/pasm'),
                      ),
                    ]),
                  ),
                  const SizedBox(width: 14),
                  // Right column
                  Expanded(
                    flex: 7,
                    child: Column(children: [
                      // Radar + AI core aligned
                      Stack(children: [
                        Container(
                          decoration: BoxDecoration(
                            color: Colors.black.withOpacity(0.18),
                            borderRadius: BorderRadius.circular(12),
                          ),
                          padding: const EdgeInsets.all(12),
                          child: Row(children: [
                            // radar
                            Expanded(child: _buildRadar()),
                            const SizedBox(width: 12),
                            // AI core + micro details
                            Column(children: [
                              _buildAICore(),
                              const SizedBox(height: 12),
                              _buildTopRiskCard(),
                            ]),
                          ]),
                        ),
                      ]),
                      const SizedBox(height: 12),
                      _buildAttackPreviewCompact(),
                    ]),
                  ),
                ],
              ),
              const SizedBox(height: 20),
              // foot actions
              Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
                ElevatedButton.icon(onPressed: _refreshAll, icon: const Icon(Icons.refresh), label: const Text('Refresh')),
                Text('Connected nodes: 12 • Federated: ON', style: TextStyle(color: Colors.white54)),
              ])
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildDrawer() {
    return Drawer(
      backgroundColor: const Color(0xFF02111F),
      child: ListView(padding: EdgeInsets.zero, children: [
        DrawerHeader(
          decoration: const BoxDecoration(color: Colors.transparent),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            const Text('J.A.R.V.I.S.', style: TextStyle(color: Colors.white, fontSize: 22, fontWeight: FontWeight.bold)),
            const SizedBox(height: 6),
            Text('Conscious Cyber Defense', style: TextStyle(color: Colors.white.withOpacity(0.7))),
            const Spacer(),
            OutlinedButton.icon(
              onPressed: _openWhitepaper,
              icon: const Icon(Icons.picture_as_pdf),
              label: const Text('Open Whitepaper'),
            )
          ]),
        ),
        ListTile(leading: const Icon(Icons.rss_feed), title: const Text('Live Feed'), onTap: () { Navigator.of(context).pop(); Navigator.of(context).pushNamed('/feed'); }),
        ListTile(leading: const Icon(Icons.devices), title: const Text('Assets'), onTap: () { Navigator.of(context).pop(); Navigator.of(context).pushNamed('/assets'); }),
        ListTile(leading: const Icon(Icons.timeline), title: const Text('Attack Path (PASM)'), onTap: () { Navigator.of(context).pop(); Navigator.of(context).pushNamed('/pasm'); }),
        ListTile(leading: const Icon(Icons.explore), title: const Text('CED Explain'), onTap: () { Navigator.of(context).pop(); Navigator.of(context).pushNamed('/ced'); }),
        if (!kIsWeb) ListTile(leading: const Icon(Icons.mic), title: const Text('Vocal SOC'), onTap: () { Navigator.of(context).pop(); Navigator.of(context).pushNamed('/vocal'); }),
        ListTile(leading: const Icon(Icons.build), title: const Text('Self-healing'), onTap: () { Navigator.of(context).pop(); Navigator.of(context).pushNamed('/self_healing'); }),
        ListTile(leading: const Icon(Icons.group), title: const Text('Federation'), onTap: () { Navigator.of(context).pop(); Navigator.of(context).pushNamed('/federation'); }),
        const Divider(color: Colors.white12),
        ListTile(leading: const Icon(Icons.settings), title: const Text('Settings'), onTap: () {}),
      ]),
    );
  }

  Widget _buildTopRiskCard() {
    final name = _topRiskAsset?['asset_id']?.toString() ?? 'none';
    final score = (_topRiskAsset?['score'] is num) ? (_topRiskAsset!['score'] as num).toDouble() : 0.0;
    final color = score > 0.7 ? Colors.redAccent : (score > 0.4 ? Colors.orangeAccent : Colors.greenAccent);
    return Container(
      width: 140,
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(color: Colors.black.withOpacity(0.35), borderRadius: BorderRadius.circular(10)),
      child: Column(children: [
        Text('Top Risk', style: TextStyle(color: Colors.white70, fontSize: 12)),
        const SizedBox(height: 6),
        Text(name, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
        const SizedBox(height: 6),
        LinearProgressIndicator(value: score, color: color, backgroundColor: Colors.white10),
      ]),
    );
  }

  Widget _buildAttackPreviewCompact() {
    return _GlassCard(
      child: Row(children: [
        Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          const Text('Attack Landscape', style: TextStyle(fontWeight: FontWeight.bold)),
          const SizedBox(height: 6),
          const Text('Interactive PASM map and predicted attack chains', style: TextStyle(color: Colors.white70)),
        ])),
        ElevatedButton(onPressed: () => Navigator.of(context).pushNamed('/pasm'), child: const Text('Open')),
      ]),
    );
  }
}

// ----------------- Supporting small widgets and painters -----------------

class _GlassCard extends StatefulWidget {
  final Widget child;
  final bool enableGlow;
  
  const _GlassCard({
    required this.child,
    this.enableGlow = true,
  });

  @override
  State<_GlassCard> createState() => _GlassCardState();
}

class _GlassCardState extends State<_GlassCard> with SingleTickerProviderStateMixin {
  late AnimationController _hoverController;
  late Animation<double> _hoverAnimation;

  @override
  void initState() {
    super.initState();
    _hoverController = AnimationController(
      duration: const Duration(milliseconds: 300),
      vsync: this,
    );
    _hoverAnimation = Tween<double>(begin: 1.0, end: 1.0).animate(
      CurvedAnimation(parent: _hoverController, curve: Curves.easeOut),
    );
  }

  @override
  void dispose() {
    _hoverController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return MouseRegion(
      onEnter: (_) {
        _hoverAnimation = Tween<double>(begin: 1.0, end: 1.02).animate(
          CurvedAnimation(parent: _hoverController, curve: Curves.easeOut),
        );
        _hoverController.forward();
      },
      onExit: (_) {
        _hoverAnimation = Tween<double>(begin: 1.02, end: 1.0).animate(
          CurvedAnimation(parent: _hoverController, curve: Curves.easeOut),
        );
        _hoverController.forward();
      },
      child: AnimatedBuilder(
        animation: _hoverAnimation,
        builder: (context, child) {
          return Transform.scale(
            scale: _hoverAnimation.value,
            child: Container(
              width: double.infinity,
              margin: const EdgeInsets.symmetric(vertical: 8),
              padding: const EdgeInsets.all(16),
              decoration: ModernEffects.glassCard(hasGlow: widget.enableGlow),
              child: ClipRRect(
                borderRadius: BorderRadius.circular(8),
                child: BackdropFilter(
                  filter: ui.ImageFilter.blur(sigmaX: 10, sigmaY: 10),
                  child: child,
                ),
              ),
            ),
          );
        },
        child: widget.child,
      ),
    );
  }
}

class _GlassActionTile extends StatefulWidget {
  final String label;
  final IconData icon;
  final Color color;
  const _GlassActionTile({required this.label, required this.icon, required this.color});

  @override
  State<_GlassActionTile> createState() => __GlassActionTileState();
}

class __GlassActionTileState extends State<_GlassActionTile> with SingleTickerProviderStateMixin {
  late final AnimationController _ctl = AnimationController(vsync: this, duration: const Duration(milliseconds: 220));
  @override
  void dispose() { _ctl.dispose(); super.dispose(); }
  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTapDown: (_) => _ctl.forward(),
      onTapUp: (_) => _ctl.reverse(),
      onTapCancel: () => _ctl.reverse(),
      child: ScaleTransition(
        scale: Tween<double>(begin: 1.0, end: 0.96).animate(CurvedAnimation(parent: _ctl, curve: Curves.easeOut)),
        child: Container(
          decoration: BoxDecoration(
            color: Colors.white10,
            borderRadius: BorderRadius.circular(10),
            border: Border.all(color: Colors.white12),
          ),
          padding: const EdgeInsets.all(12),
          child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
            Container(
              width: 44,
              height: 44,
              decoration: BoxDecoration(shape: BoxShape.circle, gradient: RadialGradient(colors: [widget.color.withOpacity(0.95), Colors.transparent])),
              child: Icon(widget.icon, color: Colors.black, size: 24),
            ),
            const SizedBox(height: 10),
            Text(widget.label, style: const TextStyle(fontWeight: FontWeight.bold)),
          ]),
        ),
      ),
    );
  }
}

class _OrbPainter extends CustomPainter {
  final double progress;
  final double pulse;
  _OrbPainter({required this.progress, required this.pulse});

  @override
  void paint(Canvas canvas, Size size) {
    final center = size.center(Offset.zero);
    final radius = min(size.width, size.height) / 2.6;
    final base = Paint()..shader = ui.Gradient.radial(center, radius, [const Color(0xFF002B36), const Color(0xFF00121F)]);
    canvas.drawCircle(center, radius, base);

    // subtle network lines
    final line = Paint()..color = const Color(0xFF00E8FF).withOpacity(0.08 + pulse * 0.2)..strokeWidth = 1.2;
    for (var i = 0; i < 5; i++) {
      final a = progress * pi * 2 + i * pi / 3;
      final x = center.dx + cos(a) * radius * 0.85;
      final y = center.dy + sin(a) * radius * 0.85;
      canvas.drawLine(center, Offset(x, y), line);
    }

    // glow ring
    final glow = Paint()..color = const Color(0xFF00E8FF).withOpacity(0.08 + pulse * 0.3)..style = PaintingStyle.stroke..strokeWidth = 6;
    canvas.drawCircle(center, radius + 6 * (0.8 + 0.2 * pulse), glow);
  }

  @override
  bool shouldRepaint(covariant _OrbPainter old) => old.progress != progress || old.pulse != pulse;
}

class _Blip { final double angle, distance, strength; final String label; _Blip({ required this.angle, required this.distance, required this.strength, required this.label}); }

class _RadarPainter extends CustomPainter {
  final double progress;
  final List<_Blip> blips;
  _RadarPainter({required this.progress, required this.blips});

  @override
  void paint(Canvas canvas, Size size) {
    final center = size.center(Offset.zero);
    final radius = min(size.width, size.height) / 2.2;
    final stroke = Paint()..color = Colors.white12..style = PaintingStyle.stroke..strokeWidth = 1;
    // concentric rings
    for (var i = 1; i <= 4; i++) {
      canvas.drawCircle(center, radius * (i / 4), stroke);
    }

    // sweeping radar line
    final sweep = Paint()..shader = ui.Gradient.radial(center, radius, [Colors.cyanAccent.withOpacity(0.25), Colors.transparent])..blendMode = BlendMode.screen;
    final sweepAngle = progress * pi * 2;
    final sweepPath = Path()..moveTo(center.dx, center.dy)..arcTo(Rect.fromCircle(center: center, radius: radius), sweepAngle - 0.25, 0.5, false)..close();
    canvas.drawPath(sweepPath, sweep);

    // draw blips (converted from polar coords)
    for (final b in blips) {
      final ang = b.angle;
      final r = b.distance * radius;
      final x = center.dx + cos(ang) * r;
      final y = center.dy + sin(ang) * r;
      final p = Paint()..color = Colors.redAccent.withOpacity(b.strength * 0.9)..style = PaintingStyle.fill;
      canvas.drawCircle(Offset(x, y), 6 * b.strength, p);
      // label
      final tp = TextPainter(text: TextSpan(text: b.label, style: TextStyle(color: Colors.white54, fontSize: 9)), textDirection: TextDirection.ltr);
      tp.layout();
      tp.paint(canvas, Offset(x + 8, y - 6));
    }
  }

  @override
  bool shouldRepaint(covariant _RadarPainter old) => old.progress != progress || old.blips.length != blips.length;
}
