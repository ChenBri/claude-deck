"""Mascot life: what the mascot gets up to during ambient mode, picked by
the local hour. One small room, lit and furnished differently through the
day: coffee in the morning, wandering around midday, reading in the
afternoon, watching the sky in the evening, asleep at night.

Everything is drawn from ctx.now, no per-scene state, so leaving and
re-entering ambient mode never leaves an animation half-finished.
"""
from __future__ import annotations

import math

import pygame

from deck.screen import WallClock
from deck.ui import sprites
from deck.ui.gfx import draw_text
from deck.ui.scenes.base import Context

W, H = 160, 120
FLOOR_Y = 92
WINDOW = pygame.Rect(104, 12, 44, 40)
TABLE = pygame.Rect(36, 82, 68, 4)

# (start hour, vignette); the last one wraps past midnight
_SCHEDULE = ((6, "coffee"), (11, "wander"), (15, "reading"), (19, "window"), (23, "sleep"))

_ROOM = {
    # wall, floor, sky
    "coffee": ((52, 40, 32), (70, 48, 34), (150, 186, 214)),
    "wander": ((56, 44, 34), (74, 52, 36), (130, 176, 222)),
    "reading": ((50, 36, 30), (66, 44, 32), (214, 150, 96)),
    "window": ((30, 24, 28), (40, 30, 28), (22, 30, 64)),
    "sleep": ((16, 14, 20), (22, 18, 20), (10, 14, 34)),
}


def vignette_for_hour(hour: int) -> str:
    current = _SCHEDULE[-1][1]
    for start, name in _SCHEDULE:
        if hour >= start:
            current = name
    return current


def _twinkle(i: int, now: float) -> bool:
    return math.sin(now * (0.7 + (i * 37 % 11) / 10) + i * 1.9) > -0.3


def _room(canvas, name: str, now: float) -> None:
    wall, floor, sky = _ROOM[name]
    canvas.fill(wall)
    pygame.draw.rect(canvas, floor, (0, FLOOR_Y, W, H - FLOOR_Y))
    pygame.draw.line(canvas, tuple(max(0, c - 16) for c in floor), (0, FLOOR_Y), (W, FLOOR_Y))

    pygame.draw.rect(canvas, sky, WINDOW)
    if name in ("window", "sleep"):
        for i in range(9):
            x = WINDOW.x + 3 + (i * 17) % (WINDOW.width - 6)
            y = WINDOW.y + 3 + (i * 11) % (WINDOW.height - 10)
            if _twinkle(i, now):
                canvas.set_at((x, y), (230, 230, 200))
        canvas.blit(sprites.moon(), (WINDOW.right - 22, WINDOW.y + 4))
    frame = (24, 18, 16)
    pygame.draw.rect(canvas, frame, WINDOW, 2)
    pygame.draw.line(canvas, frame, (WINDOW.centerx, WINDOW.y), (WINDOW.centerx, WINDOW.bottom - 1), 2)
    pygame.draw.line(canvas, frame, (WINDOW.x, WINDOW.centery), (WINDOW.right - 1, WINDOW.centery), 2)
    pygame.draw.rect(canvas, frame, (WINDOW.x - 3, WINDOW.bottom, WINDOW.width + 6, 3))

    canvas.blit(sprites.plant(), (6, FLOOR_Y - 28))


def _mascot(canvas, surf, center) -> None:
    canvas.blit(surf, surf.get_rect(center=center))


def _table(canvas) -> None:
    pygame.draw.rect(canvas, (96, 64, 40), TABLE)
    for x in (TABLE.x + 4, TABLE.right - 7):
        pygame.draw.rect(canvas, (70, 46, 30), (x, TABLE.bottom, 3, FLOOR_Y + 6 - TABLE.bottom))


def _coffee(canvas, now: float) -> None:
    _table(canvas)
    cycle = now % 8.0
    sipping = 5.0 <= cycle < 6.2
    blink = (now % 4.0) < 0.15
    _mascot(canvas, sprites.mascot_face("right", closed=blink or sipping, mouth="smile" if cycle >= 6.2 else None), (60, 62))
    mug = sprites.mug()
    mx, my = (78, 58) if sipping else (84, TABLE.y - mug.get_height())
    canvas.blit(mug, (mx, my))
    if not sipping:
        for i in range(3):
            phase = (now * 0.8 + i / 3) % 1.0
            sx = mx + 8 + round(math.sin(now * 2 + i * 2) * 2) + i * 4
            sy = my - 3 - round(phase * 14)
            if phase < 0.8:
                pygame.draw.rect(canvas, (200, 196, 190), (sx, sy, 2, 2))


def _wander(canvas, now: float) -> None:
    period = 16.0
    t = now % period
    # walk right (0-6s), stop at the window (6-8s), walk back (8-14s), stop by the plant (14-16s)
    if t < 6:
        x, look, walking = 40 + t / 6 * 56, "right", True
    elif t < 8:
        x, look, walking = 96, "up", False
    elif t < 14:
        x, look, walking = 96 - (t - 8) / 6 * 56, "left", True
    else:
        x, look, walking = 40, "left", False
    hop = abs(math.sin(now * 7)) * 3 if walking else 0
    _mascot(canvas, sprites.mascot_face(look), (round(x), round(FLOOR_Y - 30 - hop)))
    if walking and math.sin(now * 7) > 0.9:
        pygame.draw.rect(canvas, (110, 80, 56), (round(x) - 10, FLOOR_Y - 2, 2, 2))


def _reading(canvas, now: float) -> None:
    _table(canvas)
    blink = (now % 5.0) < 0.15
    _mascot(canvas, sprites.mascot_face("down", closed=blink), (70, 46))
    flipping = (now % 6.0) < 0.35
    book = sprites.book(flip=flipping)
    canvas.blit(book, (70 - 22, TABLE.y - book.get_height() + 2))


def _window(canvas, now: float) -> None:
    sway = math.sin(now * 0.8) * 1.5
    blink = (now % 6.0) < 0.15
    _mascot(canvas, sprites.mascot_face("right", closed=blink), (round(72 + sway), FLOOR_Y - 34))


def _sleep(canvas, now: float) -> None:
    breathe = math.sin(now * 1.1)
    _mascot(canvas, sprites.mascot_face(closed=True), (70, round(FLOOR_Y - 26 + breathe)))
    for i in range(3):
        phase = (now * 0.25 + i / 3) % 1.0
        x = 88 + round(phase * 14) + round(math.sin(now + i) * 2)
        y = FLOOR_Y - 50 - round(phase * 30)
        shade = round(170 * (1 - phase))
        draw_text(canvas, "z" if i % 2 else "Z", (x, y), size=7 + i * 2, color=(shade, shade, shade + 20))


_DRAW = {
    "coffee": _coffee,
    "wander": _wander,
    "reading": _reading,
    "window": _window,
    "sleep": _sleep,
}


def draw_life(canvas, ctx: Context, clock: WallClock) -> None:
    name = vignette_for_hour(clock.hour)
    _room(canvas, name, ctx.now)
    _DRAW[name](canvas, ctx.now)
