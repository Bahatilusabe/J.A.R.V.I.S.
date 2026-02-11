import 'dart:convert';
import 'http_client.dart';

class SelfHealingService {
  final AuthenticatedClient client;
  final String baseUrl;

  SelfHealingService(this.client, {this.baseUrl = const String.fromEnvironment('API_BASE', defaultValue: '')});

  Future<Map<String, dynamic>> getMetrics() async {
    final url = Uri.parse('${baseUrl.isEmpty ? '' : baseUrl}/self_healing/metrics');
    final resp = await client.get(url).timeout(const Duration(seconds: 6));
    return json.decode(resp.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> getActions({String? resource}) async {
    final q = resource != null ? '?resource=${Uri.encodeComponent(resource)}' : '';
    final url = Uri.parse('${baseUrl.isEmpty ? '' : baseUrl}/self_healing/actions$q');
    final resp = await client.get(url).timeout(const Duration(seconds: 6));
    return json.decode(resp.body) as Map<String, dynamic>;
  }
}
