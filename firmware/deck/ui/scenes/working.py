from __future__ import annotations

import pygame

from deck.ui import sprites
from deck.ui.gfx import clear, draw_text
from deck.ui.scenes.base import Context, Scene

_GLYPHS = ["<", ">", "{", "}", "/", "=", "#"]


class WorkingScene(Scene):
    """Types at a tiny desk, glyphs fly. Speed tracks the tool-call rate."""

    def draw(self, canvas, ctx: Context) -> None:
        clear(canvas)
        w, h = canvas.get_width(), canvas.get_height()
        speed = 1.0 + min(ctx.tool_rate, 4.0)

        cx, cy = w // 2, h // 2 + 6
        typing = int(ctx.now * speed * 6) % 2 == 0
        mascot = sprites.mascot_mouth("open" if typing else "flat")
        canvas.blit(mascot, mascot.get_rect(center=(cx, cy)))

        # tiny desk
        pygame.draw.rect(canvas, (60, 40, 28), (cx - 20, cy + 20, 40, 6))

        # glyphs flying up and away, looping
        for i, glyph in enumerate(_GLYPHS):
            phase = (ctx.now * speed * 0.8 + i * 0.6) % 3.0
            gx = cx + 14 + i * 4 - int(phase * 6)
            gy = cy - 10 - int(phase * 20)
            alpha_ok = phase < 2.5
            if alpha_ok:
                draw_text(canvas, glyph, (gx, gy), size=9, color=(255, 178, 92))

        if ctx.tool_name:
            label = ctx.tool_name
            if ctx.tool_target:
                label += f" {ctx.tool_target}"
            draw_text(canvas, label[:26], (2, h - 10), size=8, color=(200, 200, 200))
