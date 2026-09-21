from __future__ import annotations

from deck.ui import sprites
from deck.ui.gfx import clear, draw_text
from deck.ui.scenes.base import Context, Scene


class ErrorScene(Scene):
    """Storm cloud over the mascot."""

    def draw(self, canvas, ctx: Context) -> None:
        clear(canvas)
        w, h = canvas.get_width(), canvas.get_height()
        cloud = sprites.storm_cloud()
        canvas.blit(cloud, cloud.get_rect(center=(w // 2, h // 2 - 14)))
        mascot = sprites.mascot_mouth("open")
        canvas.blit(mascot, mascot.get_rect(center=(w // 2, h // 2 + 10)))
        draw_text(canvas, "error", (w // 2 - 12, h - 10), size=8, color=(214, 64, 48))
