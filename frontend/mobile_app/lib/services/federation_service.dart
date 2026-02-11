import 'dart:convert';
import 'package:http/http.dart' as http;
import 'http_client.dart';

class FederationService {
  final AuthenticatedClient client;
  final String baseUrl;
  final String? adminToken;

  FederationService(
    this.client, {
    this.baseUrl = const String.fromEnvironment('API_BASE', defaultValue: ''),
    this.adminToken = const String.fromEnvironment('FEDERATION_ADMIN_TOKEN', defaultValue: ''),
  });

  Future<Map<String, dynamic>> getStatus() async {
    final url = Uri.parse('${baseUrl.isEmpty ? '' : baseUrl}/federation/status');
    final resp = await client.get(url).timeout(const Duration(seconds: 6));
    return json.decode(resp.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> getModels() async {
    final url = Uri.parse('${baseUrl.isEmpty ? '' : baseUrl}/federation/models');
    final resp = await client.get(url).timeout(const Duration(seconds: 6));
    return json.decode(resp.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> getNodeDetail(String nodeId, {int limit = 100}) async {
    final url = Uri.parse('${baseUrl.isEmpty ? '' : baseUrl}/federation/nodes/$nodeId?limit=$limit');
    final resp = await client.get(url).timeout(const Duration(seconds: 6));
    return json.decode(resp.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> triggerNodeSync(String nodeId) async {
    final url = Uri.parse('${baseUrl.isEmpty ? '' : baseUrl}/federation/nodes/$nodeId/sync');
    final req = http.Request('POST', url);
    if (adminToken != null && adminToken!.isNotEmpty) {
      req.headers['X-Admin-Token'] = adminToken!;
    }
    final resp = await client.send(req).timeout(const Duration(seconds: 10));
    return json.decode(await resp.stream.bytesToString()) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> triggerAggregate() async {
    final url = Uri.parse('${baseUrl.isEmpty ? '' : baseUrl}/federation/aggregate');
    final req = http.Request('POST', url);
    if (adminToken != null && adminToken!.isNotEmpty) {
      req.headers['X-Admin-Token'] = adminToken!;
    }
    final resp = await client.send(req).timeout(const Duration(seconds: 10));
    return json.decode(await resp.stream.bytesToString()) as Map<String, dynamic>;
  }
}
