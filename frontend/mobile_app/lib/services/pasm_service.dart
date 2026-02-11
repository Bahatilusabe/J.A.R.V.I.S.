import 'dart:convert';

import 'package:http/http.dart' as http;

import 'http_client.dart';
import '../config.dart';

class PathNode {
  final String id;
  final String label;

  PathNode({required this.id, required this.label});

  factory PathNode.fromJson(Map<String, dynamic> j) {
    return PathNode(id: j['id'].toString(), label: j['label'] ?? j['name'] ?? j['id'].toString());
  }
}

class AttackPath {
  final List<String> nodes; // node ids in order
  final double score;
  final String reason;

  AttackPath({required this.nodes, required this.score, this.reason = ''});

  factory AttackPath.fromJson(Map<String, dynamic> j) {
    return AttackPath(
      nodes: (j['nodes'] is List) ? List<String>.from(j['nodes'].map((e) => e.toString())) : [],
      score: (j['score'] is num) ? (j['score'] as num).toDouble() : 0.0,
      reason: j['reason']?.toString() ?? '',
    );
  }
}

class PasmService {
  final http.Client client;

  PasmService({http.Client? client}) : client = client ?? AuthenticatedClient();

  /// GET /pasm/graph/small
  Future<List<PathNode>> getSmallGraph() async {
    final uri = Uri.parse('${Config.baseUrl}/pasm/graph/small');
    final res = await client.get(uri);
    if (res.statusCode != 200) throw Exception('Failed to load graph: ${res.statusCode}');
    final body = json.decode(res.body);
    if (body is List) {
      return body.map((e) => PathNode.fromJson(Map<String, dynamic>.from(e))).toList();
    }
    return [];
  }

  /// GET /pasm/predict?asset={id}
  Future<List<AttackPath>> predictForAsset(String assetId) async {
    final uri = Uri.parse('${Config.baseUrl}/pasm/predict?asset=$assetId');
    final res = await client.get(uri);
    if (res.statusCode != 200) throw Exception('Predict failed: ${res.statusCode}');
    final body = json.decode(res.body);
    if (body is List) {
      return body.map((e) => AttackPath.fromJson(Map<String, dynamic>.from(e))).toList();
    }
    return [];
  }

  /// GET /pasm/confidence
  Future<double> getConfidence() async {
    final uri = Uri.parse('${Config.baseUrl}/pasm/confidence');
    final res = await client.get(uri);
    if (res.statusCode != 200) return 0.0;
    final body = json.decode(res.body);
    if (body is Map && body['confidence'] is num) return (body['confidence'] as num).toDouble();
    return 0.0;
  }
}
