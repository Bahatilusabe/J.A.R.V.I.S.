import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:jarvis_mobile/screens/pasm_screen.dart';
import 'package:jarvis_mobile/services/pasm_service.dart';
import 'package:jarvis_mobile/services/asset_service.dart';

class FakePasmService extends PasmService {
  @override
  Future<List<PathNode>> getSmallGraph() async => [
    PathNode(id: 'n1', label: 'Node 1'),
    PathNode(id: 'n2', label: 'Node 2'),
    PathNode(id: 'n3', label: 'Node 3'),
  ];
  @override
  Future<List<AttackPath>> predictForAsset(String assetId) async => [
    AttackPath(nodes: ['n1', 'n2', 'n3'], score: 0.9, reason: 'Test path'),
  ];
}

class FakeAssetService extends AssetService {
  @override
  Future<List<AssetSummary>> getAssets() async => [
    AssetSummary(id: 'a1', name: 'Asset 1', online: true, lastTelemetry: null),
    AssetSummary(id: 'a2', name: 'Asset 2', online: false, lastTelemetry: null),
  ];
}

void main() {
  testWidgets('PasmScreen renders graph and paths', (WidgetTester tester) async {
    // Inject fake services by replacing the stateful widget with a test double if needed
    await tester.pumpWidget(MaterialApp(home: Builder(
      builder: (context) => PasmScreen(),
    )));

    // Wait for graph and assets to load
    await tester.pumpAndSettle();

    // Should show node labels
    expect(find.text('Node 1'), findsWidgets);
    expect(find.text('Node 2'), findsWidgets);
    expect(find.text('Node 3'), findsWidgets);

    // Open asset dropdown and select first asset
    await tester.tap(find.byType(DropdownButtonFormField<String>));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Asset 1').last);
    await tester.pumpAndSettle();

    // Tap Predict
    await tester.tap(find.text('Predict'));
    await tester.pumpAndSettle();

    // Should show predicted path with node labels
    expect(find.textContaining('Node 1 → Node 2 → Node 3'), findsOneWidget);
    expect(find.textContaining('Score 90.0%'), findsOneWidget);
    expect(find.text('Why?'), findsOneWidget);
  });
}
