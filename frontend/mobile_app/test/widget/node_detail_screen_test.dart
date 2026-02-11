import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import '../lib/screens/node_detail_screen.dart';
import '../lib/services/federation_service.dart';

// Fake FederationService for testing
class FakeFederationService extends FederationService {
  FakeFederationService()
      : super(
          // Create a dummy client; it won't be used since we override the method
          _DummyClient(),
        );

  @override
  Future<Map<String, dynamic>> getNodeDetail(String nodeId, {int limit = 100}) async {
    // Simulate historical data with trends
    final now = DateTime.now();
    final history = <Map<String, dynamic>>[];

    // Generate 20 historical entries with trending health and trust
    for (int i = 0; i < 20; i++) {
      final timestamp = now.subtract(Duration(minutes: 20 - i));
      // Health trending slightly down from 0.95 to 0.85
      final health = 0.95 - (i * 0.005);
      // Trust trending up from 0.80 to 0.90
      final trust = 0.80 + (i * 0.005);

      history.add({
        'timestamp': timestamp.toIso8601String(),
        'node_id': nodeId,
        'sync_health': health,
        'trust_score': trust,
        'last_ledger': 'block-$i',
        'active': true,
      });
    }

    return {
      'ok': true,
      'node_id': nodeId,
      'history': history,
      'total_entries': history.length,
      'stats': {
        'avg_health': 0.90,
        'avg_trust': 0.85,
        'min_health': 0.85,
        'max_health': 0.95,
        'min_trust': 0.80,
        'max_trust': 0.90,
      },
      'timestamp': now.toIso8601String(),
    };
  }
}

class _DummyClient {
  Future<dynamic> get(_) => throw UnimplementedError();
  Future<dynamic> post(_) => throw UnimplementedError();
  Future<dynamic> send(_) => throw UnimplementedError();
}

void main() {
  group('NodeDetailScreen Tests', () {
    testWidgets('NodeDetailScreen displays node information', (WidgetTester tester) async {
      final fakeService = FakeFederationService();

      await tester.pumpWidget(
        MaterialApp(
          home: NodeDetailScreen(
            nodeId: 'node-test-1',
            federationService: fakeService,
          ),
        ),
      );

      // Wait for the future to resolve
      await tester.pumpAndSettle();

      // Verify AppBar title
      expect(find.byType(AppBar), findsOneWidget);
      expect(find.text('Node: node-test-1'), findsOneWidget);

      // Verify Node Information card
      expect(find.text('Node Information'), findsOneWidget);
      expect(find.text('node-test-1'), findsWidgets);
      expect(find.text('History Entries:'), findsOneWidget);
      expect(find.text('20'), findsOneWidget);

      // Verify statistics are displayed
      expect(find.text('Health & Trust Statistics'), findsOneWidget);
      expect(find.text('Avg Health'), findsOneWidget);
      expect(find.text('0.90'), findsWidgets);
      expect(find.text('Avg Trust'), findsOneWidget);
      expect(find.text('0.85'), findsWidgets);
    });

    testWidgets('NodeDetailScreen displays trend charts', (WidgetTester tester) async {
      final fakeService = FakeFederationService();

      await tester.pumpWidget(
        MaterialApp(
          home: NodeDetailScreen(
            nodeId: 'node-test-1',
            federationService: fakeService,
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Verify Trends section exists
      expect(find.text('Trends'), findsOneWidget);
      expect(find.text('Sync Health Trend'), findsOneWidget);
      expect(find.text('Trust Score Trend'), findsOneWidget);

      // Verify CustomPaint widgets are rendered (charts)
      expect(find.byType(CustomPaint), findsWidgets);
    });

    testWidgets('NodeDetailScreen displays recent history', (WidgetTester tester) async {
      final fakeService = FakeFederationService();

      await tester.pumpWidget(
        MaterialApp(
          home: NodeDetailScreen(
            nodeId: 'node-test-1',
            federationService: fakeService,
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Verify Recent History section
      expect(find.text('Recent History'), findsOneWidget);

      // Verify at least some history entries are visible
      expect(find.byType(ListView), findsWidgets);
      expect(find.text('Health:'), findsWidgets);
      expect(find.text('Trust:'), findsWidgets);
    });

    testWidgets('NodeDetailScreen has refresh button', (WidgetTester tester) async {
      final fakeService = FakeFederationService();

      await tester.pumpWidget(
        MaterialApp(
          home: NodeDetailScreen(
            nodeId: 'node-test-1',
            federationService: fakeService,
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Verify floating action button exists
      expect(find.byType(FloatingActionButton), findsOneWidget);
      expect(find.byIcon(Icons.refresh), findsOneWidget);
    });

    testWidgets('NodeDetailScreen refreshes data on FAB tap', (WidgetTester tester) async {
      final fakeService = FakeFederationService();

      await tester.pumpWidget(
        MaterialApp(
          home: NodeDetailScreen(
            nodeId: 'node-test-1',
            federationService: fakeService,
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Tap the refresh button
      await tester.tap(find.byType(FloatingActionButton));
      await tester.pumpAndSettle();

      // Data should still be visible after refresh
      expect(find.text('Node: node-test-1'), findsOneWidget);
      expect(find.text('Avg Health'), findsOneWidget);
    });

    testWidgets('NodeDetailScreen displays statistics correctly', (WidgetTester tester) async {
      final fakeService = FakeFederationService();

      await tester.pumpWidget(
        MaterialApp(
          home: NodeDetailScreen(
            nodeId: 'node-test-1',
            federationService: fakeService,
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Verify all stats are displayed
      expect(find.text('Avg Health'), findsOneWidget);
      expect(find.text('Min Health'), findsOneWidget);
      expect(find.text('Max Health'), findsOneWidget);
      expect(find.text('Avg Trust'), findsOneWidget);
      expect(find.text('Min Trust'), findsOneWidget);
      expect(find.text('Max Trust'), findsOneWidget);

      // Verify stat values
      expect(find.text('0.90'), findsWidgets); // avg_health
      expect(find.text('0.85'), findsWidgets); // min_health and avg_trust
      expect(find.text('0.95'), findsWidgets); // max_health
      expect(find.text('0.80'), findsOneWidget); // min_trust
    });

    testWidgets('NodeDetailScreen handles empty history gracefully', (WidgetTester tester) async {
      // Custom fake service with empty history
      final emptyService = _EmptyHistoryFederationService();

      await tester.pumpWidget(
        MaterialApp(
          home: NodeDetailScreen(
            nodeId: 'node-empty',
            federationService: emptyService,
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Should display error or no data message
      expect(find.text('No history found for node node-empty'), findsOneWidget);
    });

    testWidgets('NodeDetailScreen scrolls through long history', (WidgetTester tester) async {
      final fakeService = FakeFederationService();

      await tester.pumpWidget(
        MaterialApp(
          home: NodeDetailScreen(
            nodeId: 'node-test-1',
            federationService: fakeService,
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Scroll down to see more history entries
      await tester.drag(find.byType(ListView).last, const Offset(0, -500));
      await tester.pumpAndSettle();

      // Should still find the recent history section
      expect(find.text('Recent History'), findsOneWidget);
    });
  });
}

class _EmptyHistoryFederationService extends FakeFederationService {
  @override
  Future<Map<String, dynamic>> getNodeDetail(String nodeId, {int limit = 100}) async {
    throw Exception('No history found for node $nodeId');
  }
}
