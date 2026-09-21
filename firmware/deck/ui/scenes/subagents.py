from __future__ import annotations

import math

import pygame

from deck.ui import sprites
from deck.ui.gfx import clear
from deck.ui.scenes.base import Context, Scene


class SubagentsScene(Scene):
    """One mini mascot per live subagent, orbiting the main one."""

    def draw(self, canvas, ctx: Context) -> None:
        clear(canvas)
        w, h = canvas.get_width(), canvas.get_height()
        cx, cy = w // 2, h // 2
        count = ctx.session.subagent_count if ctx.session else 1

        mascot = sprites.mascot_mouth("open" if int(ctx.now * 4) % 2 == 0 else "flat")
        canvas.blit(mascot, mascot.get_rect(center=(cx, cy)))

        mini = pygame.transform.smoothscale(
            sprites.mascot_idle(), (mascot.get_width() // 2, mascot.get_height() // 2)
        )
        radius = 26
        for i in range(count):
            angle = ctx.now * 1.2 + i * (2 * math.pi / max(count, 1))
            mx = cx + int(math.cos(angle) * radius)
            my = cy + int(math.sin(angle) * radius * 0.6)
            canvas.blit(mini, mini.get_rect(center=(mx, my)))
