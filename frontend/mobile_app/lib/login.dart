import 'package:flutter/material.dart';
import 'package:local_auth/local_auth.dart';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'services/auth_service.dart';

class LoginPage extends StatefulWidget {
  const LoginPage({super.key});

  @override
  State<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends State<LoginPage> {
  final _localAuth = LocalAuthentication();
  bool _busy = false;
  String _status = '';

  Future<void> _startLogin() async {
    setState(() {
      _busy = true;
      _status = 'Starting handshake...';
    });
    final deviceId = 'device-${DateTime.now().millisecondsSinceEpoch}';
    final tInitStart = DateTime.now();
    print('[login] initHandshake start: $tInitStart');
    final init = await AuthService.initHandshake(deviceId);
    final tInitEnd = DateTime.now();
    print('[login] initHandshake end: $tInitEnd, duration_ms=${tInitEnd.difference(tInitStart).inMilliseconds}');
    if (init == null) {
      setState(() {
        _status = 'Handshake init failed';
        _busy = false;
      });
      return;
    }
    final hid = init['handshake_id'] as String;
    setState(() => _status = 'Prompting biometric...');

    bool didAuthenticate = false;
    if (kIsWeb) {
      // local_auth isn't supported on web — simulate a very short prompt for dev
      // runs so the handshake flow proceeds and timing prints are visible when
      // running in Chrome. Keep this minimal to avoid perceived slowness.
      final tPromptStart = DateTime.now();
      print('[login] local_auth (simulated) prompt start: $tPromptStart');
      // minimal simulated delay to mimic a near-instant biometric prompt
      await Future.delayed(const Duration(milliseconds: 10));
      final tPromptEnd = DateTime.now();
      print('[login] local_auth (simulated) prompt end: $tPromptEnd, duration_ms=${tPromptEnd.difference(tPromptStart).inMilliseconds}');
      didAuthenticate = true;
    } else {
      try {
        final tPromptStart = DateTime.now();
        print('[login] local_auth prompt start: $tPromptStart');
        didAuthenticate = await _localAuth.authenticate(
          localizedReason: 'Authenticate to unlock your J.A.R.V.I.S. session',
          options: const AuthenticationOptions(biometricOnly: true),
        );
        final tPromptEnd = DateTime.now();
        print('[login] local_auth prompt end: $tPromptEnd, duration_ms=${tPromptEnd.difference(tPromptStart).inMilliseconds}');
      } catch (e) {
        // fallthrough
      }
    }

    if (!didAuthenticate) {
      setState(() {
        _status = 'Biometric auth failed';
        _busy = false;
      });
      return;
    }

    // In production, obtain a real biometric attestation token. For dev we send a placeholder.
    final bioToken = 'dev-biom';
    setState(() => _status = 'Verifying biometric...');
  final tVerifyStart = DateTime.now();
  print('[login] verifyBiometric start: $tVerifyStart');
  final ok = await AuthService.verifyBiometric(hid, bioToken);
  final tVerifyEnd = DateTime.now();
  print('[login] verifyBiometric end: $tVerifyEnd, duration_ms=${tVerifyEnd.difference(tVerifyStart).inMilliseconds}');
    if (!ok) {
      setState(() {
        _status = 'Biometric verification failed';
        _busy = false;
      });
      return;
    }

    setState(() => _status = 'Requesting session token...');
  final tSessionStart = DateTime.now();
  print('[login] createSession start: $tSessionStart');
  final token = await AuthService.createSession(hid);
  final tSessionEnd = DateTime.now();
  print('[login] createSession end: $tSessionEnd, duration_ms=${tSessionEnd.difference(tSessionStart).inMilliseconds}');
    if (token == null) {
      setState(() {
        _status = 'Session creation failed';
        _busy = false;
      });
      return;
    }

    setState(() {
      _status = 'Secure session established';
      _busy = false;
    });
    // Navigate to home
    if (mounted) Navigator.of(context).pushReplacementNamed('/home');
  }

  Future<void> _demoLogin() async {
    // Demo mode: skip backend and go straight to home
    await AuthService.setStoredToken('demo-token-${DateTime.now().millisecondsSinceEpoch}');
    if (mounted) Navigator.of(context).pushReplacementNamed('/home');
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Login — J.A.R.V.I.S.')),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            Text(_status, style: const TextStyle(fontSize: 16)),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: _busy ? null : _startLogin,
              child: _busy ? const CircularProgressIndicator() : const Text('Unlock with biometrics'),
            ),
            const SizedBox(height: 12),
            ElevatedButton(
              onPressed: _busy ? null : _demoLogin,
              style: ElevatedButton.styleFrom(backgroundColor: Colors.grey),
              child: const Text('Demo Mode (Skip Login)'),
            ),
          ]),
        ),
      ),
    );
  }
}
