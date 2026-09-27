"""App launcher: a small home screen reachable from ambient mode (encoder
push), listing every registered app in deck.apps.APPS. Not state-driven
like the other scenes, so - like the settings menu - it's drawn directly
by main.py rather than through SceneManager.

A carousel: the focused app's icon large in the middle with its name
under it, its neighbours smaller and dimmed either side, and a dot per
app along the bottom. Joystick left/right moves, encoder push opens,
joystick push backs out.
"""
from __future__ import annotations

import pygame

from deck.apps import APPS
from deck.ui import sprites
from deck.ui.gfx import clear, draw_text, get_font

ACCENT = (255, 210, 140)
TITLE = (224, 122, 42)
HINT = (120, 120, 120)

FOCUS_SCALE = 4  # 12x12 icon -> 48px
SIDE_SCALE = 2  # -> 24px
SIDE_OFFSET = 50  # px from centre to each neighbour's centre
ICON_Y = 50
NEIGHBOUR_DIM = 110  # out of 255


def _dimmed(surf: pygame.Surface) -> pygame.Surface:
    out = surf.copy()
    out.fill((NEIGHBOUR_DIM, NEIGHBOUR_DIM, NEIGHBOUR_DIM, 255), special_flags=pygame.BLEND_RGBA_MULT)
    return out


def draw_home(canvas, selected_index: int) -> None:
    clear(canvas)
    w, h = canvas.get_width(), canvas.get_height()
    cx = w // 2
    draw_text(canvas, "APPS", (4, 2), size=10, color=TITLE)

    count = len(APPS)
    if count > 1:
        for side in (-1, 1):
            app = APPS[(selected_index + side) % count]
            icon = _dimmed(sprites.app_icon(app.id, SIDE_SCALE))
            canvas.blit(icon, icon.get_rect(center=(cx + side * SIDE_OFFSET, ICON_Y)))
        draw_text(canvas, "<", (4, ICON_Y - 6), size=10, color=HINT)
        draw_text(canvas, ">", (w - 10, ICON_Y - 6), size=10, color=HINT)

    app = APPS[selected_index]
    icon = sprites.app_icon(app.id, FOCUS_SCALE)
    rect = icon.get_rect(center=(cx, ICON_Y))
    pygame.draw.rect(canvas, (40, 32, 26), rect.inflate(10, 10), border_radius=4)
    pygame.draw.rect(canvas, TITLE, rect.inflate(10, 10), 1, border_radius=4)
    canvas.blit(icon, rect)

    label_w = get_font(10).size(app.label)[0]
    draw_text(canvas, app.label, (cx - label_w // 2, rect.bottom + 9), size=10, color=ACCENT)

    dot_gap = 7
    x0 = cx - (count - 1) * dot_gap // 2
    for i in range(count):
        color = ACCENT if i == selected_index else (70, 64, 60)
        pygame.draw.rect(canvas, color, (x0 + i * dot_gap - 1, h - 22, 3, 3))

    hint = "stick: move  knob: open"
    draw_text(canvas, hint, (cx - get_font(7).size(hint)[0] // 2, h - 12), size=7, color=HINT)
