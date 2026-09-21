#!/usr/bin/env python3
"""Captures live Claude Code hook events into JSONL, for replay into the
simulator before the daemon exists (docs/BUILD.md phase 0, step 1).

Binds the same 127.0.0.1:7327 address hooks/emit.js posts to, so it's a
drop-in stand-in for the daemon's hook-ingest endpoint. Run this, use Claude
Code normally for a while, then feed the file to tools/replay.py.

    python tools/record.py --out sessions/2026-09-21.jsonl
"""
from __future__ import annotations

import argparse
import json
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

DEFAULT_PORT = 7327


def make_handler(out_path: Path):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args) -> None:
            pass

        def do_POST(self) -> None:  # noqa: N802
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length) if length else b"{}"
            try:
                payload = json.loads(body)
            except json.JSONDecodeError:
                payload = {"raw": body.decode(errors="replace")}
            payload["recorded_at"] = time.time()
            with open(out_path, "a") as f:
                f.write(json.dumps(payload) + "\n")
            print(f"recorded {payload.get('hook', '?')}")
            self.send_response(204)
            self.end_headers()

    return Handler


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("sessions") / f"{time.strftime('%Y-%m-%d')}.jsonl")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(args.out))
    print(f"recording hook events to {args.out}, listening on 127.0.0.1:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
