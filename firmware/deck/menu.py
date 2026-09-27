"""Settings, one of the apps reachable from the home screen. Regexes cannot
be typed on a knob, so the menu only flips booleans and steps numbers; it
writes /var/deck/settings.yaml, which is where the real regex patterns for
the denylist categories live, hand-edited, not through this menu.

main.py owns whether Settings is currently showing (App.current_app ==
"settings"); this class only tracks which row is focused and applies
changes, matching how the other apps (games) don't know whether they're
on screen either.
"""
from __future__ import annotations

import copy
import os
from dataclasses import dataclass
from pathlib import Path

import yaml

from deck.audio.chiptune import DEFAULT_THEME, THEMES
from deck.calibration import default_curve
from deck.panel.base import METERS

DEFAULT_SETTINGS_PATH = Path(os.environ.get("DECK_VAR", "./var/deck")) / "settings.yaml"

DEFAULT_SETTINGS = {
    "idle_after_seconds": 300,
    "denylist": {
        "database": True,
        "destructive_fs_git": True,
        "infrastructure": True,
        "secrets": True,
    },
    "wifi": False,
    "night_brightness": 0.2,
    "sound_theme": DEFAULT_THEME,
    "night_screen": 0.4,
    "quiet_hours": True,
    "quiet_start": 1,
    "quiet_end": 8,
    "meter_cal": {m: default_curve() for m in METERS},
}


@dataclass
class MenuItem:
    key: str  # dotted path into settings, or an action name ("EXIT", "HWTEST", "CALIBRATE")
    label: str
    kind: str  # "action" | "bool" | "int" | "float" | "choice"
    step: float = 1
    minimum: float = 0
    maximum: float = 1
    choices: tuple[str, ...] = ()


ITEMS = [
    MenuItem("EXIT", "back to apps", "action"),
    MenuItem("idle_after_seconds", "idle timeout (s)", "int", step=30, minimum=60, maximum=1800),
    MenuItem("denylist.database", "block: database", "bool"),
    MenuItem("denylist.destructive_fs_git", "block: fs/git", "bool"),
    MenuItem("denylist.infrastructure", "block: infra", "bool"),
    MenuItem("denylist.secrets", "block: secrets", "bool"),
    MenuItem("wifi", "wifi radio", "bool"),
    MenuItem("night_brightness", "night brightness", "float", step=0.05, minimum=0.0, maximum=1.0),
    MenuItem("night_screen", "night screen", "float", step=0.05, minimum=0.05, maximum=1.0),
    MenuItem("quiet_hours", "quiet hours", "bool"),
    MenuItem("quiet_start", "quiet from (h)", "int", step=1, minimum=0, maximum=23),
    MenuItem("quiet_end", "quiet until (h)", "int", step=1, minimum=0, maximum=23),
    MenuItem("sound_theme", "sounds", "choice", choices=tuple(THEMES)),
    MenuItem("HWTEST", "hardware test", "action"),
    MenuItem("CALIBRATE", "calibrate meters", "action"),
]


def _get(settings: dict, dotted_key: str):
    node = settings
    *parts, last = dotted_key.split(".")
    for part in parts:
        node = node[part]
    return node[last]


def _set(settings: dict, dotted_key: str, value) -> None:
    node = settings
    *parts, last = dotted_key.split(".")
    for part in parts:
        node = node[part]
    node[last] = value


class Menu:
    def __init__(self, settings_path: Path = DEFAULT_SETTINGS_PATH) -> None:
        self.settings_path = Path(settings_path)
        self.settings = self._load()
        self.focus = 0

    def _load(self) -> dict:
        if self.settings_path.exists():
            with open(self.settings_path) as f:
                loaded = yaml.safe_load(f) or {}
            return {**copy.deepcopy(DEFAULT_SETTINGS), **loaded}
        return copy.deepcopy(DEFAULT_SETTINGS)

    def save(self) -> None:
        self._save()

    def _save(self) -> None:
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.settings_path, "w") as f:
            yaml.safe_dump(self.settings, f)

    def current_item(self) -> MenuItem:
        return ITEMS[self.focus]

    def current_value(self):
        item = self.current_item()
        return None if item.kind == "action" else _get(self.settings, item.key)

    def rotate(self, direction: int) -> None:
        self.focus = (self.focus + direction) % len(ITEMS)

    def activate(self) -> None:
        """Encoder push while Settings is showing: act on the focused item.
        Action items are intercepted by main.py before this is called."""
        item = self.current_item()
        if item.kind == "choice":
            current = _get(self.settings, item.key)
            index = item.choices.index(current) if current in item.choices else -1
            _set(self.settings, item.key, item.choices[(index + 1) % len(item.choices)])
            self._save()
        elif item.kind == "bool":
            _set(self.settings, item.key, not _get(self.settings, item.key))
            self._save()
        elif item.kind in ("int", "float"):  # push steps through the range, then wraps
            value = _get(self.settings, item.key) + item.step
            if value > item.maximum:
                value = item.minimum
            _set(self.settings, item.key, round(value, 2))
            self._save()
