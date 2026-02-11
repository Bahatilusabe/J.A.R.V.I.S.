import 'package:web_socket_channel/web_socket_channel.dart';

WebSocketChannel connectWebSocket(Uri uri, {Map<String, String>? headers}) {
  // Browser WebSocket doesn't support custom headers; ignore headers.
  return WebSocketChannel.connect(uri);
}
