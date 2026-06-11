"""Serve tests drive the request handler through in-memory streams (a fake
connection) rather than a real TCP socket, so they run under a network-blocked
sandbox and assert the same do_GET/do_POST behavior."""
import json
from io import BytesIO

import serve as serve_mod


class _FakeConn:
    """Stands in for a socket: rfile feeds the request, wfile captures the response."""
    def __init__(self, request_bytes):
        self.rfile = BytesIO(request_bytes)
        self.wfile = BytesIO()

    def makefile(self, mode, *a, **k):
        return self.rfile if "r" in mode else self.wfile

    def sendall(self, b):
        self.wfile.write(b)

    def close(self):
        pass


class _FakeServer:
    server_address = ("127.0.0.1", 0)


def _request(inst, date, raw):
    """Run one HTTP/1.0 request through the handler; return (status_code, body_bytes)."""
    handler_cls, state = serve_mod._make_handler(inst, date)
    conn = _FakeConn(raw)
    handler_cls(conn, ("127.0.0.1", 0), _FakeServer())   # __init__ handles the request
    resp = conn.wfile.getvalue()
    status_line, _, rest = resp.partition(b"\r\n")
    code = int(status_line.split(b" ")[1])
    body = rest.split(b"\r\n\r\n", 1)[1] if b"\r\n\r\n" in rest else b""
    return code, body, state


def _post(path, payload):
    body = json.dumps(payload).encode() if payload is not None else b""
    return (f"POST {path} HTTP/1.0\r\nContent-Type: application/json\r\n"
            f"Content-Length: {len(body)}\r\n\r\n").encode() + body


def _instance(tmp_path):
    inst = tmp_path / "instance"
    (inst / "queue" / "review").mkdir(parents=True)
    return inst


def test_post_decision_appends_one_line(tmp_path):
    inst = _instance(tmp_path)
    code, _, _ = _request(inst, "2026-06-11", _post("/decision",
                          {"card_id": "outbound:p1", "decision": "send"}))
    assert code == 204
    code, _, _ = _request(inst, "2026-06-11", _post("/decision",
                          {"card_id": "outbound:p2", "decision": "reject"}))
    assert code == 204
    lines = (inst / "queue" / "review" / "decisions-2026-06-11.jsonl").read_text().splitlines()
    assert [json.loads(l)["card_id"] for l in lines] == ["outbound:p1", "outbound:p2"]


def test_malformed_post_is_rejected_no_write(tmp_path):
    inst = _instance(tmp_path)
    raw = (b"POST /decision HTTP/1.0\r\nContent-Type: application/json\r\n"
           b"Content-Length: 4\r\n\r\n{bad")
    code, _, _ = _request(inst, "2026-06-11", raw)
    assert code == 400
    assert not (inst / "queue" / "review" / "decisions-2026-06-11.jsonl").exists()


def test_missing_required_fields_rejected(tmp_path):
    inst = _instance(tmp_path)
    code, _, _ = _request(inst, "2026-06-11", _post("/decision", {"card_id": "x"}))  # no decision
    assert code == 400
    assert not (inst / "queue" / "review" / "decisions-2026-06-11.jsonl").exists()


def test_done_flips_running_flag(tmp_path):
    inst = _instance(tmp_path)
    code, _, state = _request(inst, "2026-06-11", _post("/done", None))
    assert code == 204
    assert state["running"] is False


def test_get_root_serves_dashboard_in_live_mode(tmp_path):
    inst = _instance(tmp_path)
    code, body, _ = _request(inst, "2026-06-11", b"GET / HTTP/1.0\r\n\r\n")
    assert code == 200
    text = body.decode()
    assert "<!doctype html>" in text
    assert "__REVIEW_POST__" in text   # served with the live banner + POST endpoint


def test_unknown_path_404(tmp_path):
    inst = _instance(tmp_path)
    code, _, _ = _request(inst, "2026-06-11", b"GET /nope HTTP/1.0\r\n\r\n")
    assert code == 404
