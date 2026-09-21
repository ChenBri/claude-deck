from __future__ import annotations

from deck.ui.gfx import clear, draw_text
from deck.ui.scenes.base import Context, Scene


class BootScene(Scene):
    """Covers the ~25s Pi boot so the panel never looks broken."""

    def draw(self, canvas, ctx: Context) -> None:
        clear(canvas)
        w, h = canvas.get_width(), canvas.get_height()
        dots = "." * (int(ctx.now * 2) % 4)
        draw_text(canvas, "claude-deck", (w // 2 - 30, h // 2 - 6), size=10, color=(224, 122, 42))
        draw_text(canvas, f"booting{dots}", (w // 2 - 24, h // 2 + 8), size=8, color=(160, 160, 160))
