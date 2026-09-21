from __future__ import annotations

import math

import pygame

from deck.ui import sprites
from deck.ui.gfx import clear, draw_text
from deck.ui.scenes.base import Context, Scene


class BlockedPermissionScene(Scene):
    """Turns, looks at you, holds a question sign showing the pending call."""

    def draw(self, canvas, ctx: Context) -> None:
        clear(canvas)
        w, h = canvas.get_width(), canvas.get_height()
        cx, cy = w // 2 - 10, h // 2
        mascot = sprites.mascot_mouth("question")
        canvas.blit(mascot, mascot.get_rect(center=(cx, cy)))

        sign_rect = pygame.Rect(cx + 20, cy - 22, 34, 26)
        pygame.draw.rect(canvas, (235, 235, 235), sign_rect)
        pygame.draw.rect(canvas, (40, 24, 16), sign_rect, 1)
        draw_text(canvas, "?", (sign_rect.centerx - 3, sign_rect.centery - 6), size=14, color=(214, 64, 48))

        pending = ctx.session.pending if ctx.session else None
        if pending:
            label = pending.tool
            if pending.target:
                label += f" {pending.target}"
            draw_text(canvas, label[:26], (2, h - 10), size=8, color=(214, 64, 48))


class BlockedInputScene(Scene):
    """Taps foot, checks watch: waiting on you, nothing pending to approve."""

    def draw(self, canvas, ctx: Context) -> None:
        clear(canvas)
        w, h = canvas.get_width(), canvas.get_height()
        cx, cy = w // 2, h // 2
        tap = math.sin(ctx.now * 6) > 0
        mascot = sprites.mascot_idle(blink=False)
        canvas.blit(mascot, mascot.get_rect(center=(cx, cy + (1 if tap else 0))))
        draw_text(canvas, "waiting on you", (cx - 24, h - 10), size=8, color=(200, 200, 200))
