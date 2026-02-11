import 'dart:convert';
import 'dart:typed_data';

import 'package:web_socket_channel/web_socket_channel.dart';

import '../config.dart';
import 'http_client.dart';

class VocalSocService {
  final AuthenticatedClient client;

  VocalSocService(this.client);

  /// Open a websocket to the ASR streaming endpoint. Caller is responsible for
  /// listening to channel.stream and closing the channel.
  WebSocketChannel openAsrStream() {
    final uri = Uri.parse(Config.wsPath('/ws/vocal/stream'));
    // Pass auth header if available
    // AuthenticatedClient doesn't currently expose token publicly; if needed,
    // modify AuthenticatedClient to expose the token or pass headers here.
    return WebSocketChannel.connect(uri);
  }

  /// Parse intent either from text or raw audio bytes (WAV recommended).
  /// Either provide [text] or [audioBytes]. If both provided, audio takes precedence.
  Future<Map<String, dynamic>> parseIntent({String? text, Uint8List? audioBytes, String? format}) async {
    final url = Uri.parse('${Config.baseUrl}/vocal/intent');
    Map<String, dynamic> payload = {};
    if (audioBytes != null) {
      payload['audio_b64'] = base64Encode(audioBytes);
      if (format != null) payload['format'] = format;
    } else if (text != null) {
      payload['text'] = text;
    } else {
      throw ArgumentError('either text or audioBytes must be provided');
    }

    final resp = await client.post(url, body: jsonEncode(payload), headers: {
      'Content-Type': 'application/json'
    });
    return jsonDecode(resp.body) as Map<String, dynamic>;
  }

  /// Verify identity using audio bytes. The server-side `VoiceAuthenticator`
  /// expects WAV-formatted audio bytes (base64) or a path. We send `audio_b64`.
  Future<Map<String, dynamic>> verifyIdentity({required Uint8List audioBytes, String? userId}) async {
    final url = Uri.parse('${Config.baseUrl}/vocal/auth');
    final payload = {
      'audio_b64': base64Encode(audioBytes),
      'format': 'wav',
    };
    if (userId != null) payload['user_id'] = userId;

    final resp = await client.post(url, body: jsonEncode(payload), headers: {
      'Content-Type': 'application/json'
    });
    return jsonDecode(resp.body) as Map<String, dynamic>;
  }

  /// Enroll a user by sending WAV bytes to the server.
  Future<Map<String, dynamic>> enroll({required String userId, required Uint8List audioBytes}) async {
    final url = Uri.parse('${Config.baseUrl}/vocal/enroll');
    final payload = {
      'user_id': userId,
      'audio_b64': base64Encode(audioBytes),
      'format': 'wav',
    };
    final resp = await client.post(url, body: jsonEncode(payload), headers: {
      'Content-Type': 'application/json'
    });
    return jsonDecode(resp.body) as Map<String, dynamic>;
  }
}
