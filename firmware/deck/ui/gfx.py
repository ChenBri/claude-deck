"""Small drawing helpers shared by every scene. Kept separate from render.py
so scenes can import this without a circular import back through the scene
manager."""
from __future__ import annotations

import pygame

BG_COLOR = (18, 14, 12)

# The default pygame font (Font(None, ...)) is a proportional TrueType face
# that renders as broken, illegible mush at these tiny point sizes with
# antialiasing off. A monospace font, antialiased, is dramatically more
# legible at the same size - this is a font/rendering fix, not a CRT-look
# change. SysFont tries each name in order and falls back safely if none of
# them exist on this system (e.g. the real Pi).
_FONT_NAMES = "consolas,dejavusansmono,couriernew,monospace"

_fonts: dict[int, pygame.font.Font] = {}


def get_font(size: int = 8) -> pygame.font.Font:
    font = _fonts.get(size)
    if font is None:
        font = pygame.font.SysFont(_FONT_NAMES, size)
        _fonts[size] = font
    return font


def draw_text(canvas, text, pos, size=8, color=(235, 235, 235)):
    surf = get_font(size).render(text, True, color)
    canvas.blit(surf, pos)


def clear(canvas, color=BG_COLOR):
    canvas.fill(color)
