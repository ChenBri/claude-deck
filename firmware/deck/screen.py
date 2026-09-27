"""Whole-screen brightness: NIGHT dimming and quiet-hours blanking. Pure
logic; main.py passes the result to Panel.present as screen_level.

Blanking only ever happens in a calm state. Anything that wants you
(BLOCKED, ERROR, INTERRUPTED) or shows live work lights the screen
regardless of the hour, and any touch of the panel wakes it for a while.
Lamps and LEDs are not affected here: NIGHT already governs those.

The deck has no RTC and no route to the internet, so wall-clock time comes
from the daemon's idle_info when it has sent one, and only falls back to
the deck's own clock (right on the desktop sim, possibly wrong on the
board) when it hasn't.
"""
from __future__ import annotations

import time
from dataclasses import dataclass

from deck.state import State

WAKE_SECONDS = 180.0
CALM_STATES = {State.READY, State.DONE, State.IDLE, State.OFFLINE}


@dataclass(frozen=True)
class WallClock:
    hour: int
    minute: int
    year: int
    month: int
    day: int

    @property
    def weekday(self) -> int:
        """0 = Monday."""
        return time.strptime(f"{self.year}-{self.month}-{self.day}", "%Y-%m-%d").tm_wday


def wall_clock(idle_info: dict, fallback: time.struct_time | None = None) -> WallClock:
    local = fallback or time.localtime()
    hour, minute = local.tm_hour, local.tm_min
    year, month, day = local.tm_year, local.tm_mon, local.tm_mday
    try:
        h, m = str(idle_info["clock"]).split(":")
        hour, minute = int(h), int(m)
    except (KeyError, ValueError):
        pass
    try:
        y, mo, d = str(idle_info["date"]).split("-")
        year, month, day = int(y), int(mo), int(d)
    except (KeyError, ValueError):
        pass
    return WallClock(hour % 24, minute % 60, year, month, day)


def in_quiet_hours(hour: int, start: int, end: int) -> bool:
    """[start, end) in local hours, wrapping past midnight. start == end is off."""
    if start == end:
        return False
    if start < end:
        return start <= hour < end
    return hour >= start or hour < end


def screen_level(state: State, hour: int, night_on: bool, since_input: float, settings: dict) -> float:
    if (
        settings.get("quiet_hours", True)
        and state in CALM_STATES
        and since_input >= WAKE_SECONDS
        and in_quiet_hours(hour, int(settings.get("quiet_start", 1)), int(settings.get("quiet_end", 8)))
    ):
        return 0.0
    if night_on:
        return max(0.0, min(1.0, float(settings.get("night_screen", 0.4))))
    return 1.0
