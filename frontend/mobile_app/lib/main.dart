import 'package:flutter/material.dart';
import 'dart:async';
import 'services/auth_service.dart';
import 'services/auth_state.dart';
import 'login.dart';
import 'home_dashboard.dart' show HomeDashboardUpgrade;
import 'real_time_feed.dart';
import 'screens/assets_screen.dart';
import 'screens/pasm_screen.dart';
import 'screens/ced_view.dart';
import 'screens/vocal_soc.dart';
import 'screens/self_healing_screen.dart';
import 'screens/federated_node_screen.dart';
import 'screens/forensics_view.dart';
import 'screens/alert_demo_screen.dart';
import 'services/http_client.dart';
import 'theme.dart';
import 'screens/mobile_shell.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'screens/incident_detail_screen.dart';
import 'screens/attack_view.dart';

void main() {
  runApp(const JarvisApp());
}

class JarvisApp extends StatefulWidget {
  const JarvisApp({super.key});

  @override
  State<JarvisApp> createState() => _JarvisAppState();
}

class _JarvisAppState extends State<JarvisApp> {
  final GlobalKey<NavigatorState> _navKey = GlobalKey<NavigatorState>();
  late final StreamSubscription<bool> _authSub;

  @override
  void initState() {
    super.initState();
    _authSub = AuthState.instance.onAuthChanged.listen((loggedIn) {
      if (!loggedIn) {
        // clear navigation stack and go to login
        _navKey.currentState?.pushNamedAndRemoveUntil('/login', (route) => false);
      } else {
        _navKey.currentState?.pushNamedAndRemoveUntil('/home', (route) => false);
      }
    });
  }

  @override
  void dispose() {
    _authSub.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return ProviderScope(
      child: MaterialApp(
      navigatorKey: _navKey,
      title: 'J.A.R.V.I.S. Mobile',
      theme: jarvisTheme,
      routes: {
        '/home': (c) => const MobileShell(),
        '/login': (c) => const LoginPage(),
        '/feed': (c) => const RealTimeFeed(),
        '/assets': (c) => const AssetsScreen(),
        '/pasm': (c) => const PasmScreen(),
        '/ced': (c) => const CedView(),
        '/vocal': (c) => VocalSocScreen(client: AuthenticatedClient()),
        '/attack': (c) => const AttackView(),
        '/forensics': (c) => const ForensicsView(),
        '/alerts': (c) => const AlertDemoScreen(),
        '/self_healing': (c) => SelfHealingScreen(client: AuthenticatedClient()),
        '/federation': (c) => FederatedNodeScreen(client: AuthenticatedClient()),
        '/incident': (c) => const _IncidentDetailRoute(),
      },
      home: FutureBuilder<String?>(
        future: AuthService.getStoredToken(),
        builder: (context, snap) {
          if (snap.connectionState != ConnectionState.done) return const SizedBox();
          if (snap.hasData && snap.data != null) return const HomeDashboardUpgrade();
          return const LoginPage();
        },
      ),
      ),
    );
  }
}

// Helper route widget to extract incidentId from arguments
class _IncidentDetailRoute extends StatelessWidget {
  // ignore: unused_element
  const _IncidentDetailRoute({super.key});
  @override
  Widget build(BuildContext context) {
    final args = ModalRoute.of(context)?.settings.arguments;
    final id = args is String ? args : null;
    if (id == null) return const Scaffold(body: Center(child: Text('No incident id')));
    return IncidentDetailScreen(incidentId: id);
  }
}

