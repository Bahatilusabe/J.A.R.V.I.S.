import 'dart:convert';

import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;
import '../config.dart';
import 'auth_state.dart';

class AuthService {
  static final _storage = FlutterSecureStorage();
  static const _tokenKey = 'jarvis_pqc_token';
  static const _refreshKey = 'jarvis_refresh_token';

  static Future<Map<String, dynamic>?> initHandshake(String deviceId) async {
    final base = Config.baseUrl;
    final t0 = DateTime.now();
    final res = await http.post(Uri.parse('$base/auth/mobile/init'),
        headers: {'Content-Type': 'application/json'}, body: json.encode({'device_id': deviceId}));
    final t1 = DateTime.now();
    print('[auth] initHandshake network_ms=${t1.difference(t0).inMilliseconds} url=$base/auth/mobile/init');
    if (res.statusCode == 200) return json.decode(res.body) as Map<String, dynamic>;
    return null;
  }

  static Future<bool> verifyBiometric(String handshakeId, String biometricToken) async {
    final base = Config.baseUrl;
    final t0 = DateTime.now();
    final res = await http.post(Uri.parse('$base/auth/biometric'),
        headers: {'Content-Type': 'application/json'}, body: json.encode({'handshake_id': handshakeId, 'biometric_token': biometricToken}));
    final t1 = DateTime.now();
    print('[auth] verifyBiometric network_ms=${t1.difference(t0).inMilliseconds} url=$base/auth/biometric');
    return res.statusCode == 200;
  }

  static Future<String?> createSession(String handshakeId) async {
    final base = Config.baseUrl;
  final t0 = DateTime.now();
  final res = await http.post(Uri.parse('$base/auth/mobile/session'),
    headers: {'Content-Type': 'application/json'}, body: json.encode({'handshake_id': handshakeId}));
  final t1 = DateTime.now();
  print('[auth] createSession network_ms=${t1.difference(t0).inMilliseconds} url=$base/auth/mobile/session');
    if (res.statusCode == 200) {
      final data = json.decode(res.body);
      final token = data['access_token'] as String?;
      final refresh = data['refresh_token'] as String?;
      if (token != null) {
        await _storage.write(key: _tokenKey, value: token);
        if (refresh != null) await _storage.write(key: _refreshKey, value: refresh);
        // notify listeners we're logged in
        AuthState.instance.setLoggedIn(true);
        return token;
      }
    }
    return null;
  }

  static Future<String?> getStoredToken() async {
    return await _storage.read(key: _tokenKey);
  }

  static Future<void> setStoredToken(String token) async {
    await _storage.write(key: _tokenKey, value: token);
    AuthState.instance.setLoggedIn(true);
  }

  static Future<void> clearToken() async {
    await _storage.delete(key: _tokenKey);
    await _storage.delete(key: _refreshKey);
    // notify listeners we're logged out
    AuthState.instance.setLoggedIn(false);
  }

  /// Attempt to refresh access token using stored refresh token.
  /// Returns true when a new access token was obtained and stored.
  static Future<bool> refreshToken() async {
    final refresh = await _storage.read(key: _refreshKey);
    if (refresh == null) return false;
    final base = Config.baseUrl;
    try {
      final res = await http.post(Uri.parse('$base/auth/refresh'), headers: {'Content-Type': 'application/json'}, body: json.encode({'refresh_token': refresh}));
      if (res.statusCode == 200) {
        final data = json.decode(res.body);
        final token = data['access_token'] as String?;
        final newRefresh = data['refresh_token'] as String?;
        if (token != null) {
          await _storage.write(key: _tokenKey, value: token);
          if (newRefresh != null) await _storage.write(key: _refreshKey, value: newRefresh);
          return true;
        }
      }
    } catch (_) {}
    return false;
  }
}
