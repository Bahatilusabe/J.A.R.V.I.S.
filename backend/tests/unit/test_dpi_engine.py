import threading
import time
import os

from backend.core.tds.dpi_engine import DpiEngine, send_packet_to_socket


def test_dpi_engine_basic(tmp_path):
    # run socket in repository run/ directory inside tmp_path
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    socket_path = str(run_dir / "jarvis_dpi.sock")

    # small signature set (inline)
    sigs = [(10, b"attacker"), (20, b"magic")]
    engine = DpiEngine(socket_path=socket_path, signatures=sigs)
    engine.start()
    time.sleep(0.05)

    # packet without signatures -> accept
    pkt1 = b"hello benign packet"
    r1 = send_packet_to_socket(pkt1, socket_path=socket_path)
    assert r1.get("verdict") == "accept"

    # packet with signature
    pkt2 = b"payload contains attacker inside"
    r2 = send_packet_to_socket(pkt2, socket_path=socket_path)
    assert r2.get("verdict") == "drop"
    assert 10 in r2.get("matches")

    engine.stop()
    time.sleep(0.01)
