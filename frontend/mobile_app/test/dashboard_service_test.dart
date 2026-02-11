import 'dart:convert';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import '../lib/services/dashboard_service.dart';

void main() {
  test('getTelemetryHistory returns parsed list', () async {
    final mockClient = MockClient((request) async {
      return http.Response(jsonEncode([{'id': '1', 'message': 'test'}]), 200);
    });

  final results = await DashboardService.getTelemetryHistoryWithClient(limit: 10, client: mockClient);
    expect(results, isA<List>());
    expect(results.length, 1);
    expect(results.first['id'], '1');
  });
}
