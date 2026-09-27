"""Per-game high score table, one shared file. Mirrors deck.menu's
settings.yaml pattern: same DECK_VAR root, same load-then-save-on-change
shape, module-level state like deck.audio.chiptune rather than a class,
since games are built with no constructor args (see ui/render.py's
SceneManager._get) and have nowhere to receive an instance.
"""
from __future__ import annotations

import os
from pathlib import Path

import yaml

DEFAULT_SCORES_PATH = Path(os.environ.get("DECK_VAR", "./var/deck")) / "scores.yaml"
TOP_N = 5

_path = DEFAULT_SCORES_PATH
_boards: dict[str, list[dict]] | None = None


def _load() -> dict[str, list[dict]]:
    if _path.exists():
        with open(_path) as f:
            return yaml.safe_load(f) or {}
    return {}


def _ensure_loaded() -> dict[str, list[dict]]:
    global _boards
    if _boards is None:
        _boards = _load()
    return _boards


def _save() -> None:
    _path.parent.mkdir(parents=True, exist_ok=True)
    with open(_path, "w") as f:
        yaml.safe_dump(_boards, f)


def top(game: str, n: int = TOP_N) -> list[tuple[str, int]]:
    boards = _ensure_loaded()
    entries = boards.get(game, [])
    return [(e["name"], e["score"]) for e in entries[:n]]


def qualifies(game: str, score: int, n: int = TOP_N) -> bool:
    if score <= 0:
        return False
    boards = _ensure_loaded()
    entries = boards.get(game, [])
    return len(entries) < n or score > entries[-1]["score"]


def add(game: str, name: str, score: int, n: int = TOP_N) -> None:
    boards = _ensure_loaded()
    entries = boards.setdefault(game, [])
    entries.append({"name": name, "score": score})
    entries.sort(key=lambda e: e["score"], reverse=True)
    del entries[n:]
    _save()
