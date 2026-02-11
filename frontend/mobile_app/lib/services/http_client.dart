import 'dart:async';
import 'package:http/http.dart' as http;
import 'auth_service.dart';

/// A HTTP client that injects Authorization header from AuthService and
/// retries once after attempting token refresh when a 401 is received.
class AuthenticatedClient extends http.BaseClient {
  final http.Client _inner;
  bool _closed = false;

  AuthenticatedClient([http.Client? inner]) : _inner = inner ?? http.Client();

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    if (_closed) throw StateError('Client closed');
    try {
      final token = await AuthService.getStoredToken();
      if (token != null && token.isNotEmpty) request.headers['Authorization'] = 'Bearer $token';
    } catch (_) {}

    var response = await _inner.send(request);

    if (response.statusCode == 401) {
      // try refresh
      final refreshed = await AuthService.refreshToken();
      if (refreshed) {
        final newToken = await AuthService.getStoredToken();
        if (newToken != null && request is http.Request) {
          final retry = http.Request(request.method, request.url)
            ..headers.addAll(request.headers)
            ..bodyBytes = request.bodyBytes;
          retry.headers['Authorization'] = 'Bearer $newToken';
          try {
            return await _inner.send(retry);
          } catch (_) {
            // fallthrough to clear token
          }
        }
      }

      // refresh failed or retry failed: clear tokens and notify listeners
      try {
        await AuthService.clearToken();
      } catch (_) {}
    }

    return response;
  }

  @override
  void close() {
    _closed = true;
    _inner.close();
  }
}
