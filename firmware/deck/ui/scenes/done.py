from __future__ import annotations

import math
import random

from deck.ui import sprites
from deck.ui.gfx import clear
from deck.ui.scenes.base import Context, Scene


class DoneScene(Scene):
    """Victory hop and confetti."""

    def __init__(self) -> None:
        self._rng = random.Random(0)
        self._confetti = []  # (x, y0, phase, color)

    def on_enter(self, ctx: Context) -> None:
        self._confetti = [
            (self._rng.uniform(0, 160), self._rng.uniform(-40, 0), self._rng.uniform(0, 3), self._rng.choice("GY"))
            for _ in range(24)
        ]

    def draw(self, canvas, ctx: Context) -> None:
        clear(canvas)
        w, h = canvas.get_width(), canvas.get_height()
        hop = abs(math.sin(ctx.now * 4)) * 10
        mascot = sprites.mascot_mouth("smile")
        canvas.blit(mascot, mascot.get_rect(center=(w // 2, h // 2 - int(hop))))

        for x, y0, phase, color in self._confetti:
            fall = ((ctx.now + phase) * 30) % (h + 40)
            particle = sprites.confetti_particle(color)
            canvas.blit(particle, (int(x), int(y0 + fall)))
