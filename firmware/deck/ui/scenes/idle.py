from __future__ import annotations

import time

from deck.ui.gfx import clear, draw_text
from deck.ui.scenes.base import Context, Scene
from deck.ui.scenes.snake import SnakeScene

ATTRACT_AFTER_SECONDS = 60.0


class IdleScene(Scene):
    """Clock, date, name, weather, git status, today's totals. Drops into a
    self-playing snake demo if nobody's touched the panel for a while."""

    def __init__(self) -> None:
        self._entered_at: float | None = None
        self._attract = SnakeScene(autoplay=True)

    def on_enter(self, ctx: Context) -> None:
        self._entered_at = ctx.now

    def draw(self, canvas, ctx: Context) -> None:
        if self._entered_at is None:
            self._entered_at = ctx.now
        if ctx.now - self._entered_at >= ATTRACT_AFTER_SECONDS:
            self._attract.draw(canvas, ctx)
            return

        clear(canvas)
        info = ctx.idle_info
        y = 4
        clock = info.get("clock") or time.strftime("%H:%M")
        date = info.get("date") or time.strftime("%Y-%m-%d")
        draw_text(canvas, clock, (4, y), size=16, color=(255, 178, 92))
        y += 18
        draw_text(canvas, date, (4, y), size=8, color=(200, 200, 200))
        y += 12
        name = info.get("name")
        if name:
            draw_text(canvas, name, (4, y), size=8, color=(200, 200, 200))
            y += 10
        weather = info.get("weather")
        if weather:
            draw_text(canvas, weather, (4, y), size=8, color=(160, 190, 220))
            y += 10
        git_status = info.get("git")
        if git_status:
            draw_text(canvas, git_status[:26], (4, y), size=7, color=(140, 200, 140))
            y += 9
        totals = info.get("totals")
        if totals:
            draw_text(canvas, totals[:26], (4, canvas.get_height() - 10), size=7, color=(150, 150, 150))
