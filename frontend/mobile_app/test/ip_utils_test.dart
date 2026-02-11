import 'package:flutter_test/flutter_test.dart';
import 'package:jarvis_mobile/utils/ip_utils.dart';

void main() {
  group('IP utils', () {
    test('isValidIp accepts IPv4 and IPv6', () {
      expect(isValidIp('192.168.1.1'), isTrue);
      expect(isValidIp('255.255.255.255'), isTrue);
      expect(isValidIp('::1'), isTrue);
      expect(isValidIp('2001:0db8:85a3:0000:0000:8a2e:0370:7334'), isTrue);
      expect(isValidIp('not an ip'), isFalse);
      expect(isValidIp('256.256.256.256'), isFalse);
    });

    test('normalizeIp returns canonical form', () {
      expect(normalizeIp('192.168.001.001'), '192.168.1.1');
      // IPv6 compressed form expected
      expect(normalizeIp('0:0:0:0:0:0:0:1'), '::1');
    });

    test('extractAllIpsFromIncident finds ips in fields and timeline', () {
      final incident = {
        'source_ip': '10.0.0.5',
        'timeline': [
          {'message': 'Connection from 8.8.8.8 established'},
          'Suspicious traffic to 2001:db8::1 seen',
        ]
      };
      final ips = extractAllIpsFromIncident(incident);
      expect(ips, containsAll(['10.0.0.5', '8.8.8.8', '2001:db8::1']));
    });
  });
}
