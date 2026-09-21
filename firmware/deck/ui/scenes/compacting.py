from __future__ import annotations

import math

import pygame

from deck.ui import sprites
from deck.ui.gfx import clear, draw_text
from deck.ui.scenes.base import Context, Scene


class CompactingScene(Scene):
    """Sweeps papers into a box."""

    def draw(self, canvas, ctx: Context) -> None:
        clear(canvas)
        w, h = canvas.get_width(), canvas.get_height()
        cx, cy = w // 2, h // 2 + 4
        mascot = sprites.mascot_mouth("flat")
        canvas.blit(mascot, mascot.get_rect(center=(cx, cy)))

        box = pygame.Rect(cx + 16, cy + 6, 22, 16)
        pygame.draw.rect(canvas, (120, 84, 48), box)
        pygame.draw.rect(canvas, (40, 24, 16), box, 1)

        sweep = (math.sin(ctx.now * 3) + 1) / 2
        paper_x = cx - 10 + int(sweep * 24)
        pygame.draw.rect(canvas, (235, 235, 235), (paper_x, cy + 8, 6, 8))

        draw_text(canvas, "compacting", (cx - 24, h - 10), size=8, color=(200, 200, 200))
