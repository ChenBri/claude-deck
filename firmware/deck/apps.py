"""Registry of apps reachable from the home screen. Add an entry here to
add an app - the launcher (ui/scenes/home.py) and main.py's navigation
pick it up automatically. Games are drawn through ui/render.py's GAMES
map; "settings" is special-cased since it draws the settings list, not a
Scene.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AppDef:
    id: str
    label: str
    icon: str  # one glyph, since there's no room for real icon art yet


APPS: list[AppDef] = [
    AppDef("settings", "Settings", "@"),
    AppDef("snake", "Snake", "S"),
    AppDef("tetris", "Tetris", "T"),
]
