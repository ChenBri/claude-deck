#!/usr/bin/env python3
"""Replays a JSONL recording (from tools/record.py) into a live simulator,
at up to --speed x realtime, so every scene and transition gets tuned
against how you actually work.

    python tools/replay.py sessions/2026-09-21.jsonl --speed 10

This is a dev-only stand-in for the daemon's classify.ts: it turns raw
Claude Code hook payloads into the same (session_id, event, meta) calls
DaemonLink would make, using simple heuristics rather than the daemon's real
denylist and scrubbing. Good enough to tune animations; not the safety path.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from deck.main import App, build_panel  # noqa: E402
from deck.menu import Menu  # noqa: E402
from deck.state import Deck  # noqa: E402

_DENYLIST_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in (
        r"\b(psql|mysql|mongosh|redis-cli)\b",
        r"\brm\s+-rf\b",
        r"\bgit\s+(push\s+--force|reset\s+--hard|branch\s+-D)\b",
        r"\bterraform\s+(apply|destroy)\b",
        r"\baws\s+\w+\s+(create|delete|put|update)",
        r"\.env\b|credentials|private[_-]?key",
    )
]


def _is_denylisted(target: str) -> bool:
    return any(p.search(target) for p in _DENYLIST_PATTERNS)


def classify(record: dict) -> tuple[str, str, dict] | None:
    """Raw hook record -> (session_id, event, meta), or None to skip it."""
    hook = record.get("hook")
    payload = record.get("payload", {})
    session_id = payload.get("session_id", "default")

    if hook in (
        "SessionStart", "UserPromptSubmit", "PreCompact", "Stop", "SubagentStop",
    ):
        return session_id, hook, {}

    if hook == "PreToolUse":
        tool = payload.get("tool_name", "")
        tool_input = payload.get("tool_input", {}) or {}
        target = tool_input.get("command") or tool_input.get("file_path") or tool_input.get("path") or ""
        return session_id, hook, {"tool": tool, "target": str(target)[:60]}

    if hook == "PostToolUse":
        tool = payload.get("tool_name", "")
        failed = bool(payload.get("tool_response", {}).get("error")) if isinstance(payload.get("tool_response"), dict) else False
        return session_id, hook, {"tool": tool, "failed": failed}

    if hook == "Notification":
        message = str(payload.get("message", ""))
        tool = payload.get("tool_name", "")
        if tool or "permission" in message.lower():
            target = message[:60]
            return session_id, hook, {
                "variant": "permission",
                "request_id": payload.get("tool_use_id", f"replay-{record.get('recorded_at', 0)}"),
                "tool": tool,
                "target": target,
                "approvable": not _is_denylisted(f"{tool} {target}"),
            }
        return session_id, hook, {"variant": "idle"}

    if hook == "SessionEnd":
        return session_id, hook, {"error": payload.get("reason") == "error"}

    return None


def feed(path: Path, deck: Deck, speed: float) -> None:
    records = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))

    if not records:
        print("nothing to replay")
        return

    base_ts = records[0].get("recorded_at", 0.0)
    start = time.monotonic()
    for record in records:
        target_delay = (record.get("recorded_at", base_ts) - base_ts) / speed
        while time.monotonic() - start < target_delay:
            time.sleep(0.01)
        parsed = classify(record)
        if parsed is None:
            continue
        session_id, event, meta = parsed
        try:
            deck.registry.handle(session_id, event, **meta)
        except Exception as exc:  # a malformed recording must not kill the demo
            print(f"skipped bad record ({event}): {exc}")
    print("replay finished")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("recording", type=Path)
    parser.add_argument("--speed", type=float, default=1.0)
    parser.add_argument("--panel", choices=["sim", "real"], default="sim")
    args = parser.parse_args()

    panel = build_panel(args.panel)
    menu = Menu()
    deck = Deck(selector="ALL", idle_after_seconds=float(menu.settings.get("idle_after_seconds", 300)))
    app = App(panel, deck, menu, use_link=False)

    feeder = threading.Thread(target=feed, args=(args.recording, deck, args.speed), daemon=True)
    feeder.start()
    try:
        app.run()
    finally:
        app.stop()


if __name__ == "__main__":
    main()
