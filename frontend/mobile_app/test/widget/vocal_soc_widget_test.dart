import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:jarvis_mobile/screens/vocal_soc.dart' show VocalSocScreen;
import 'package:jarvis_mobile/services/vocalsoc_service.dart' show VocalSocService;
import 'package:jarvis_mobile/services/http_client.dart' show AuthenticatedClient;

class FakeService implements VocalSocService {
  FakeService(): super(AuthenticatedClient());

  bool verifyCalled = false;
  bool enrollCalled = false;

  @override
  Future<Map<String, dynamic>> parseIntent({String? text, Uint8List? audioBytes, String? format}) async {
    return {'ok': true, 'text': text ?? 'hello', 'intent': {'intent': 'test.intent', 'confidence': 0.9}};
  }

  @override
  Future<Map<String, dynamic>> verifyIdentity({required Uint8List audioBytes, String? userId}) async {
    verifyCalled = true;
    return {'matched': true, 'score': 0.95};
  }

  @override
  Future<Map<String, dynamic>> enroll({required String userId, required Uint8List audioBytes}) async {
    enrollCalled = true;
    return {'ok': true};
  }

  @override
  dynamic openAsrStream() => throw UnimplementedError();
}

void main() {
  testWidgets('VocalSoc shows intent and confirmation dialog', (WidgetTester tester) async {
    final fake = FakeService();
    await tester.pumpWidget(MaterialApp(home: VocalSocScreen(client: AuthenticatedClient(), serviceOverride: fake)));

    // call the public handler to simulate ASR result
    final state = tester.state(find.byType(VocalSocScreen));
    // ignore analyzer: dynamic call
    // ignore: avoid_dynamic_calls
    (state as dynamic).onAsrResult({'ok': true, 'text': 'open vpn', 'intent': {'intent': 'action.open_vpn', 'confidence': 0.9}});
    await tester.pumpAndSettle();

    expect(find.textContaining('Confirm: action.open_vpn'), findsOneWidget);

    // tap confirm
    await tester.tap(find.text('Confirm'));
    await tester.pumpAndSettle();

    expect(fake.verifyCalled, isTrue);
  });
}
