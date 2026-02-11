/// Lightweight IP utilities implemented without `dart:io` so they work on web.
/// These use regex-based validation and normalization suitable for UI tasks.

/// Validate IPv4 and IPv6 using conservative regexes.
bool isValidIp(String ip) {
  final s = ip.trim();
  if (s.isEmpty) return false;
  final ipv4 = RegExp(r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}\$');
  final ipv6 = RegExp(r'^[0-9a-fA-F:]{2,}\$');
  if (ipv4.hasMatch(s)) {
    // quick numeric range check for IPv4 octets
    final parts = s.split('.');
    for (final p in parts) {
      final v = int.tryParse(p);
      if (v == null || v < 0 || v > 255) return false;
    }
    return true;
  }
  if (ipv6.hasMatch(s)) return true;
  return false;
}

String normalizeIp(String ip) => ip.trim();

List<String> extractAllIpsFromIncident(Map<String, dynamic>? incident) {
  final List<String> found = [];
  if (incident == null) return found;
  try {
    for (final key in ['target_ip', 'source_ip', 'attacker_ip', 'ip']) {
      if (incident.containsKey(key) && incident[key] != null) {
        final v = incident[key].toString().trim();
        if (isValidIp(v)) {
          final norm = normalizeIp(v);
          if (!found.contains(norm)) found.add(norm);
        }
      }
    }

    final timeline = incident['timeline'];
    if (timeline is List) {
      final ipRegex = RegExp(r"\b(?:(?:[0-9]{1,3}\.){3}[0-9]{1,3})\b|\b[0-9a-fA-F:]{2,}\b");
      for (final e in timeline) {
        final text = e is Map ? (e['message'] ?? e['description'] ?? e.toString()) : e.toString();
        for (final m in ipRegex.allMatches(text.toString())) {
          final candidate = m.group(0)!.trim();
          if (!isValidIp(candidate)) continue;
          final norm = normalizeIp(candidate);
          if (!found.contains(norm)) found.add(norm);
        }
      }
    }
  } catch (_) {}
  return found;
}
