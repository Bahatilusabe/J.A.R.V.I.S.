import 'dart:async';
import 'dart:math' as math;
import 'package:flutter/foundation.dart' show kIsWeb, debugPrint;
import 'package:web_socket_channel/web_socket_channel.dart';
// Use a small connector wrapper that resolves to the native I/O connector on
// non-web platforms and to the browser connector on web. This avoids
// referencing IOWebSocketChannel when compiling to web.
import 'ws_connector_io.dart' if (dart.library.html) 'ws_connector_web.dart';

/// WebSocket client with header-based auth attempt and automatic reconnect with backoff.
class WsClient {
  final String url;
  final String? token;

  WebSocketChannel? _chan;
  StreamController<String>? _controller;
  StreamSubscription? _sub;
  bool _shouldReconnect = true;
  int _retryCount = 0;

  WsClient(this.url, {this.token});

  Stream<String> get stream {
    _controller ??= StreamController<String>.broadcast(onListen: () {}, onCancel: () {});
    return _controller!.stream;
  }

  void connect() {
    _shouldReconnect = true;
    debugPrint('[ws] connect requested url=$url token=${token != null ? 'present' : 'none'} kIsWeb=$kIsWeb');
    _open();
  }

  void _open() {
    try {
      debugPrint('[ws] _open start url=$url retry=$_retryCount');
      Uri uri = Uri.parse(url);
      if (kIsWeb) {
        // Browser: use the default WebSocket implementation. Headers not
        // supported by browser WebSocket, so append token as query param.
        if (token != null && token!.isNotEmpty) {
          final params = Map<String, String>.from(uri.queryParameters);
          params['token'] = token!;
          uri = uri.replace(queryParameters: params);
        }
        _chan = connectWebSocket(uri);
      } else {
        if (token != null && token!.isNotEmpty) {
          // try header-based auth for native platforms
          try {
            _chan = connectWebSocket(uri, headers: {'Authorization': 'Bearer $token'});
          } catch (e) {
            // fallback: append token as query param
            final params = Map<String, String>.from(uri.queryParameters);
            params['token'] = token!;
            uri = uri.replace(queryParameters: params);
            _chan = connectWebSocket(uri);
          }
        } else {
          _chan = connectWebSocket(uri);
        }
      }

      _sub = _chan!.stream.listen((event) {
        debugPrint('[ws] message received (${event.runtimeType})');
        _controller?.add(event.toString());
      }, onError: (e) {
        _controller?.addError(e);
        debugPrint('[ws] listen error: $e');
        _scheduleReconnect();
      }, onDone: () {
        debugPrint('[ws] onDone called, scheduling reconnect');
        _scheduleReconnect();
      });

      // reset retry count on successful open
      _retryCount = 0;
    } catch (e) {
      debugPrint('[ws] _open exception: $e');
      _scheduleReconnect();
    }
  }

  void _scheduleReconnect() {
    if (!_shouldReconnect) return;
    _retryCount += 1;
    // Use a shorter, bounded backoff to avoid long stalls in the browser.
    final delaySeconds = math.min(5, math.pow(2, _retryCount).toInt());
    Future.delayed(Duration(seconds: delaySeconds), () {
      if (!_shouldReconnect) return;
      debugPrint('[ws] reconnecting attempt=$_retryCount after ${delaySeconds}s');
      _open();
    });
  }

  void dispose() {
    debugPrint('[ws] dispose called for url=$url');
    _shouldReconnect = false;
    _sub?.cancel();
    try {
      _chan?.sink.close();
    } catch (_) {}
    _chan = null;
    _controller?.close();
    _controller = null;
  }
}
