"""Talks to the daemon over the USB point-to-point link.

Two directions, per docs/ARCHITECTURE.md:
  daemon -> Pi:  classified hook events, pushed as they happen (this side
                 runs a small HTTP server on the Pi's link address).
  Pi -> daemon:  button/mech-key events, sent as outbound requests.

A missed heartbeat (no POST from the daemon within HEARTBEAT_TIMEOUT) drives
the LINK lamp dark and takes the deck to OFFLINE via Deck.link_alive.
"""
from __future__ import annotations

import json
import os
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Callable

from deck.state import SessionRegistry

# Real hardware: 10.55.0.1 (Pi) <-> 10.55.0.2 (host), per docs/HARDWARE.md.
# Overridable so the daemon and this firmware can both run on one dev
# machine (e.g. both on 127.0.0.1, different ports) before any hardware
# exists - see README.md's "running the full stack locally" section.
LISTEN_HOST = os.environ.get("DECK_PI_LISTEN_HOST", "10.55.0.1")
LISTEN_PORT = int(os.environ.get("DECK_PI_LISTEN_PORT", "7328"))
DAEMON_HOST = os.environ.get("DECK_DAEMON_HOST", "10.55.0.2")
DAEMON_PORT = int(os.environ.get("DECK_DAEMON_PORT", "7329"))
HEARTBEAT_TIMEOUT = 5.0
ACTION_TIMEOUT = 1.0


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, *args) -> None:  # quiet; the daemon side has the audit log
        pass

    def do_POST(self) -> None:  # noqa: N802 (http.server's naming)
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length) if length else b""
        link: DaemonLink = self.server.link  # type: ignore[attr-defined]
        link._on_request(self.path, body)
        self.send_response(204)
        self.end_headers()


class DaemonLink:
    def __init__(
        self,
        registry: SessionRegistry,
        on_link_alive_change: Callable[[bool], None],
        on_idle_info: Callable[[dict], None] | None = None,
        listen_host: str = LISTEN_HOST,
        listen_port: int = LISTEN_PORT,
        daemon_host: str = DAEMON_HOST,
        daemon_port: int = DAEMON_PORT,
        heartbeat_timeout: float = HEARTBEAT_TIMEOUT,
    ) -> None:
        self.registry = registry
        self.on_link_alive_change = on_link_alive_change
        self.on_idle_info = on_idle_info or (lambda info: None)
        self.listen_host = listen_host
        self.listen_port = listen_port
        self.daemon_host = daemon_host
        self.daemon_port = daemon_port
        self.heartbeat_timeout = heartbeat_timeout

        self._last_seen = 0.0
        self._alive = False
        self._server: ThreadingHTTPServer | None = None
        self._monitor_thread = threading.Thread(target=self._monitor, daemon=True)
        self._stop = threading.Event()

    def start(self) -> None:
        try:
            self._server = ThreadingHTTPServer((self.listen_host, self.listen_port), _Handler)
        except OSError as exc:
            print(
                f"link.py: could not bind {self.listen_host}:{self.listen_port} ({exc.strerror}). "
                "Expected until the USB gadget link is configured, or the env vars are set for "
                "local dev - see README.md. The deck will show OFFLINE until this binds."
            )
            return
        self._server.link = self  # type: ignore[attr-defined]
        threading.Thread(target=self._server.serve_forever, daemon=True).start()
        self._monitor_thread.start()
        print(
            f"link.py: listening on {self.listen_host}:{self.listen_port}, "
            f"sending actions to {self.daemon_host}:{self.daemon_port}"
        )

    def stop(self) -> None:
        self._stop.set()
        if self._server is not None:
            self._server.shutdown()

    def _on_request(self, path: str, body: bytes) -> None:
        self._last_seen = time.monotonic()
        if not self._alive:
            self._alive = True
            self.on_link_alive_change(True)
        if not body:
            return  # bare heartbeat ping
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            return

        if path == "/idle_info":
            self.on_idle_info(payload)
            return
        if path != "/event":
            return
        session_id = payload.get("session_id")
        event = payload.get("event")
        if not session_id or not event:
            return
        meta = payload.get("meta", {})
        self.registry.handle(session_id, event, **meta)

    def _monitor(self) -> None:
        while not self._stop.is_set():
            if self._alive and time.monotonic() - self._last_seen > self.heartbeat_timeout:
                self._alive = False
                self.on_link_alive_change(False)
            time.sleep(0.5)

    def send_action(self, kind: str, **fields) -> None:
        """Fire-and-forget: a slow or dead daemon must never stall the render loop."""

        def _send() -> None:
            body = json.dumps({"kind": kind, **fields}).encode()
            url = f"http://{self.daemon_host}:{self.daemon_port}/action"
            request = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
            try:
                urllib.request.urlopen(request, timeout=ACTION_TIMEOUT)
            except (urllib.error.URLError, TimeoutError, OSError):
                pass

        threading.Thread(target=_send, daemon=True).start()
