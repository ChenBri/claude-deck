"""Small drawing helpers shared by every scene. Kept separate from render.py
so scenes can import this without a circular import back through the scene
manager."""
from __future__ import annotations

import pygame

BG_COLOR = (18, 14, 12)

_fonts: dict[int, pygame.font.Font] = {}


def get_font(size: int = 8) -> pygame.font.Font:
    font = _fonts.get(size)
    if font is None:
        font = pygame.font.Font(None, size)
        _fonts[size] = font
    return font


def draw_text(canvas, text, pos, size=8, color=(235, 235, 235)):
    surf = get_font(size).render(text, False, color)
    canvas.blit(surf, pos)


def clear(canvas, color=BG_COLOR):
    canvas.fill(color)
