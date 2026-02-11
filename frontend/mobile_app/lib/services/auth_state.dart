import 'dart:async';

/// Simple singleton to broadcast authentication state changes across the app.
class AuthState {
  AuthState._internal();
  static final AuthState instance = AuthState._internal();

  final StreamController<bool> _controller = StreamController<bool>.broadcast();

  /// Stream of logged-in state. `true` = logged in, `false` = logged out.
  Stream<bool> get onAuthChanged => _controller.stream;

  void setLoggedIn(bool v) {
    try {
      _controller.add(v);
    } catch (_) {}
  }

  void dispose() {
    _controller.close();
  }
}
