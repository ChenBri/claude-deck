"""Ambient data cards, one full 160x120 screen each. Every card reads only
the daemon's idle payload (scrubbed on the PC like everything else), and
`available()` says which ones have data, so an empty card never shows.

The rails already carry the time, date, weather and both meters at a
glance; the cards are the longer look at the same things.
"""
from __future__ import annotations

import pygame

from deck.screen import WallClock
from deck.ui.gfx import clear, draw_text, get_font
from deck.ui.rails import weather_icon, weather_kind

TITLE = (224, 122, 42)
TEXT = (230, 230, 230)
DIM = (140, 140, 140)
ACCENT = (255, 178, 92)
GOOD = (120, 200, 140)
WARN = (240, 210, 90)
BAD = (214, 64, 48)

_DAY_NAMES = ("MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY")
_MONTH_NAMES = ("JANUARY", "FEBRUARY", "MARCH", "APRIL", "MAY", "JUNE", "JULY", "AUGUST",
                "SEPTEMBER", "OCTOBER", "NOVEMBER", "DECEMBER")


def available(info: dict) -> set[str]:
    found = {"clock"}
    if info.get("weather"):
        found.add("weather")
    if isinstance(info.get("today"), dict):
        found.add("usage")
    if info.get("git"):
        found.add("git")
    series = info.get("five_hour_series")
    if isinstance(series, list) and series and any(v > 0 for v in series):
        found.add("five_hour")
    return found


def _centered(canvas, text: str, y: int, size: int, color) -> None:
    w = get_font(size).size(text)[0]
    draw_text(canvas, text, ((canvas.get_width() - w) // 2, y), size=size, color=color)


def _title(canvas, text: str) -> None:
    draw_text(canvas, text, (6, 4), size=9, color=TITLE)
    pygame.draw.line(canvas, (44, 38, 34), (6, 16), (canvas.get_width() - 7, 16))


def _greeting(hour: int) -> str:
    if 5 <= hour < 12:
        return "good morning"
    if 12 <= hour < 18:
        return "good afternoon"
    if 18 <= hour < 23:
        return "good evening"
    return "late night"


def draw_clock(canvas, info: dict, clock: WallClock, now: float) -> None:
    clear(canvas)
    greeting = _greeting(clock.hour)
    name = info.get("name")
    _centered(canvas, f"{greeting}, {name}" if name else greeting, 14, 8, DIM)
    colon = ":" if int(now) % 2 == 0 else " "
    _centered(canvas, f"{clock.hour:02d}{colon}{clock.minute:02d}", 32, 36, ACCENT)
    _centered(canvas, f"{_DAY_NAMES[clock.weekday]} {clock.day} {_MONTH_NAMES[clock.month - 1]}", 82, 8, TEXT)
    # day progress, a quiet sense of where the day is
    frac = (clock.hour * 60 + clock.minute) / (24 * 60)
    pygame.draw.rect(canvas, (44, 38, 34), (20, 100, 120, 3))
    pygame.draw.rect(canvas, (120, 84, 48), (20, 100, round(120 * frac), 3))


def draw_weather(canvas, info: dict, clock: WallClock, now: float) -> None:
    clear(canvas)
    _title(canvas, "WEATHER")
    weather = str(info.get("weather", ""))
    parts = weather.split(maxsplit=1)
    temp = parts[0].replace("C", "") if parts else ""
    label = parts[1] if len(parts) > 1 else ""
    kind = weather_kind(weather)
    if kind:
        icon = pygame.Surface((24, 24), pygame.SRCALPHA)
        weather_icon(icon, kind, 12, 10)
        canvas.blit(pygame.transform.scale(icon, (72, 72)), (8, 26))
    draw_text(canvas, temp, (84, 40), size=28, color=TEXT)
    if label:
        draw_text(canvas, label[:16], (84, 76), size=8, color=DIM)


def _human(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}k"
    return str(n)


def draw_usage(canvas, info: dict, clock: WallClock, now: float) -> None:
    clear(canvas)
    _title(canvas, "TODAY")
    today = info.get("today", {})
    rows = [
        ("sessions", _human(int(today.get("sessions", 0))), TEXT),
        ("tool calls", _human(int(today.get("tool_calls", 0))), TEXT),
        ("approved", _human(int(today.get("approved", 0))), GOOD),
        ("denied", _human(int(today.get("denied", 0))), BAD if today.get("denied") else DIM),
        ("turns", _human(int(today.get("turns", 0))), TEXT),
        ("tokens out", _human(int(today.get("output_tokens", 0))), ACCENT),
    ]
    y = 22
    for label, value, color in rows:
        draw_text(canvas, label, (10, y + 2), size=8, color=DIM)
        w = get_font(11).size(value)[0]
        draw_text(canvas, value, (canvas.get_width() - 10 - w, y), size=11, color=color)
        y += 15


def draw_git(canvas, info: dict, clock: WallClock, now: float) -> None:
    clear(canvas)
    _title(canvas, "GIT")
    # daemon/src/enrich/git.ts: "<branch line>, N changed" or "<branch line>, clean",
    # where the branch line is git's own "branch...upstream [ahead 1]"
    status = str(info.get("git", ""))
    branch_line, _, tail = status.rpartition(", ")
    if not branch_line:
        branch_line, tail = status, ""
    branch, _, tracking = branch_line.partition("...")
    upstream, _, ahead_behind = tracking.partition(" ")
    _centered(canvas, branch[:18], 30, 16, ACCENT)
    if upstream:
        _centered(canvas, f"-> {upstream}"[:28], 54, 7, DIM)
    if ahead_behind:
        _centered(canvas, ahead_behind.strip("[]")[:28], 66, 8, WARN)
    if tail:
        _centered(canvas, tail, 86, 11, GOOD if tail == "clean" else WARN)


def draw_five_hour(canvas, info: dict, clock: WallClock, now: float) -> None:
    clear(canvas)
    _title(canvas, "LAST 5 HOURS")
    pct = float(info.get("five_hour_pct", 0.0))
    label = f"{round(pct * 100)}%"
    w = get_font(9).size(label)[0]
    draw_text(canvas, label, (canvas.get_width() - 7 - w, 4), size=9, color=BAD if pct >= 0.85 else ACCENT)

    series = [float(v) for v in info.get("five_hour_series", [])]
    left, right, top, bottom = 10, canvas.get_width() - 10, 26, 100
    even = 1.0 / max(len(series), 1)  # each bucket's share if the budget burned evenly
    ceiling = max(even * 1.5, max(series, default=0.0))
    slot = (right - left) / max(len(series), 1)
    for i, value in enumerate(series):
        height = round((bottom - top) * value / ceiling) if ceiling else 0
        color = BAD if value > even * 1.5 else ACCENT if value > even else (160, 110, 60)
        pygame.draw.rect(canvas, color, (round(left + i * slot) + 1, bottom - height, max(round(slot) - 2, 1), height))
    even_y = bottom - round((bottom - top) * even / ceiling)
    for x in range(left, right, 4):
        pygame.draw.line(canvas, DIM, (x, even_y), (x + 1, even_y))
    pygame.draw.line(canvas, (70, 64, 60), (left, bottom), (right, bottom))
    draw_text(canvas, "-5h", (left, bottom + 3), size=7, color=DIM)
    draw_text(canvas, "even pace", (left + 1, even_y - 9), size=6, color=DIM)
    now_w = get_font(7).size("now")[0]
    draw_text(canvas, "now", (right - now_w, bottom + 3), size=7, color=DIM)


_CARDS = {
    "clock": draw_clock,
    "weather": draw_weather,
    "usage": draw_usage,
    "git": draw_git,
    "five_hour": draw_five_hour,
}


def draw_card(name: str, canvas, info: dict, clock: WallClock, now: float) -> None:
    _CARDS.get(name, draw_clock)(canvas, info, clock, now)
