// Use conditional imports to avoid importing dart:io on web builds.
import 'src/platform_stub.dart'
    if (dart.library.io) 'src/platform_android.dart'
    if (dart.library.html) 'src/platform_web.dart';

class Config {
  // Change these values for production environment.
  static const String scheme = 'http';
  static const int port = 8000;

  // If true, use secure websocket (wss) and https for REST
  static const bool useTls = false;

  // Use platform helper to detect Android and choose emulator host mapping.
  static String get host {
    final base = defaultHost;
    if (isAndroid && base == 'localhost') return '10.0.2.2';
    return base;
  }

  static String get baseUrl {
    final proto = useTls ? 'https' : 'http';
    return '$proto://$host:$port';
  }

  static String get wsScheme => useTls ? 'wss' : 'ws';

  static String wsPath(String path) => '$wsScheme://$host:$port$path';
}
