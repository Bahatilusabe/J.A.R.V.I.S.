"""
Packet inspection helpers using Scapy.

Provides parse_packet(raw_bytes) -> dict which extracts L2/L3/L4 headers and payload.
Falls back to minimal parsing if Scapy isn't available.
"""
from typing import Dict, Any

try:
    from scapy.all import Ether, IP, IPv6, TCP, UDP
    _HAS_SCAPY = True
except Exception:
    _HAS_SCAPY = False


def parse_packet(raw: bytes) -> Dict[str, Any]:
    """Parse raw packet bytes into a dictionary of fields.

    Returns a dict with keys: l2 (dict), l3 (dict), l4 (dict), payload (bytes)
    """
    if _HAS_SCAPY:
        try:
            eth = Ether(raw)
        except Exception:
            return {"error": "scapy_parse_error"}

        result = {"l2": {}, "l3": {}, "l4": {}, "payload": b""}

        # L2
        result["l2"]["src_mac"] = eth.src if hasattr(eth, "src") else None
        result["l2"]["dst_mac"] = eth.dst if hasattr(eth, "dst") else None
        result["l2"]["type"] = eth.type if hasattr(eth, "type") else None

        # L3
        if IP in eth:
            ip = eth[IP]
            result["l3"] = {
                "version": 4,
                "src_ip": ip.src,
                "dst_ip": ip.dst,
                "proto": ip.proto,
                "ihl": ip.ihl,
                "ttl": ip.ttl,
            }
            payload_layer = ip.payload
        elif IPv6 in eth:
            ip6 = eth[IPv6]
            result["l3"] = {
                "version": 6,
                "src_ip": ip6.src,
                "dst_ip": ip6.dst,
                "nh": ip6.nh,
                "hlim": ip6.hlim,
            }
            payload_layer = ip6.payload
        else:
            # no IP
            result["payload"] = bytes(eth.payload)
            return result

        # L4
        if TCP in payload_layer:
            tcp = payload_layer[TCP]
            result["l4"] = {
                "proto": "TCP",
                "src_port": tcp.sport,
                "dst_port": tcp.dport,
                "flags": str(tcp.flags),
            }
            result["payload"] = bytes(tcp.payload)
        elif UDP in payload_layer:
            udp = payload_layer[UDP]
            result["l4"] = {
                "proto": "UDP",
                "src_port": udp.sport,
                "dst_port": udp.dport,
            }
            result["payload"] = bytes(udp.payload)
        else:
            # other L4 or no transport
            result["payload"] = bytes(payload_layer)

        return result

    # Fallback minimal parser: try to find IPv4/TCP headers by offsets
    res = {"l2": {}, "l3": {}, "l4": {}, "payload": raw}
    return res


if __name__ == "__main__":
    # quick CLI demo
    import sys
    if len(sys.argv) < 2:
        print("Usage: packet_inspector.py <hex-packet-file>")
        sys.exit(1)
    path = sys.argv[1]
    with open(path, "rb") as f:
        raw = f.read()
    print(parse_packet(raw))
