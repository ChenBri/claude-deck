from __future__ import annotations

import math

from deck.ui import sprites
from deck.ui.gfx import clear
from deck.ui.scenes.base import Context, Scene


class ReadyScene(Scene):
    """Mascot sits, blinks."""

    BLINK_PERIOD = 4.0
    BLINK_DURATION = 0.15

    def draw(self, canvas, ctx: Context) -> None:
        clear(canvas)
        bob = math.sin(ctx.now * 1.5) * 2
        blink = (ctx.now % self.BLINK_PERIOD) < self.BLINK_DURATION
        mascot = sprites.mascot_idle(blink=blink)
        rect = mascot.get_rect(center=(canvas.get_width() // 2, canvas.get_height() // 2 + int(bob)))
        canvas.blit(mascot, rect)
