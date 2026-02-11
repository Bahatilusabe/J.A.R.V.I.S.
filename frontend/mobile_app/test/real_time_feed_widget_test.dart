import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import '../lib/real_time_feed.dart';

void main() {
  testWidgets('RealTimeFeed displays provided initial alerts', (WidgetTester tester) async {
    final sample = [
      {'id': 'a1', 'asset': 'host-1', 'description': 'Test alert', 'severity': 'high', 'pasm_probability': 0.85, 'timestamp': DateTime.now().toIso8601String()},
    ];

    await tester.pumpWidget(MaterialApp(home: RealTimeFeed(initialAlerts: sample)));
    await tester.pumpAndSettle();

    expect(find.text('host-1'), findsOneWidget);
    expect(find.text('Test alert'), findsOneWidget);
    expect(find.text('Open Incident'), findsOneWidget);
  });
}
