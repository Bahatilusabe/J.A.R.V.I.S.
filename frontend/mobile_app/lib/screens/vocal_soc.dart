import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:math';
import 'package:flutter/foundation.dart' show kIsWeb;

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_sound/flutter_sound.dart';
import 'package:web_socket_channel/web_socket_channel.dart';

import '../services/vocalsoc_service.dart';
import '../services/http_client.dart';
import '../theme.dart';
import '../utils/modern_effects.dart';

class VocalSocScreen extends StatefulWidget {
  final AuthenticatedClient client;
  final VocalSocService? serviceOverride;

  const VocalSocScreen({super.key, required this.client, this.serviceOverride});

  @override
  State<VocalSocScreen> createState() => _VocalSocScreenState();
}

class _VocalSocScreenState extends State<VocalSocScreen>
    with SingleTickerProviderStateMixin {
  late VocalSocService service;
  WebSocketChannel? _channel;
  final FlutterSoundRecorder _recorder = FlutterSoundRecorder();
  StreamController<Uint8List>? _pcmController;
  StreamSubscription<Uint8List>? _pcmSub;
  bool _recording = false;
  String _transcript = '';
  String? _detectedIntent;
  final List<Map<String, dynamic>> _recentCommands = [];
  // ignore: unused_field
  final Random _rand = Random();
  List<double> _waveform = List.generate(40, (_) => 0.0);
  // ignore: unused_field
  Timer? _waveTimer;
  // ignore: unused_field
  Timer? _ampTimer;
  String? _currentRecordingPath;
  // ignore: unused_field
  int _lastSent = 0;
  // ignore: unused_field
  Timer? _fileSenderTimer;

  @override
  void initState() {
    super.initState();
    // allow injection via widget for testing
    service = widget.serviceOverride ?? VocalSocService(widget.client);
    // open the flutter_sound recorder session on non-web platforms
    if (!kIsWeb) {
      () async {
        try {
          await _recorder.openRecorder();
          // some platforms require setting subscription duration; ignore here
        } catch (_) {}
      }();
    }
  }

  Future<void> _showEnrollDialog() async {
    String userId = '';
    bool recordingLocal = false;

    await showDialog<void>(
      context: context,
      builder: (ctx) {
        return StatefulBuilder(builder: (ctx2, setState2) {
          return AlertDialog(
            title: const Text('Enroll user'),
            content: Column(mainAxisSize: MainAxisSize.min, children: [
              TextField(
                decoration: const InputDecoration(labelText: 'User ID'),
                onChanged: (v) => userId = v.trim(),
              ),
              const SizedBox(height: 8),
              Row(children: [
                    ElevatedButton.icon(
                  onPressed: () async {
                    // record a short enrollment clip
                    if (!recordingLocal) {
                      setState2(() => recordingLocal = true);
                      // start the same recorder used elsewhere (it creates a temp file)
                      if (!kIsWeb) {
                        await _startRecorder();
                      } else {
                        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Recording not available on web')));
                      }
                      setState2(() {});
                    } else {
                      if (!kIsWeb) {
                        await _stopRecorder();
                      }
                      setState2(() => recordingLocal = false);
                    }
                  },
                  icon: Icon(recordingLocal ? Icons.stop : Icons.fiber_manual_record),
                  label: Text(recordingLocal ? 'Stop' : 'Record'),
                ),
                const SizedBox(width: 8),
                Text(recordingLocal ? 'Recording...' : 'Tap record for ~3s'),
              ])
            ]),
            actions: [
              TextButton(onPressed: () => Navigator.of(ctx).pop(), child: const Text('Cancel')),
              ElevatedButton(
                onPressed: () async {
                  if (userId.isEmpty) return;
                  if (_currentRecordingPath == null) return;
                  try {
                    final f = File(_currentRecordingPath!);
                    final bytes = await f.readAsBytes();
                    final resp = await service.enroll(userId: userId, audioBytes: bytes);
                    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Enroll: ${resp['ok'] ?? true}')));
                  } catch (e) {
                    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Enroll failed: $e')));
                  }
                  Navigator.of(ctx).pop();
                },
                child: const Text('Enroll'),
              ),
            ],
          );
        });
      },
    );
  }

  @override
  void dispose() {
    _stopRecording();
    _pcmSub?.cancel();
    _pcmController?.close();
    try {
      _recorder.closeRecorder();
    } catch (_) {}
    super.dispose();
  }

  void _startRecording() {
    setState(() => _recording = true);
    // Start recording to a WAV file and stream PCM frames via flutter_sound.
    _startRecorder();
    // Open websocket for streaming frames
    try {
      _channel = service.openAsrStream();
      _channel!.stream.listen((msg) {
        try {
          final parsed = jsonDecode(msg as String) as Map<String, dynamic>;
          if (mounted) onAsrResult(parsed);
        } catch (_) {}
      }, onError: (err) {
        if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('ASR WS error: $err')));
      });
    } catch (e) {
      // ignore websocket errors; streaming will fallback to final upload
    }
  }

  void _stopRecording() {
    setState(() => _recording = false);
    _stopRecorder();
    // stop websocket sender
    if (_channel != null) {
      try {
        _channel!.sink.close();
      } catch (_) {}
      _channel = null;
    }
    _lastSent = 0;
  }

  void onAsrResult(Map<String, dynamic> parsed) async {
    // parsed includes keys: ok, text, intent
    final text = parsed['text']?.toString() ?? '';
    final intentMap = parsed['intent'] as Map<String, dynamic>?;
    final intent = intentMap != null ? intentMap['intent']?.toString() ?? intentMap['name']?.toString() ?? 'unknown' : parsed['intent']?.toString();
    setState(() {
      _transcript = text;
      _detectedIntent = intent;
    });
    if (intent != null) {
      _showConfirmationForIntent(intent, text);
    }
  }

  Future<void> _showConfirmationForIntent(String intent, String utterance) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) {
        return AlertDialog(
          title: Text('Confirm: $intent'),
          content: Text('Detected command: "${utterance}"\n\nExecute this action?'),
          actions: [
            TextButton(onPressed: () => Navigator.of(ctx).pop(false), child: const Text('Cancel')),
            ElevatedButton(onPressed: () => Navigator.of(ctx).pop(true), child: const Text('Confirm')),
          ],
        );
      },
    );

    if (confirmed == true) {
      // Verify identity (best-effort). We send the recorded WAV bytes to the
      // verify endpoint which matches the server-side VoiceAuthenticator.
      Uint8List? audioBytes;
      if (_currentRecordingPath != null) {
        try {
          final f = File(_currentRecordingPath!);
          audioBytes = await f.readAsBytes();
        } catch (_) {
          audioBytes = null;
        }
      }

      Map<String, dynamic> authResp = {};
      bool passed = false;
      if (audioBytes != null) {
        authResp = await service.verifyIdentity(audioBytes: audioBytes);
        passed = authResp['matched'] == true || authResp['verified'] == true || authResp['success'] == true;
      } else {
        // Fallback: no recorded audio available
        authResp = {'error': 'no_audio'};
        passed = false;
      }
      final entry = {
        'time': DateTime.now().toIso8601String(),
        'intent': intent,
        'utterance': utterance,
        'auth': authResp,
        'verified': passed,
      };
      setState(() => _recentCommands.insert(0, entry));
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(passed ? 'Voice verified — command queued' : 'Voice not verified — action blocked')),
      );
    }
  }

  Widget _buildWaveform() {
    return SizedBox(
      height: 80,
      child: CustomPaint(
        painter: _WavePainter(_waveform, _recording),
        child: Container(),
      ),
    );
  }

  Future<void> _startRecorder() async {
    try {
      final tmpDir = Directory.systemTemp;
      final filePath = '${tmpDir.path}/jarvis_vocal_${DateTime.now().millisecondsSinceEpoch}.wav';
      _currentRecordingPath = filePath;

      // prepare PCM stream controller that flutter_sound will feed
      _pcmController = StreamController<Uint8List>();
      _pcmSub = _pcmController!.stream.listen((chunk) {
        // forward PCM/WAV frames to websocket if available
        if (_channel != null) {
          try {
            _channel!.sink.add(chunk);
          } catch (_) {}
        }
        // compute RMS amplitude from 16-bit PCM little-endian
        try {
          double sum = 0.0;
          for (var i = 0; i + 1 < chunk.length; i += 2) {
            final sample = (chunk[i] & 0xFF) | (chunk[i + 1] << 8);
            int s = sample;
            if (s & 0x8000 != 0) s = s - 0x10000;
            sum += s * s;
          }
          if (chunk.length >= 2) {
            final rms = sqrt(sum / (chunk.length / 2));
            final amp = (rms / 32768.0).clamp(0.0, 1.0);
            setState(() {
              _waveform.removeAt(0);
              _waveform.add(amp);
            });
          }
        } catch (_) {}
      });

      // start recorder writing WAV to a file and streaming PCM chunks to controller
      await _recorder.startRecorder(
        toStream: _pcmController!.sink,
        toFile: filePath,
        codec: Codec.pcm16WAV,
        sampleRate: 16000,
        numChannels: 1,
      );

      setState(() => _recording = true);
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Recorder error: $e')));
    }
  }

  Future<void> _stopRecorder() async {
    try {
      // stop stream subscription first
      await _recorder.stopRecorder();
      _pcmSub?.cancel();
      _pcmSub = null;
      await _pcmController?.close();
      _pcmController = null;

      setState(() => _recording = false);

      // After stopping, read file and call ASR intent endpoint with audio bytes (WAV)
      if (_currentRecordingPath != null) {
        try {
          final f = File(_currentRecordingPath!);
          if (await f.exists()) {
            final bytes = await f.readAsBytes();
            // send final full-file parse in case server didn't produce final via WS
            final parsed = await service.parseIntent(audioBytes: bytes, format: 'wav');
            if (mounted) onAsrResult(parsed);
          }
        } catch (e) {
          // ignore
        }
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Stop recorder error: $e')));
    }
  }

  @override
  Widget build(BuildContext context) {
    final isMobile = MediaQuery.of(context).size.width < 600;

    return Scaffold(
      appBar: AppBar(
        title: const Text('VocalSOC'),
        elevation: 0,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            // Waveform card
            Container(
              decoration: ModernEffects.glassCard(hasGlow: _recording),
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    _recording ? 'Recording...' : 'Ready to Listen',
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      color: _recording ? neonCyan : Colors.white70,
                    ),
                  ),
                  const SizedBox(height: 12),
                  _buildWaveform(),
                  const SizedBox(height: 12),
                  if (_detectedIntent != null)
                    Container(
                      padding: const EdgeInsets.all(8),
                      decoration: BoxDecoration(
                        color: holographicBlue.withValues(alpha: 0.1),
                        border: Border.all(color: holographicBlue.withValues(alpha: 0.3)),
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: Row(
                        children: [
                          const Icon(Icons.lightbulb, color: holographicBlue, size: 16),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              'Intent: $_detectedIntent',
                              style: const TextStyle(
                                fontSize: 12,
                                color: Colors.white70,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  if (_transcript.isNotEmpty)
                    Padding(
                      padding: const EdgeInsets.only(top: 12),
                      child: Container(
                        padding: const EdgeInsets.all(8),
                        decoration: BoxDecoration(
                          color: Colors.white.withValues(alpha: 0.05),
                          border: Border.all(color: Colors.white24),
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: Text(
                          _transcript,
                          style: const TextStyle(
                            fontSize: 12,
                            color: Colors.white70,
                          ),
                        ),
                      ),
                    ),
                ],
              ),
            ),
            const SizedBox(height: 20),

            // Microphone button
            GestureDetector(
              onTapDown: (_) {
                if (!_recording) _startRecording();
              },
              onTapUp: (_) {
                if (_recording) _stopRecording();
              },
              onTapCancel: () {
                if (_recording) _stopRecording();
              },
              child: MouseRegion(
                cursor: SystemMouseCursors.click,
                child: TweenAnimationBuilder<double>(
                  tween: Tween<double>(begin: 1.0, end: _recording ? 1.1 : 1.0),
                  duration: const Duration(milliseconds: 200),
                  builder: (context, scale, child) {
                    return Transform.scale(
                      scale: scale,
                      child: Container(
                        width: 100,
                        height: 100,
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          gradient: LinearGradient(
                            colors: _recording 
                              ? [neonRed, neonRed.withValues(alpha: 0.6)]
                              : [neonCyan, holographicBlue],
                            begin: Alignment.topLeft,
                            end: Alignment.bottomRight,
                          ),
                          boxShadow: ModernEffects.neonGlowShadows(color: _recording ? neonRed : neonCyan),
                        ),
                        child: Material(
                          color: Colors.transparent,
                          child: InkWell(
                            onTap: () {},
                            customBorder: const CircleBorder(),
                            child: Center(
                              child: Icon(
                                _recording ? Icons.stop : Icons.mic,
                                size: 44,
                                color: Colors.white,
                              ),
                            ),
                          ),
                        ),
                      ),
                    );
                  },
                ),
              ),
            ),
            const SizedBox(height: 12),
            Text(
              _recording ? 'Recording in progress...' : 'Press & hold to record',
              style: const TextStyle(
                fontSize: 12,
                color: Colors.white54,
                fontStyle: FontStyle.italic,
              ),
            ),
            const SizedBox(height: 24),

            // Action buttons
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                _buildModernButton(
                  label: 'Enroll User',
                  icon: Icons.person_add,
                  onPressed: _showEnrollDialog,
                ),
                _buildModernButton(
                  label: 'Check ASR',
                  icon: Icons.check_circle,
                  onPressed: () async {
                    try {
                      final res = await service.parseIntent(text: 'health check');
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(content: Text('ASR: ${res['ok'] ?? 'OK'}')),
                      );
                    } catch (e) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(content: Text('ASR Error: $e')),
                      );
                    }
                  },
                ),
              ],
            ),
            const SizedBox(height: 24),

            // Recent commands
            if (_recentCommands.isNotEmpty) ...[
              Row(
                children: [
                  const Icon(Icons.history, color: Colors.white70, size: 18),
                  const SizedBox(width: 8),
                  Text(
                    'Recent Commands (${_recentCommands.length})',
                    style: Theme.of(context).textTheme.titleSmall?.copyWith(
                      color: Colors.white,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              ListView.builder(
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                itemCount: _recentCommands.length,
                itemBuilder: (ctx, i) => _buildCommandCard(_recentCommands[i], i),
              ),
            ] else
              Container(
                padding: const EdgeInsets.all(16),
                decoration: ModernEffects.glassCard(hasGlow: false),
                child: Center(
                  child: Column(
                    children: [
                      Icon(
                        Icons.mic_none,
                        size: 32,
                        color: Colors.white30,
                      ),
                      const SizedBox(height: 8),
                      const Text(
                        'No commands recorded yet',
                        style: TextStyle(
                          color: Colors.white54,
                          fontSize: 12,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildModernButton({
    required String label,
    required IconData icon,
    required VoidCallback onPressed,
  }) {
    return Container(
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [neonCyan.withValues(alpha: 0.3), holographicBlue.withValues(alpha: 0.3)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        border: Border.all(color: neonCyan.withValues(alpha: 0.5), width: 1),
        borderRadius: BorderRadius.circular(8),
        boxShadow: ModernEffects.neonGlowShadows(color: neonCyan),
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: onPressed,
          borderRadius: BorderRadius.circular(8),
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(icon, size: 16, color: neonCyan),
                const SizedBox(width: 6),
                Text(
                  label,
                  style: const TextStyle(
                    fontSize: 12,
                    color: Colors.white,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildCommandCard(Map<String, dynamic> cmd, int idx) {
    final isVerified = cmd['verified'] == true;
    final intent = cmd['intent']?.toString() ?? 'Unknown';
    final utterance = cmd['utterance']?.toString() ?? '';

    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Container(
        decoration: ModernEffects.glassCard(hasGlow: false),
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Row(
            children: [
              // Verification badge
              Container(
                width: 4,
                height: 56,
                decoration: BoxDecoration(
                  color: isVerified ? quantumGreen : neonOrange,
                  borderRadius: BorderRadius.circular(2),
                  boxShadow: ModernEffects.neonGlowShadows(
                    color: isVerified ? quantumGreen : neonOrange,
                  ),
                ),
              ),
              const SizedBox(width: 12),
              // Content
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      intent,
                      style: const TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                        color: Colors.white,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      utterance,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        fontSize: 11,
                        color: Colors.white70,
                      ),
                    ),
                  ],
                ),
              ),
              // Status badge
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: isVerified ? quantumGreen.withValues(alpha: 0.15) : neonOrange.withValues(alpha: 0.15),
                  border: Border.all(
                    color: isVerified ? quantumGreen : neonOrange,
                    width: 0.5,
                  ),
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(
                      isVerified ? Icons.check_circle : Icons.lock,
                      size: 12,
                      color: isVerified ? quantumGreen : neonOrange,
                    ),
                    const SizedBox(width: 4),
                    Text(
                      isVerified ? 'Verified' : 'Blocked',
                      style: TextStyle(
                        fontSize: 10,
                        fontWeight: FontWeight.bold,
                        color: isVerified ? quantumGreen : neonOrange,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _WavePainter extends CustomPainter {
  final List<double> samples;
  final bool active;

  _WavePainter(this.samples, this.active);

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = active ? Colors.redAccent : Colors.grey.shade400
      ..strokeWidth = 2.0
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round;

    final path = Path();
    final w = size.width / (samples.length - 1);
    for (var i = 0; i < samples.length; i++) {
      final x = i * w;
      final y = size.height / 2 - (samples[i] - 0.5) * size.height;
      if (i == 0) path.moveTo(x, y);
      else path.lineTo(x, y);
    }
    canvas.drawPath(path, paint);
  }

  @override
  bool shouldRepaint(covariant _WavePainter oldDelegate) => oldDelegate.samples != samples || oldDelegate.active != active;
}
