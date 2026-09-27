"""Meter calibration wizard screen. Drawn directly by main.py like
Settings; the state lives in deck.calibration."""
from __future__ import annotations

import pygame

from deck.calibration import POINTS, CalibrationWizard
from deck.ui.gfx import clear, draw_text

TEXT = (220, 220, 220)
DIM = (140, 140, 144)


def draw_calibrate(canvas, wizard: CalibrationWizard) -> None:
    clear(canvas, color=(14, 14, 18))
    w, h = canvas.get_width(), canvas.get_height()
    draw_text(canvas, "CALIBRATE", (4, 2), size=10, color=(224, 122, 42))

    if wizard.step == "pick":
        draw_text(canvas, f"meter: < {wizard.meter} >", (4, 30), size=9, color=TEXT)
        draw_text(canvas, "rotate: pick  push: start", (4, 50), size=7, color=DIM)
    elif wizard.step == "trimpot":
        draw_text(canvas, f"{wizard.meter}: raw 100%", (4, 26), size=9, color=TEXT)
        draw_text(canvas, "turn its trimpot until", (4, 44), size=7, color=DIM)
        draw_text(canvas, "the needle sits on full scale", (4, 54), size=7, color=DIM)
        draw_text(canvas, "push: next", (4, 70), size=7, color=DIM)
    elif wizard.step == "point":
        target = round(POINTS[wizard.point] * 100)
        duty = wizard.curves[wizard.meter][wizard.point]
        draw_text(canvas, f"{wizard.meter} {wizard.point + 1}/{len(POINTS)}", (4, 22), size=9, color=TEXT)
        draw_text(canvas, f"needle to {target}% mark", (4, 36), size=9, color=(255, 210, 140))
        draw_text(canvas, f"duty {duty:.3f}", (4, 52), size=7, color=DIM)
        pygame.draw.rect(canvas, (90, 90, 96), (4, 64, w - 8, 6), 1)
        pygame.draw.rect(canvas, (255, 178, 92), (5, 65, round((w - 10) * duty), 4))
        draw_text(canvas, "rotate: nudge  push: next", (4, 78), size=7, color=DIM)
    else:
        draw_text(canvas, f"{wizard.meter} calibrated", (4, 30), size=9, color=TEXT)
        draw_text(canvas, "push: save and exit", (4, 50), size=7, color=DIM)

    draw_text(canvas, "joystick push: cancel", (4, h - 10), size=7, color=(120, 120, 120))
