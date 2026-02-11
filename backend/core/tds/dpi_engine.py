"""
User-space DPI engine daemon and kernel-hook shim.

Design summary
--------------
- The kernel hook driver (or a kernel-mode test harness) will connect to the UNIX domain socket
  `./run/jarvis_dpi.sock` and send raw packet frames. Each packet is framed as a 4-byte big-endian
  length followed by the packet bytes.
- The DPI daemon performs signature-based matching (simple multi-pattern search) and returns a JSON
  verdict for each packet: {"verdict": "accept"|"drop", "matches": [ids]}.
- This is intentionally a small, easily auditable shim that a kernel hook can call synchronously.

Notes / next steps
------------------
- Replace the naive matching with Aho–Corasick or an NPU offload path when moving from prototype to
  production. The Ascend matcher can be plugged via the `AscendPatternMatcher` if the Ascend feature
  is enabled in the DPI Rust service and exposed via shared library calls.

This module exposes a CLI and a Python API to start/stop the daemon and to run a single packet through
the engine (useful for unit tests and integration tests).
"""

import os
import errno
import socket
import struct
import threading
import json
import time
from typing import List, Tuple, Dict

# Try to import Aho-Corasick implementations in order of preference:
# 1) pyahocorasick (fast C extension)
# 2) ahocorapy (pure-Python fallback)
# If neither is available, fall back to naive matching.
_AHO_IMPL = None
try:
    try:
        import ahocorasick as _pyahoc  # pyahocorasick
    except Exception:  # pragma: no cover - optional dependency
        _pyahoc = None  # type: ignore
    _AHO_IMPL = "pyahocorasick"
except Exception:
    try:
        # ahocorapy KeywordTree
        try:
            from ahocorapy.keywordtree import KeywordTree as _KeywordTree
        except Exception:  # pragma: no cover - optional dependency
            _KeywordTree = None  # type: ignore
        _AHO_IMPL = "ahocorapy"
    except Exception:
        _AHO_IMPL = None

SIGNATURES_PATH = os.path.join(os.path.dirname(__file__), "../../../config/dpi_signatures.txt")
SOCKET_PATH = os.path.join(os.path.dirname(__file__), "../../../../run/jarvis_dpi.sock")
 
# Optional packet inspector (Scapy-based)
try:
    from .packet_inspector import parse_packet
    _HAS_PACKET_INSPECTOR = True
except Exception:
    _HAS_PACKET_INSPECTOR = False


def load_signatures(path: str = SIGNATURES_PATH) -> List[Tuple[int, bytes]]:
    """Load signature file. Each line: id:hex-or-ascii

    Example:
      1:badpattern
      2:deadbeef (if you want hex, prefix with 0x or use raw ASCII)
    """
    sigs: List[Tuple[int, bytes]] = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for ln in f:
                ln = ln.strip()
                if not ln or ln.startswith("#"):
                    continue
                if ":" not in ln:
                    continue
                sid_str, pat = ln.split(":", 1)
                sid = int(sid_str.strip())
                pat = pat.strip()
                # support hex literal 0x...
                if pat.startswith("0x"):
                    b = bytes.fromhex(pat[2:])
                else:
                    b = pat.encode("utf-8")
                sigs.append((sid, b))
    except FileNotFoundError:
        # empty list if file missing; daemon still runs
        sigs = []
    return sigs


class DpiEngine:
    def __init__(self, socket_path: str = SOCKET_PATH, signatures: List[Tuple[int, bytes]] = None):
        self.socket_path = socket_path
        self.signatures = signatures if signatures is not None else load_signatures()
        self._server = None
        self._running = threading.Event()
        self._lock = threading.Lock()
        self._use_automaton = False
        self._automaton = None
        # Prepare automaton if an Aho implementation is available
        if _AHO_IMPL and self.signatures:
            try:
                if _AHO_IMPL == "pyahocorasick":
                    A = _pyahoc.Automaton()
                    # pyahocorasick expects strings. Use latin-1 to preserve raw bytes 1:1
                    for sid, pat in self.signatures:
                        if not pat:
                            continue
                        key = pat.decode("latin-1")
                        # store sid and pattern length so we can compute match offsets later
                        A.add_word(key, (sid, len(key)))
                    A.make_automaton()
                    self._automaton = A
                    self._use_automaton = True
                elif _AHO_IMPL == "ahocorapy":
                    # build KeywordTree with mapping from word->(sid,length)
                    tree = _KeywordTree()
                    for sid, pat in self.signatures:
                        if not pat:
                            continue
                        key = pat.decode("latin-1")
                        tree.add(key)
                    tree.finalize()
                    self._automaton = tree
                    self._use_automaton = True
            except Exception:
                # fallback to naive
                self._use_automaton = False

    def match_packet(self, packet: bytes) -> dict:
        """Return a dict with 'matches' and optional 'match_details'.

        The return value is always a dict when using an automaton and contains:
          - 'matches': list of signature ids
          - 'match_details': list of {sid, start, end} (when available)

        When automaton is not available, falls back to naive search but still returns
        both keys for consistency.
        """
        matches: List[int] = []
        match_details: List[Dict[str, int]] = []

        if self._use_automaton and self._automaton is not None:
            pkt_str = packet.decode("latin-1", errors="ignore")
            ids = set()
            try:
                if _AHO_IMPL == "pyahocorasick":
                    for end_idx, val in self._automaton.iter(pkt_str):
                        try:
                            sid, pat_len = val
                        except Exception:
                            sid = val
                            pat_len = None
                        end = end_idx
                        if pat_len is not None:
                            start = end - pat_len + 1
                            matched = pkt_str[start : end + 1]
                        else:
                            start = None
                            # best-effort: use end index only
                            matched = pkt_str[: end + 1]
                        # store matched bytes as latin-1 string for JSON safety
                        match_details.append({"sid": sid, "start": start, "end": end, "match": matched})
                        ids.add(sid)
                elif _AHO_IMPL == "ahocorapy":
                    # ahocorapy yields (start, end, word)
                    for start_idx, end_idx, word in self._automaton.iter(pkt_str):
                        # word is the matched string; use it directly as match
                        for sid, pat in self.signatures:
                            if pat == word.encode("latin-1"):
                                match_details.append({"sid": sid, "start": start_idx, "end": end_idx, "match": word})
                                ids.add(sid)
                else:
                    # Unknown implementation
                    self._use_automaton = False
            except Exception:
                # on any failure, disable automaton and fall through to naive
                self._use_automaton = False
            matches = sorted(ids)

        if not self._use_automaton:
            # naive fallback: simple substring search
            for sid, pat in self.signatures:
                if not pat:
                    continue
                idx = packet.find(pat)
                if idx != -1:
                    matches.append(sid)
                    matched = pat.decode("latin-1", errors="ignore")
                    match_details.append({"sid": sid, "start": idx, "end": idx + len(pat) - 1, "match": matched})

        return {"matches": matches, "match_details": match_details}

    def verdict_for_packet(self, packet: bytes) -> dict:
        matches = self.match_packet(packet)
        # Normalize match output: match_packet may return a dict with ids+details or a simple list
        match_ids = []
        match_details = None
        if isinstance(matches, dict):
            match_ids = matches.get("matches", [])
            match_details = matches.get("match_details")
        elif isinstance(matches, list):
            match_ids = matches

        verdict = {"verdict": "drop" if match_ids else "accept", "matches": match_ids}
        if match_details is not None:
            verdict["match_details"] = match_details
        # Add parsed metadata when packet inspector is available
        if _HAS_PACKET_INSPECTOR:
            try:
                meta = parse_packet(packet)
                verdict["meta"] = meta
            except Exception:
                verdict["meta_error"] = "parse_failed"
        return verdict

    def start(self):
        """Start daemon listening on the UNIX domain socket (blocking in a thread)."""
        # Ensure run directory exists
        run_dir = os.path.dirname(self.socket_path)
        os.makedirs(run_dir, exist_ok=True)
        # Remove old socket if present
        try:
            if os.path.exists(self.socket_path):
                os.unlink(self.socket_path)
        except Exception:
            pass

        srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        # Try to bind to the requested socket path. On some platforms (macOS)
        # UNIX socket paths can be too long (OSError: AF_UNIX path too long). In
        # that case, create a shorter socket in /tmp and place a symlink at the
        # requested path that points to the short socket so callers using the
        # original path still connect.
        try:
            srv.bind(self.socket_path)
            actual_socket_path = self.socket_path
            used_symlink = False
        except OSError as e:
            # macOS raises OSError with message 'AF_UNIX path too long'
            if e.errno == errno.ENAMETOOLONG or "AF_UNIX path too long" in str(e):
                short_dir = "/tmp"
                short_name = f"jarvis_dpi_{os.getpid()}_{int(time.time()*1000)}.sock"
                short_path = os.path.join(short_dir, short_name)
                # ensure any existing short socket removed
                try:
                    if os.path.exists(short_path):
                        os.unlink(short_path)
                except Exception:
                    pass
                srv.bind(short_path)
                actual_socket_path = short_path
                # create parent dir for requested path then create a symlink
                try:
                    os.makedirs(os.path.dirname(self.socket_path), exist_ok=True)
                    # if requested path exists, remove it first
                    if os.path.lexists(self.socket_path):
                        try:
                            os.unlink(self.socket_path)
                        except Exception:
                            pass
                    os.symlink(short_path, self.socket_path)
                    used_symlink = True
                except Exception:
                    # if symlink creation fails, keep going with short_path but callers
                    # attempting to connect to the original path will fail.
                    used_symlink = False
                # write a small helper file so clients that cannot connect to the long
                # AF_UNIX path (due to OS path length limits) can locate the actual
                # short socket path. We write it to a sidecar file at the requested
                # path + '.realpath'. Tests and helpers will check for this file.
                try:
                    mapping_file = self.socket_path + ".realpath"
                    with open(mapping_file, "w", encoding="utf-8") as mf:
                        mf.write(short_path)
                except Exception:
                    pass
            else:
                raise
        srv.listen(4)
        self._server = srv
        self._running.set()

        def serve_loop():
            while self._running.is_set():
                try:
                    conn, _ = srv.accept()
                    threading.Thread(target=self._handle_conn, args=(conn,), daemon=True).start()
                except Exception:
                    time.sleep(0.01)

        threading.Thread(target=serve_loop, daemon=True).start()

    def stop(self):
        self._running.clear()
        try:
            if self._server:
                self._server.close()
        except Exception:
            pass
        try:
            if os.path.exists(self.socket_path):
                os.unlink(self.socket_path)
        except Exception:
            pass

    def _handle_conn(self, conn: socket.socket):
        with conn:
            try:
                # read 4-byte length big-endian
                hdr = conn.recv(4)
                if len(hdr) < 4:
                    return
                (l,) = struct.unpack(">I", hdr)
                data = b""
                to_read = l
                while to_read > 0:
                    chunk = conn.recv(to_read)
                    if not chunk:
                        break
                    data += chunk
                    to_read -= len(chunk)

                result = self.verdict_for_packet(data)

                # Ensure the verdict is JSON-serializable: convert bytes to latin-1
                def _make_jsonable(o):
                    if isinstance(o, bytes):
                        try:
                            return o.decode("latin-1")
                        except Exception:
                            return repr(o)
                    if isinstance(o, dict):
                        return {k: _make_jsonable(v) for k, v in o.items()}
                    if isinstance(o, list):
                        return [_make_jsonable(v) for v in o]
                    return o

                safe_result = _make_jsonable(result)
                conn.sendall(json.dumps(safe_result).encode("utf-8"))
            except Exception as e:
                try:
                    conn.sendall(json.dumps({"error": str(e)}).encode("utf-8"))
                except Exception:
                    pass


def send_packet_to_socket(packet: bytes, socket_path: str = SOCKET_PATH, timeout: float = 2.0) -> dict:
    """Helper used by tests or a kernel-harness: send one framed packet and receive JSON verdict."""
    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client.settimeout(timeout)
    # Some platforms impose strict length limits on AF_UNIX paths. If a helper
    # mapping file exists at socket_path + '.realpath', use the mapped short
    # path instead of the possibly-too-long requested path.
    mapped = None
    try:
        mapping_file = socket_path + ".realpath"
        if os.path.exists(mapping_file):
            with open(mapping_file, "r", encoding="utf-8") as mf:
                mapped = mf.read().strip()
    except Exception:
        mapped = None

    try:
        client.connect(mapped or socket_path)
        hdr = struct.pack(">I", len(packet))
        client.sendall(hdr + packet)
        # read response
        resp = b""
        while True:
            chunk = client.recv(4096)
            if not chunk:
                break
            resp += chunk
        if not resp:
            return {"error": "no_response"}
        return json.loads(resp.decode("utf-8"))
    finally:
        client.close()


if __name__ == "__main__":
    # CLI: start daemon in foreground
    engine = DpiEngine()
    print(f"Starting DPI daemon on socket: {engine.socket_path}")
    engine.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping DPI daemon")
        engine.stop()
