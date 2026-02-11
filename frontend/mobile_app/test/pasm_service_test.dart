import 'dart:convert';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:jarvis_mobile/services/pasm_service.dart';

void main() {
  group('PasmService', () {
    test('getSmallGraph returns nodes', () async {
      final mock = MockClient((req) async {
        expect(req.url.path, contains('/pasm/graph/small'));
        return http.Response(jsonEncode([
          {'id': 'n1', 'label': 'Node 1'},
          {'id': 'n2', 'label': 'Node 2'}
        ]), 200);
      });
      final service = PasmService(client: mock);
      final nodes = await service.getSmallGraph();
      expect(nodes.length, 2);
      expect(nodes[0].id, 'n1');
      expect(nodes[0].label, 'Node 1');
    });

    test('predictForAsset returns paths', () async {
      final mock = MockClient((req) async {
        expect(req.url.path, contains('/pasm/predict'));
        return http.Response(jsonEncode([
          {'nodes': ['n1', 'n2'], 'score': 0.8, 'reason': 'test reason'}
        ]), 200);
      });
      final service = PasmService(client: mock);
      final paths = await service.predictForAsset('asset1');
      expect(paths.length, 1);
      expect(paths[0].nodes, ['n1', 'n2']);
      expect(paths[0].score, 0.8);
      expect(paths[0].reason, 'test reason');
    });

    test('getConfidence returns value', () async {
      final mock = MockClient((req) async {
        expect(req.url.path, contains('/pasm/confidence'));
        return http.Response(jsonEncode({'confidence': 0.95}), 200);
      });
      final service = PasmService(client: mock);
      final conf = await service.getConfidence();
      expect(conf, 0.95);
    });
  });
}
