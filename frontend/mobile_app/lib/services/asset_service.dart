import 'dart:convert';

import 'package:http/http.dart' as http;

import 'http_client.dart';
import '../config.dart';

class AssetSummary {
  final String id;
  final String name;
  final bool online;
  final DateTime? lastTelemetry;

  AssetSummary({
    required this.id,
    required this.name,
    required this.online,
    this.lastTelemetry,
  });

  factory AssetSummary.fromJson(Map<String, dynamic> j) {
    return AssetSummary(
      id: j['id'].toString(),
      name: j['name'] ?? j['asset_name'] ?? 'unknown',
      online: j['online'] == true || j['status'] == 'online',
      lastTelemetry: j['last_telemetry'] != null
          ? DateTime.tryParse(j['last_telemetry'])
          : null,
    );
  }
}

class AssetDetail {
  final String id;
  final String name;
  final bool online;
  final List<String> vulnerabilities;
  final DateTime? lastTelemetry;

  AssetDetail({
    required this.id,
    required this.name,
    required this.online,
    required this.vulnerabilities,
    this.lastTelemetry,
  });

  factory AssetDetail.fromJson(Map<String, dynamic> j) {
    final vulns = <String>[];
    if (j['vulnerabilities'] is List) {
      for (final v in j['vulnerabilities']) {
        vulns.add(v.toString());
      }
    }
    return AssetDetail(
      id: j['id'].toString(),
      name: j['name'] ?? j['asset_name'] ?? 'unknown',
      online: j['online'] == true || j['status'] == 'online',
      vulnerabilities: vulns,
      lastTelemetry: j['last_telemetry'] != null
          ? DateTime.tryParse(j['last_telemetry'])
          : null,
    );
  }
}

class AssetRisk {
  final String assetId;
  final double riskScore; // 0.0 - 1.0

  AssetRisk({required this.assetId, required this.riskScore});

  factory AssetRisk.fromJson(Map<String, dynamic> j) {
    return AssetRisk(
      assetId: j['asset']?.toString() ?? '',
      riskScore: (j['risk'] is num) ? (j['risk'] as num).toDouble() : 0.0,
    );
  }
}

class AssetService {
  final http.Client client;

  AssetService({http.Client? client}) : client = client ?? AuthenticatedClient();

  Future<List<AssetSummary>> getAssets() async {
    final uri = Uri.parse('${Config.baseUrl}/assets');
    final res = await client.get(uri);
    if (res.statusCode != 200) {
      throw Exception('Failed to load assets: ${res.statusCode}');
    }
    final body = json.decode(res.body);
    if (body is List) {
      return body.map((e) => AssetSummary.fromJson(Map<String, dynamic>.from(e))).toList();
    }
    return [];
  }

  Future<AssetDetail> getAsset(String id) async {
    final uri = Uri.parse('${Config.baseUrl}/assets/$id');
    final res = await client.get(uri);
    if (res.statusCode != 200) {
      throw Exception('Failed to load asset $id: ${res.statusCode}');
    }
    final body = json.decode(res.body);
    return AssetDetail.fromJson(Map<String, dynamic>.from(body));
  }

  Future<AssetRisk> getRisk(String id) async {
    final uri = Uri.parse('${Config.baseUrl}/pasm/risk?asset=$id');
    final res = await client.get(uri);
    if (res.statusCode != 200) {
      // Some backends might return 404 or 204 — default to zero
      return AssetRisk(assetId: id, riskScore: 0.0);
    }
    final body = json.decode(res.body);
    return AssetRisk.fromJson(Map<String, dynamic>.from(body));
  }
}
