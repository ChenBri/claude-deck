"""Settings app overlay. Not state-driven like the other scenes, so it lives
outside SceneManager: main.py draws it directly when App.current_app ==
"settings"."""
from __future__ import annotations

from deck.menu import ITEMS, Menu, _get
from deck.ui.gfx import clear, draw_text

VISIBLE_ROWS = 7


def draw_menu(canvas, menu: Menu) -> None:
    clear(canvas, color=(14, 14, 18))
    h = canvas.get_height()
    draw_text(canvas, "SETTINGS", (4, 2), size=10, color=(224, 122, 42))

    top = max(0, min(menu.focus - 3, max(0, len(ITEMS) - VISIBLE_ROWS)))
    y = 16
    for i in range(top, min(top + VISIBLE_ROWS, len(ITEMS))):
        item = ITEMS[i]
        focused = i == menu.focus
        color = (255, 210, 140) if focused else (170, 170, 170)
        prefix = ">" if focused else " "
        if item.kind == "action":
            text = f"{prefix} {item.label}"
        else:
            text = f"{prefix} {item.label}: {_get(menu.settings, item.key)}"
        draw_text(canvas, text[:28], (4, y), size=8, color=color)
        y += 12

    draw_text(canvas, "rotate: move  push: set", (4, h - 10), size=7, color=(120, 120, 120))
