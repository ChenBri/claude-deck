"""App launcher: a small home screen reachable from IDLE (encoder push),
listing every registered app in deck.apps.APPS. Not state-driven like the
other scenes, so - like the settings menu - it's drawn directly by
main.py rather than through SceneManager.

Joystick left/right moves the highlight, encoder push opens the
highlighted app, joystick push backs out to the idle dashboard.
"""
from __future__ import annotations

from deck.apps import APPS
from deck.ui.gfx import clear, draw_text


def draw_home(canvas, selected_index: int) -> None:
    clear(canvas)
    w, h = canvas.get_width(), canvas.get_height()
    draw_text(canvas, "APPS", (4, 2), size=10, color=(224, 122, 42))

    count = max(len(APPS), 1)
    slot_w = w // count
    icon_y = h // 2 - 14
    label_y = icon_y + 20

    for i, app in enumerate(APPS):
        x = i * slot_w
        focused = i == selected_index
        color = (255, 210, 140) if focused else (170, 170, 170)
        icon = f"[{app.icon}]" if focused else f" {app.icon} "
        draw_text(canvas, icon, (x + slot_w // 2 - 12, icon_y), size=16, color=color)
        draw_text(canvas, app.label, (x + 4, label_y), size=8, color=color)

    draw_text(canvas, "joystick: move/open  push: back", (2, h - 10), size=7, color=(120, 120, 120))
