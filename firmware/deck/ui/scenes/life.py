"""Mascot life: what the mascot gets up to during ambient mode, picked by
the local hour. First pass is the plain idle mascot; the time-of-day
vignettes and their sprites come next."""
from __future__ import annotations

import math

from deck.screen import WallClock
from deck.ui import sprites
from deck.ui.gfx import clear
from deck.ui.scenes.base import Context


def draw_life(canvas, ctx: Context, clock: WallClock) -> None:
    clear(canvas)
    bob = math.sin(ctx.now * 1.2) * 2
    blink = (ctx.now % 4.0) < 0.15
    mascot = sprites.mascot_idle(blink=blink)
    canvas.blit(mascot, mascot.get_rect(center=(canvas.get_width() // 2, canvas.get_height() // 2 + int(bob))))
