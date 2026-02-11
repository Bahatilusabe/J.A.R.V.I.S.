import 'dart:convert';
import 'auth_service.dart';
import 'http_client.dart';
import '../config.dart';

class ApiClient {
  static String get _base => Config.baseUrl;

  static Future<String?> getStatus() async {
    try {
      final token = await AuthService.getStoredToken();
      final headers = <String, String>{'Accept': 'application/json'};
      if (token != null) headers['Authorization'] = 'Bearer $token';

  final client = AuthenticatedClient();
  final res = await client.get(Uri.parse('$_base/api/v1/mobile/status'), headers: headers).timeout(const Duration(seconds: 5));
  client.close();
      if (res.statusCode == 200) {
        final data = json.decode(res.body);
        return data['status']?.toString() ?? res.body;
      }
      return 'http ${res.statusCode}';
    } catch (e) {
      return null;
    }
  }
}
