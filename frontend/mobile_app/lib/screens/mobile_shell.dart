import 'package:flutter/material.dart';
import '../home_dashboard.dart';
import '../real_time_feed.dart';
import '../screens/pasm_screen.dart';
import '../screens/ced_view.dart';
import '../screens/forensics_view.dart';

class MobileShell extends StatefulWidget {
  const MobileShell({super.key});

  @override
  State<MobileShell> createState() => _MobileShellState();
}

class _MobileShellState extends State<MobileShell> {
  int _idx = 0;

  static final List<Widget> _pages = <Widget>[
    const HomeDashboardUpgrade(),
    const RealTimeFeed(),
    const PasmScreen(),
    const CedView(),
    // Vocalsoc uses constructor requiring client; we rely on existing route wiring for full page
    // Use simple stub to keep bottom nav functional on web
    const _StubScreen(title: 'VocalSOC'),
    const ForensicsView(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: _pages[_idx],
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _idx,
        type: BottomNavigationBarType.fixed,
        backgroundColor: Theme.of(context).appBarTheme.backgroundColor,
        selectedItemColor: Theme.of(context).colorScheme.primary,
        unselectedItemColor: Colors.white54,
        onTap: (i) => setState(() => _idx = i),
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.dashboard), label: 'Dashboard'),
          BottomNavigationBarItem(icon: Icon(Icons.rss_feed), label: 'Feed'),
          BottomNavigationBarItem(icon: Icon(Icons.timeline), label: 'PASM'),
          BottomNavigationBarItem(icon: Icon(Icons.explore), label: 'CED'),
          BottomNavigationBarItem(icon: Icon(Icons.mic), label: 'Vocal'),
          BottomNavigationBarItem(icon: Icon(Icons.book), label: 'Forensics'),
        ],
      ),
    );
  }
}

class _StubScreen extends StatelessWidget {
  final String title;
  // ignore: unused_element
  const _StubScreen({required this.title, super.key});
  @override
  Widget build(BuildContext context) {
    return Scaffold(appBar: AppBar(title: Text(title)), body: Center(child: Text('$title placeholder')));
  }
}
