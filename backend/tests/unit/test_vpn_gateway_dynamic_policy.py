import os
import types

from backend.core.tds.vpn_gateway import VPNGateway


class FakeWG:
    def __init__(self):
        self.calls = []

    def add_peer(self, peer_name, public_key, allowed_ips):
        self.calls.append((peer_name, public_key, tuple(allowed_ips)))


class FakeModel:
    def __init__(self, score=0.99):
        self._score = score

    def predict(self, X):
        # return a list-like
        return [self._score]


def test_dynamic_narrowing_applies(monkeypatch):
    # Ensure WG integration is off by env default
    monkeypatch.delenv("JARVIS_USE_WIREGUARD", raising=False)

    gw = VPNGateway()

    # attach fake WireGuard manager
    fake = FakeWG()
    gw.wg = fake

    # set dynamic threshold low so our fake model triggers
    gw.policy["dynamic_narrow_threshold"] = 0.5

    # install fake model that returns high anomaly score
    gw.model = FakeModel(score=0.99)

    # ensure module-level zero_trust does not block microsegmentation check
    import backend.core.tds.vpn_gateway as vpn_mod
    vpn_mod.zero_trust = types.SimpleNamespace(enforce_microsegmentation=lambda *a, **k: {"allowed": True})

    sid = "sess-ai-1"
    gw.create_session(sid)

    # set session wg info
    gw.sessions[sid]["wg_pubkey"] = "pk-test"
    gw.sessions[sid]["wg_allowed_ips"] = ["10.0.0.0/24"]

    # build a blob for the session
    plaintext = b"probe"
    blob = gw.encrypt_for_session(sid, plaintext)

    # process incoming with a destination that should be narrowed
    dest = "10.0.0.5"
    out = gw.process_incoming(sid, blob, dest_addr=dest)

    # verify model produced an anomaly score and dynamic policy applied
    assert "anomaly_score" in out
    assert fake.calls, "expected WireGuard add_peer to be called"
    peer_name, pub, allowed = fake.calls[-1]
    assert peer_name == sid
    assert pub == "pk-test"
    # allowed-ips should have been narrowed to the dest with /32
    assert allowed[0].startswith(dest)
