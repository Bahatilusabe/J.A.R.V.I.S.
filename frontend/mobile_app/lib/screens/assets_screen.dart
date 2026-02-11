import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../services/asset_service.dart';

class AssetsScreen extends StatefulWidget {
  const AssetsScreen({super.key});

  @override
  State<AssetsScreen> createState() => _AssetsScreenState();
}

class _AssetsScreenState extends State<AssetsScreen> {
  final AssetService _service = AssetService();
  late Future<List<AssetSummary>> _future;

  @override
  void initState() {
    super.initState();
    _future = _service.getAssets();
  }

  Future<void> _refresh() async {
    setState(() {
      _future = _service.getAssets();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Assets'),
      ),
      body: FutureBuilder<List<AssetSummary>>(
        future: _future,
        builder: (context, snap) {
          if (snap.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snap.hasError) {
            return Center(child: Text('Error: ${snap.error}'));
          }
          final assets = snap.data ?? [];
          if (assets.isEmpty) {
            return RefreshIndicator(
              onRefresh: _refresh,
              child: ListView(
                children: const [SizedBox(height: 200), Center(child: Text('No assets'))],
              ),
            );
          }

          return RefreshIndicator(
            onRefresh: _refresh,
            child: GridView.builder(
              padding: const EdgeInsets.all(12),
              gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                crossAxisCount: 2,
                childAspectRatio: 0.95,
                crossAxisSpacing: 12,
                mainAxisSpacing: 12,
              ),
              itemCount: assets.length,
              itemBuilder: (context, i) {
                final a = assets[i];
                return _AssetCard(asset: a, onOpen: () async {
                  final detail = await _service.getAsset(a.id);
                  final risk = await _service.getRisk(a.id);
                  if (!mounted) return;
                  Navigator.of(context).push(MaterialPageRoute(builder: (_) => AssetDetailScreen(detail: detail, risk: risk)));
                });
              },
            ),
          );
        },
      ),
    );
  }
}

class _AssetCard extends StatelessWidget {
  final AssetSummary asset;
  final VoidCallback onOpen;

  const _AssetCard({required this.asset, required this.onOpen});

  @override
  Widget build(BuildContext context) {
    final last = asset.lastTelemetry;
    final lastText = last != null ? DateFormat.yMd().add_jm().format(last.toLocal()) : '—';
    return Card(
      child: InkWell(
        onTap: onOpen,
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Expanded(child: Text(asset.name, style: const TextStyle(fontWeight: FontWeight.bold))),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: asset.online ? Colors.green[600] : Colors.grey[600],
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Text(asset.online ? 'Online' : 'Offline', style: const TextStyle(color: Colors.white, fontSize: 12)),
                  )
                ],
              ),
              const SizedBox(height: 8),
              Expanded(child: Text('Last telemetry: $lastText', style: const TextStyle(fontSize: 12, color: Colors.black87))),
              const SizedBox(height: 8),
              Row(
                children: const [
                  Icon(Icons.bug_report, size: 16),
                  SizedBox(width: 6),
                  Text('Vulns: n/a', style: TextStyle(fontSize: 12)),
                ],
              ),
              const SizedBox(height: 8),
              Align(
                alignment: Alignment.centerRight,
                child: TextButton(onPressed: onOpen, child: const Text('Open')),
              )
            ],
          ),
        ),
      ),
    );
  }
}

class AssetDetailScreen extends StatelessWidget {
  final AssetDetail detail;
  final AssetRisk risk;

  const AssetDetailScreen({required this.detail, required this.risk, super.key});

  @override
  Widget build(BuildContext context) {
    final last = detail.lastTelemetry;
    final lastText = last != null ? DateFormat.yMd().add_jm().format(last.toLocal()) : '—';
    return Scaffold(
      appBar: AppBar(title: Text(detail.name)),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(
            children: [
              Expanded(child: Text('Risk: ${(risk.riskScore * 100).toStringAsFixed(1)}%', style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold))),
              Container(padding: const EdgeInsets.all(8), decoration: BoxDecoration(color: detail.online ? Colors.green : Colors.grey, borderRadius: BorderRadius.circular(8)), child: Text(detail.online ? 'Online' : 'Offline', style: const TextStyle(color: Colors.white)))
            ],
          ),
          const SizedBox(height: 12),
          Text('Last telemetry: $lastText'),
          const SizedBox(height: 12),
          const Text('Vulnerabilities', style: TextStyle(fontWeight: FontWeight.bold)),
          const SizedBox(height: 8),
          if (detail.vulnerabilities.isEmpty) const Text('No known vulnerabilities'),
          for (final v in detail.vulnerabilities)
            ListTile(
              dense: true,
              leading: const Icon(Icons.bug_report, color: Colors.orange),
              title: Text(v),
            ),
          const SizedBox(height: 12),
          ElevatedButton(onPressed: () {}, child: const Text('Contain asset'))
        ]),
      ),
    );
  }
}
