import pytest

from backend.core.tds import packet_inspector


def test_parse_packet_scaffold():
    # If scapy not installed, skip
    if not getattr(packet_inspector, "_HAS_SCAPY", False):
        pytest.skip("scapy not installed in test environment")

    # Build a simple Ethernet/IP/TCP packet using scapy
    from scapy.all import Ether, IP, TCP

    pkt = Ether()/IP(dst="1.2.3.4", src="10.0.0.1")/TCP(sport=1234, dport=80)/b"GET / HTTP/1.1"
    raw = bytes(pkt)
    parsed = packet_inspector.parse_packet(raw)

    assert isinstance(parsed, dict)
    assert parsed.get("l3")
    assert parsed["l3"]["src_ip"] == "10.0.0.1"
    assert parsed["l3"]["dst_ip"] == "1.2.3.4"
    assert parsed.get("l4")
    assert parsed["l4"]["proto"] == "TCP"
    assert b"GET / HTTP/1.1" in parsed["payload"]
