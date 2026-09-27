"""Info rails: two narrow pixel canvases that fill the black bars either
side of the letterboxed 160x120 canvas on the 16:9 panel (DECISIONS.md
#20). Drawn every frame over every scene, games included, so a glance at
the deck always gives the time and the state.

Left: clock, date, weather. Right: state, session count, and the two meter
readings as bars. Same pixel scale and CRT pass as the main canvas, see
ui.render.compose_output.
"""
from __future__ import annotations

import pygame

from deck.screen import WallClock
from deck.state import State
from deck.ui.gfx import draw_text, get_font
from deck.ui.pixels import pixels_for_state

RAIL_BG = (14, 12, 11)
RULE = (44, 38, 34)
TEXT = (200, 200, 200)
DIM = (130, 130, 130)
ACCENT = (255, 178, 92)

_DAYS = ("MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN")
_MONTHS = ("JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC")

STATE_LABELS = {
    State.READY: "READY",
    State.WORKING: "WORK",
    State.SUBAGENTS: "AGENT",
    State.BLOCKED_PERMISSION: "ASK",
    State.BLOCKED_INPUT: "WAIT",
    State.COMPACTING: "PACK",
    State.DONE: "DONE",
    State.ERROR: "ERR",
    State.IDLE: "IDLE",
    State.OFFLINE: "LINK",
    State.INTERRUPTED: "STOP",
}


def _centered(surf, text: str, y: int, size: int, color) -> None:
    w = get_font(size).size(text)[0]
    draw_text(surf, text, ((surf.get_width() - w) // 2, y), size=size, color=color)


def _rule(surf, y: int) -> None:
    pygame.draw.line(surf, RULE, (3, y), (surf.get_width() - 4, y))


def weather_kind(weather: str) -> str | None:
    """Maps daemon/src/enrich/weather.ts labels onto an icon."""
    text = weather.lower()
    for key, kind in (("storm", "storm"), ("snow", "snow"), ("rain", "rain"), ("drizzle", "rain"),
                      ("shower", "rain"), ("fog", "fog"), ("overcast", "cloud"), ("cloud", "cloud"),
                      ("clear", "sun")):
        if key in text:
            return kind
    return None


def weather_icon(surf, kind: str, cx: int, cy: int) -> None:
    sun, cloud, drop = (240, 210, 90), (200, 200, 210), (120, 160, 230)
    if kind in ("sun", "cloud"):
        if kind == "sun":
            pygame.draw.circle(surf, sun, (cx, cy), 4)
            for dx, dy in ((0, -7), (0, 7), (-7, 0), (7, 0), (-5, -5), (5, 5), (-5, 5), (5, -5)):
                surf.set_at((cx + dx, cy + dy), sun)
            return
        pygame.draw.circle(surf, sun, (cx + 3, cy - 2), 3)
    pygame.draw.circle(surf, cloud, (cx - 3, cy + 1), 3)
    pygame.draw.circle(surf, cloud, (cx + 1, cy - 1), 4)
    pygame.draw.rect(surf, cloud, (cx - 6, cy + 1, 12, 3))
    if kind in ("rain", "storm"):
        for dx in (-4, 0, 4):
            pygame.draw.line(surf, drop, (cx + dx, cy + 6), (cx + dx - 1, cy + 8))
    if kind == "storm":
        pygame.draw.lines(surf, sun, False, [(cx + 1, cy + 4), (cx - 1, cy + 7), (cx + 1, cy + 7), (cx - 1, cy + 10)])
    if kind == "snow":
        for dx in (-4, 0, 4):
            surf.set_at((cx + dx, cy + 7), (235, 235, 235))
    if kind == "fog":
        for dy in (6, 8):
            pygame.draw.line(surf, cloud, (cx - 6, cy + dy), (cx + 6, cy + dy))


def draw_left(surf, clock: WallClock, weather: str | None) -> None:
    surf.fill(RAIL_BG)
    _centered(surf, f"{clock.hour:02d}", 2, 16, ACCENT)
    _centered(surf, f"{clock.minute:02d}", 20, 16, ACCENT)
    _rule(surf, 40)
    _centered(surf, _DAYS[clock.weekday], 44, 8, DIM)
    _centered(surf, str(clock.day), 54, 12, TEXT)
    _centered(surf, _MONTHS[clock.month - 1], 68, 8, DIM)
    if weather:
        _rule(surf, 82)
        kind = weather_kind(weather)
        if kind:
            weather_icon(surf, kind, surf.get_width() // 2, 93)
        temp = weather.split()[0].replace("C", "")
        _centered(surf, temp[:5], 106, 8, TEXT)


def _bar(surf, x: int, label: str, level: float) -> None:
    level = max(0.0, min(1.0, level))
    top, bottom, width = 44, 104, 8
    _centered_at(surf, f"{round(level * 100)}", x + width // 2, top - 9, 6, DIM)
    pygame.draw.rect(surf, RULE, (x, top, width, bottom - top), 1)
    fill = round((bottom - top - 2) * level)
    color = (214, 64, 48) if level >= 0.85 else ACCENT
    if fill:
        pygame.draw.rect(surf, color, (x + 1, bottom - 1 - fill, width - 2, fill))
    _centered_at(surf, label, x + width // 2, bottom + 3, 6, DIM)


def _centered_at(surf, text: str, cx: int, y: int, size: int, color) -> None:
    w = get_font(size).size(text)[0]
    draw_text(surf, text, (cx - w // 2, y), size=size, color=color)


WARN = (214, 64, 48)


def draw_right(
    surf, state: State, now: float, sessions: int, context_pct: float, five_hour_pct: float, wifi_on: bool = False
) -> None:
    surf.fill(RAIL_BG)
    color = pixels_for_state(state, now, 1.0, 1)[0]
    if max(color) < 60:  # IDLE's strip colour is near-black by design; the rail still wants a visible dot
        color = (90, 90, 96)
    cx = surf.get_width() // 2
    pygame.draw.circle(surf, color, (cx, 9), 5)
    _centered(surf, STATE_LABELS.get(state, state.value)[:5], 17, 7, TEXT)
    # WiFi on is the one way the deck has a route out, so it's never hidden:
    # a red frame round the rail, and the tag shares the line with the
    # session count, taking turns every 2s.
    if wifi_on and (not sessions or int(now / 2) % 2 == 0):
        _centered(surf, "WIFI", 26, 7, WARN)
    elif sessions:
        _centered(surf, f"x{sessions}", 26, 7, DIM)
    _rule(surf, 35)
    _bar(surf, 3, "C", context_pct)
    _bar(surf, surf.get_width() - 11, "5H", five_hour_pct)
    if wifi_on:
        pygame.draw.rect(surf, WARN, surf.get_rect(), 1)
