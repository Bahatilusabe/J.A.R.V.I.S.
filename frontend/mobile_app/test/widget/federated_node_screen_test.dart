import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import '../lib/screens/federated_node_screen.dart';
import '../lib/services/federation_service.dart';

class FakeFederationService extends FederationService {
  FakeFederationService() : super(null as dynamic);

  @override
  Future<Map<String, dynamic>> getStatus() async {
    return {
      'ok': true,
      'nodes': [
        {'id': 'node-us-1', 'country': 'USA', 'tag': 'us-east', 'sync_health': 0.95, 'trust_score': 0.92, 'last_ledger': 'block-12345', 'last_sync': '2025-11-25T12:00:00Z'},
        {'id': 'node-eu-1', 'country': 'EU', 'tag': 'eu-central', 'sync_health': 0.88, 'trust_score': 0.85, 'last_ledger': 'block-12340', 'last_sync': '2025-11-25T11:55:00Z'},
      ],
      'network_health': 0.915,
      'network_trust': 0.885,
      'total_nodes': 2,
    };
  }

  @override
  Future<Map<String, dynamic>> getModels() async {
    return {
      'ok': true,
      'models': [
        {'id': 'model-v1', 'version': '1.0.0', 'node_id': 'node-us-1', 'created_at': '2025-11-25T12:00:00Z', 'status': 'training'},
        {'id': 'model-v2', 'version': '1.0.1', 'node_id': 'node-eu-1', 'created_at': '2025-11-25T10:00:00Z', 'status': 'aggregated'},
      ],
      'latest_model': {'id': 'model-v1', 'version': '1.0.0', 'node_id': 'node-us-1', 'created_at': '2025-11-25T12:00:00Z', 'status': 'training'},
      'total_models': 2,
    };
  }
}

void main() {
  testWidgets('FederatedNodeScreen shows node list, network stats and model info', (WidgetTester tester) async {
    await tester.pumpWidget(
      MaterialApp(
        home: FederatedNodeScreen(
          client: null as dynamic,
          serviceOverride: FakeFederationService(),
        ),
      ),
    );

    // Wait for initial load
    await tester.pumpAndSettle();

    // Check for network health and trust display
    expect(find.text('Network Health'), findsOneWidget);
    expect(find.text('Network Trust'), findsOneWidget);
    expect(find.textContaining('91.5%'), findsWidgets);  // network health

    // Check for node list
    expect(find.text('Node List'), findsOneWidget);
    expect(find.text('USA (us-east)'), findsOneWidget);
    expect(find.text('EU (eu-central)'), findsOneWidget);

    // Check for health and trust percentages in node tiles
    expect(find.textContaining('95%'), findsWidgets);  // node health
    expect(find.textContaining('92%'), findsWidgets);  // node trust

    // Check for ledger info
    expect(find.text('Ledger: block-12345'), findsOneWidget);
    expect(find.text('Ledger: block-12340'), findsOneWidget);

    // Check for model provenance section
    expect(find.text('Model Provenance'), findsOneWidget);
    expect(find.text('Latest Model'), findsOneWidget);
    expect(find.text('Version: 1.0.0'), findsOneWidget);

    // Check that refresh button exists
    expect(find.byIcon(Icons.refresh), findsWidgets);
  });

  testWidgets('FederatedNodeScreen refresh button works', (WidgetTester tester) async {
    await tester.pumpWidget(
      MaterialApp(
        home: FederatedNodeScreen(
          client: null as dynamic,
          serviceOverride: FakeFederationService(),
        ),
      ),
    );

    await tester.pumpAndSettle();
    
    // Tap refresh
    await tester.tap(find.byIcon(Icons.refresh).first);
    await tester.pumpAndSettle();

    // Verify content still renders after refresh
    expect(find.text('Node List'), findsOneWidget);
    expect(find.text('USA (us-east)'), findsOneWidget);
  });
}
