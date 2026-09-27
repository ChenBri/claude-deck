"""Hardware test screen. Like Settings, drawn directly by main.py rather
than through SceneManager; the state lives in deck.hwtest."""
from __future__ import annotations

import pygame

from deck.hwtest import HardwareTest
from deck.panel.base import GB_BUTTONS, MECH_KEYS, TOGGLES
from deck.ui.gfx import clear, draw_text

ON = (255, 210, 140)
OFF = (90, 90, 96)
DIM = (140, 140, 144)
ROW = 11


def _cells(canvas, y: int, items: list[tuple[str, bool]]) -> None:
    x = 4
    for label, lit in items:
        w = len(label) * 5 + 6
        if lit:
            pygame.draw.rect(canvas, (60, 44, 24), (x - 2, y - 1, w - 2, ROW - 1))
        draw_text(canvas, label, (x, y), size=7, color=ON if lit else OFF)
        x += w


def draw_hwtest(canvas, test: HardwareTest, now: float, output_label: str) -> None:
    clear(canvas, color=(14, 14, 18))
    w, h = canvas.get_width(), canvas.get_height()
    draw_text(canvas, "HW TEST", (4, 2), size=10, color=(224, 122, 42))
    draw_text(canvas, output_label[:22], (54, 4), size=7, color=(160, 190, 220))

    y = 18
    _cells(canvas, y, [("APPROVE", test.flashing("APPROVE", now)), ("DENY", test.flashing("DENY", now))])
    y += ROW
    _cells(canvas, y, [(name, test.flashing(name, now)) for name in MECH_KEYS])
    y += ROW
    _cells(canvas, y, [(name, name in test.held) for name in GB_BUTTONS])
    y += ROW
    _cells(canvas, y, [(name.replace("AUTO_ACCEPT", "AUTO"), test.toggles.get(name, False)) for name in TOGGLES])
    y += ROW
    draw_text(canvas, f"SEL {test.selector or '?'}   EFFORT {test.effort or '?'}", (4, y), size=7, color=DIM)
    y += ROW
    jx, jy = test.joystick
    _cells(canvas, y, [(f"ENC {test.encoder_count:+d}", test.flashing("ENC", now)),
                       (f"JOY {jx:+.1f},{jy:+.1f}", test.flashing("JOY", now) or bool(jx or jy))])
    y += ROW
    vol = "?" if test.volume is None else f"{round(test.volume * 100)}%"
    draw_text(canvas, f"VOL {vol}", (4, y), size=7, color=DIM)
    if test.volume is not None:
        pygame.draw.rect(canvas, OFF, (40, y + 2, 60, 5), 1)
        pygame.draw.rect(canvas, ON, (41, y + 3, round(58 * test.volume), 3))

    draw_text(canvas, "mushroom: own screen  2x push: exit", (2, h - 10), size=6, color=(120, 120, 120))
