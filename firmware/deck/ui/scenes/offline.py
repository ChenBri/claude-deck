from __future__ import annotations

import pygame

from deck.ui.gfx import clear, draw_text
from deck.ui.scenes.base import Context, Scene


class OfflineScene(Scene):
    """Connection lost card: the daemon heartbeat has gone quiet."""

    def draw(self, canvas, ctx: Context) -> None:
        clear(canvas, color=(10, 10, 12))
        w, h = canvas.get_width(), canvas.get_height()
        card = pygame.Rect(w // 2 - 40, h // 2 - 16, 80, 32)
        pygame.draw.rect(canvas, (50, 50, 54), card)
        pygame.draw.rect(canvas, (90, 90, 96), card, 1)
        draw_text(canvas, "LINK LOST", (card.centerx - 22, card.centery - 8), size=10, color=(200, 200, 200))
        draw_text(canvas, "no heartbeat from daemon", (card.centerx - 38, card.centery + 4), size=7, color=(140, 140, 144))
