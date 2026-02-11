import 'dart:convert';
import 'package:http/http.dart' as http;
import 'auth_service.dart';
import 'http_client.dart';
import '../config.dart';

class DashboardService {
  // Default to local backend in dev. Change to production host as needed.
  static String get _base => Config.baseUrl;

  static Future<Map<String, String>> _authHeaders() async {
    final token = await AuthService.getStoredToken();
    final headers = <String, String>{'Accept': 'application/json'};
    if (token != null) headers['Authorization'] = 'Bearer $token';
    return headers;
  }

  /// Fetch latest telemetry alerts. Expects an array of alerts.
  static Future<List<Map<String, dynamic>>> getLatestAlerts({http.Client? client}) async {
    client ??= AuthenticatedClient();
    try {
      final headers = await _authHeaders();
      final res = await client.get(Uri.parse('$_base/telemetry/latest'), headers: headers).timeout(const Duration(seconds: 5));
      if (res.statusCode == 200) {
        final data = json.decode(res.body);
        if (data is List) return List<Map<String, dynamic>>.from(data.cast<Map>());
      }
    } catch (_) {}
    return [];
  }

  /// Fetch top risk asset from PASM predictor.
  static Future<Map<String, dynamic>?> getPasmTopRisk({http.Client? client}) async {
    client ??= AuthenticatedClient();
    try {
      final headers = await _authHeaders();
      final res = await client.get(Uri.parse('$_base/pasm/top_risk'), headers: headers).timeout(const Duration(seconds: 5));
      if (res.statusCode == 200) {
        final data = json.decode(res.body);
        if (data is Map) return Map<String, dynamic>.from(data);
      }
    } catch (_) {}
    return null;
  }

  /// Fetch telemetry history (e.g., last N alerts).
  static Future<List<Map<String, dynamic>>> getTelemetryHistory({int limit = 50}) async {
    return getTelemetryHistoryWithClient(limit: limit, client: null);
  }

  // Separated helper to allow passing a mock client in tests.
  static Future<List<Map<String, dynamic>>> getTelemetryHistoryWithClient({int limit = 50, http.Client? client}) async {
    client ??= AuthenticatedClient();
    try {
      final headers = await _authHeaders();
      final res = await client.get(Uri.parse('$_base/telemetry/history?limit=$limit'), headers: headers).timeout(const Duration(seconds: 5));
      if (res.statusCode == 200) {
        final data = json.decode(res.body);
        if (data is List) return List<Map<String, dynamic>>.from(data.cast<Map>());
      }
    } catch (_) {}
    return [];
  }

  /// Quick actions (placeholders) — these should map to real backend actions.
  static Future<bool> containAsset(String assetId, {http.Client? client}) async {
    client ??= AuthenticatedClient();
    try {
      final headers = await _authHeaders();
      headers['Content-Type'] = 'application/json';
      final res = await client.post(Uri.parse('$_base/actions/contain'), headers: headers, body: json.encode({'asset_id': assetId})).timeout(const Duration(seconds: 5));
      return res.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  static Future<bool> patchAsset(String assetId, {http.Client? client}) async {
    client ??= AuthenticatedClient();
    try {
      final headers = await _authHeaders();
      headers['Content-Type'] = 'application/json';
      final res = await client.post(Uri.parse('$_base/actions/patch'), headers: headers, body: json.encode({'asset_id': assetId})).timeout(const Duration(seconds: 5));
      return res.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  static Future<bool> blockAsset(String assetId, {http.Client? client}) async {
    client ??= AuthenticatedClient();
    try {
      final headers = await _authHeaders();
      headers['Content-Type'] = 'application/json';
      final res = await client.post(Uri.parse('$_base/actions/block'), headers: headers, body: json.encode({'asset_id': assetId})).timeout(const Duration(seconds: 5));
      return res.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  static Future<bool> explainAlert(String alertId, {http.Client? client}) async {
    client ??= AuthenticatedClient();
    try {
      final headers = await _authHeaders();
      headers['Content-Type'] = 'application/json';
      final res = await client.post(Uri.parse('$_base/actions/explain'), headers: headers, body: json.encode({'alert_id': alertId})).timeout(const Duration(seconds: 5));
      return res.statusCode == 200;
    } catch (_) {
      return false;
    }
  }
}
