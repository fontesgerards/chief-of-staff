"""Optional localhost write-back server for the decision dashboard (U3).

Used only on hosts whose config.md runtime row verifies `script_exec`. Serves the
one rendered dashboard and turns each click into an append to
`decisions-<date>.jsonl` — so the principal gets a true one-click round-trip
instead of the export-file fallback. Absence of this server is a fully supported
mode (render.py + Export); this just removes the manual step.

Hard boundaries (KTD5):
  - binds 127.0.0.1 on an ephemeral port — loopback only, never a network listener;
  - serves exactly one dashboard and writes only under queue/review/;
  - performs NO outward action — the outbound gate remains the only send path;
  - refuses to start unless COS_SCRIPT_EXEC_VERIFIED=1 (the skill sets this only
    after matching the live host's verified capability row).

stdlib only.
"""
from __future__ import annotations

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
import render as render_mod  # noqa: E402


def _make_handler(instance_dir, date):
    decisions_path = Path(instance_dir) / "queue" / "review" / f"decisions-{date}.jsonl"
    state = {"running": True}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *a):  # quiet — the skill relays status, not access logs
            pass

        def _send(self, code, body=b"", ctype="text/plain; charset=utf-8"):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            if body:
                self.wfile.write(body)

        def do_GET(self):
            if self.path in ("/", "/index.html"):
                html = render_mod.render(
                    instance_dir, date,
                    server_post="/decision", server_done="/done",
                ).encode("utf-8")
                self._send(200, html, "text/html; charset=utf-8")
            else:
                self._send(404)

        def do_POST(self):
            if self.path == "/done":
                self._send(204)
                state["running"] = False
                return
            if self.path != "/decision":
                self._send(404)
                return
            try:
                length = int(self.headers.get("Content-Length", 0))
                raw = self.rfile.read(length) if length else b""
                obj = json.loads(raw.decode("utf-8"))
                if not isinstance(obj, dict) or not obj.get("card_id") or not obj.get("decision"):
                    raise ValueError("decision needs card_id + decision")
            except (ValueError, json.JSONDecodeError) as e:
                self._send(400, f"bad decision: {e}".encode("utf-8"))
                return
            decisions_path.parent.mkdir(parents=True, exist_ok=True)
            with decisions_path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(obj, ensure_ascii=False) + "\n")  # append-only (R5)
            self._send(204)

    return Handler, state


def serve(instance_dir, date, host="127.0.0.1", port=0):
    if os.environ.get("COS_SCRIPT_EXEC_VERIFIED") != "1":
        sys.exit("refusing to start: COS_SCRIPT_EXEC_VERIFIED != 1 "
                 "(host's runtime row does not verify script_exec)")
    handler, state = _make_handler(instance_dir, date)
    httpd = ThreadingHTTPServer((host, port), handler)
    bound = httpd.server_address
    print(f"http://{bound[0]}:{bound[1]}/", flush=True)  # skill relays this URL
    try:
        while state["running"]:
            httpd.handle_request()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="localhost write-back server for the dashboard")
    ap.add_argument("instance_dir")
    ap.add_argument("date")
    ap.add_argument("--port", type=int, default=0)
    args = ap.parse_args()
    serve(args.instance_dir, args.date, port=args.port)
