import 'package:web_socket_channel/io.dart';
import 'package:web_socket_channel/web_socket_channel.dart';

WebSocketChannel connectWebSocket(Uri uri, {Map<String, String>? headers}) {
  // IOWebSocketChannel.connect expects a String URL; headers are supported.
  final url = uri.toString();
  if (headers != null && headers.isNotEmpty) {
    return IOWebSocketChannel.connect(url, headers: headers);
  }
  return IOWebSocketChannel.connect(url);
}
