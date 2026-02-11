import types
import time

from backend.core.tds.vpn_gateway import VPNGateway


class SeqModel:
    def __init__(self, seq):
        self.seq = list(seq)

    def predict(self, X):
        # return next score from sequence, or last one repeatedly
        if self.seq:
            v = self.seq.pop(0)
        else:
            v = 0.0
        return [v]


class FakeWG:
    def __init__(self):
        self.calls = []

    def add_peer(self, peer_name, public_key, allowed_ips):
        self.calls.append((peer_name, public_key, tuple(allowed_ips)))


def test_dynamic_narrow_then_restore(monkeypatch):
    # Ensure OPA consult will approve actions by monkeypatching zero_trust helper
    import backend.core.tds.vpn_gateway as vpn_mod
    vpn_mod.zero_trust = types.SimpleNamespace(
        enforce_microsegmentation=lambda *a, **k: {"allowed": True},
        _evaluate_opa_policy=lambda opa_url, path, inp: {"allowed": True},
    )

    gw = VPNGateway()
    fake = FakeWG()
    gw.wg = fake

    # low threshold for dynamic narrow, restore threshold slightly lower
    gw.policy["dynamic_narrow_threshold"] = 0.5
    gw.policy["dynamic_restore_threshold"] = 0.3

    # model will produce: normal (0.1), anomaly (0.8), anomaly(0.9), normal(0.2), normal(0.1)
    gw.model = SeqModel([0.1, 0.8, 0.9, 0.2, 0.1])

    sid = "sess-int-1"
    gw.create_session(sid)
    gw.sessions[sid]["wg_pubkey"] = "pk-int"
    gw.sessions[sid]["wg_allowed_ips"] = ["10.0.0.0/24"]

    dest = "10.0.0.5"
    plaintext = b"hello"
    blob = gw.encrypt_for_session(sid, plaintext)

    # process five times to consume model sequence
    results = []
    for _ in range(5):
        out = gw.process_incoming(sid, blob, dest_addr=dest)
        results.append(out)
        time.sleep(0.01)

    # After anomalies, WireGuard add_peer should have been called to narrow
    assert any(call for call in fake.calls if call[0] == sid and call[1] == "pk-int"), "expected wg.add_peer calls"

    # Find the first narrowing call allowed-ips (should include dest)
    narrowed = None
    for _, _, allowed in fake.calls:
        if allowed and any(str(dest) in a for a in allowed):
            narrowed = allowed
            break
    assert narrowed is not None, "expected narrowing to dest"

    # Later calls should include restoration to previous allowed-ips (10.0.0.0/24)
    restored = any(tuple(["10.0.0.0/24"]) == call[2] for call in fake.calls)
    assert restored, f"expected restoration call to 10.0.0.0/24, calls: {fake.calls}"
