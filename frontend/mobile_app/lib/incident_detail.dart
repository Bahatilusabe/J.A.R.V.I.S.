import 'package:flutter/material.dart';

class IncidentDetail extends StatelessWidget {
  final Map<String, dynamic> alert;
  const IncidentDetail({super.key, required this.alert});

  @override
  Widget build(BuildContext context) {
    final id = alert['id']?.toString() ?? 'unknown';
    final asset = (alert['asset'] ?? alert['asset_name'] ?? alert['asset_id'] ?? 'Unknown').toString();
    final desc = (alert['description'] ?? alert['message'] ?? '').toString();
    final severity = (alert['severity'] ?? 'info').toString();
    final ts = (alert['timestamp'] ?? alert['time'] ?? '').toString();

    return Scaffold(
      appBar: AppBar(title: Text('Incident $id')),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(children: [
              Text('Severity: ', style: TextStyle(fontWeight: FontWeight.bold)),
              Text(severity.toUpperCase(), style: const TextStyle(color: Colors.red)),
            ]),
            const SizedBox(height: 8),
            Text('Asset: $asset', style: const TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            Text('Time: $ts', style: const TextStyle(color: Colors.white70)),
            const SizedBox(height: 16),
            const Text('Description', style: TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            Expanded(child: SingleChildScrollView(child: Text(desc))),
          ],
        ),
      ),
    );
  }
}
