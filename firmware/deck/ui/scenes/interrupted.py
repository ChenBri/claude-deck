from __future__ import annotations

import pygame

from deck.ui import sprites
from deck.ui.gfx import clear, draw_text
from deck.ui.scenes.base import Context, Scene


class InterruptedScene(Scene):
    """Panic latched: everything halts until the mushroom is twist-released."""

    def draw(self, canvas, ctx: Context) -> None:
        clear(canvas, color=(28, 12, 12))
        w, h = canvas.get_width(), canvas.get_height()
        mascot = sprites.mascot_mouth("flat")
        gray = pygame.Surface(mascot.get_size(), pygame.SRCALPHA)
        gray.blit(mascot, (0, 0))
        gray.fill((160, 160, 160, 0), special_flags=pygame.BLEND_RGBA_MULT)
        canvas.blit(gray, gray.get_rect(center=(w // 2, h // 2)))

        pygame.draw.circle(canvas, (214, 64, 48), (w // 2, 16), 8, 2)
        pygame.draw.line(canvas, (214, 64, 48), (w // 2 - 6, 10), (w // 2 + 6, 22), 2)
        pygame.draw.line(canvas, (214, 64, 48), (w // 2 + 6, 10), (w // 2 - 6, 22), 2)

        draw_text(canvas, "INTERRUPTED", (w // 2 - 30, h - 10), size=9, color=(214, 64, 48))
        draw_text(canvas, "twist to release", (w // 2 - 28, h - 20), size=7, color=(180, 100, 96))
