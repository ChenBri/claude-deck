from __future__ import annotations

import random

import pygame

from deck.ui.gfx import clear, draw_text
from deck.ui.scenes.base import Context, Scene

CELL = 8
COLS = 10
ROWS = 15
FALL_SECONDS = 0.6
SOFT_DROP_SECONDS = 0.08

# Each piece as a set of (x, y) cells in a 4x4 box, rotated 90 deg by (x, y) -> (y, 3 - x).
_PIECES = {
    "I": [(0, 1), (1, 1), (2, 1), (3, 1)],
    "O": [(1, 0), (2, 0), (1, 1), (2, 1)],
    "T": [(1, 0), (0, 1), (1, 1), (2, 1)],
    "S": [(1, 0), (2, 0), (0, 1), (1, 1)],
    "Z": [(0, 0), (1, 0), (1, 1), (2, 1)],
    "J": [(0, 0), (0, 1), (1, 1), (2, 1)],
    "L": [(2, 0), (0, 1), (1, 1), (2, 1)],
}
_COLORS = {
    "I": (120, 200, 220), "O": (240, 210, 90), "T": (190, 120, 220),
    "S": (120, 200, 140), "Z": (214, 64, 48), "J": (100, 130, 220), "L": (224, 122, 42),
}


def _rotate(cells):
    return [(y, 3 - x) for x, y in cells]


class TetrisScene(Scene):
    """Joystick moves, mech keys rotate (CLD) and hard-drop (NEW). Encoder push pauses."""

    def __init__(self) -> None:
        self._rng = random.Random()
        self._reset()

    def _reset(self) -> None:
        self.grid: dict[tuple[int, int], str] = {}
        self.game_over = False
        self._paused = False
        self._last_fall = 0.0
        self._spawn()

    def _spawn(self) -> None:
        self.kind = self._rng.choice(list(_PIECES))
        self.cells = list(_PIECES[self.kind])
        self.pos = (COLS // 2 - 2, 0)
        if self._collides(self.cells, self.pos):
            self.game_over = True

    def _collides(self, cells, pos) -> bool:
        px, py = pos
        for x, y in cells:
            gx, gy = px + x, py + y
            if gx < 0 or gx >= COLS or gy >= ROWS:
                return True
            if gy >= 0 and (gx, gy) in self.grid:
                return True
        return False

    def _lock(self) -> None:
        px, py = self.pos
        for x, y in self.cells:
            gx, gy = px + x, py + y
            if gy >= 0:
                self.grid[(gx, gy)] = self.kind
        self._clear_lines()
        self._spawn()

    def _clear_lines(self) -> None:
        full_rows = [y for y in range(ROWS) if all((x, y) in self.grid for x in range(COLS))]
        if not full_rows:
            return
        remaining = {(x, y): k for (x, y), k in self.grid.items() if y not in full_rows}
        shift = {y: sum(1 for fy in full_rows if fy > y) for y in range(ROWS)}
        self.grid = {(x, y + shift[y]): k for (x, y), k in remaining.items()}

    def on_enter(self, ctx: Context) -> None:
        self._last_fall = ctx.now

    def _handle_input(self, ctx: Context) -> None:
        if ctx.inputs.get("encoder_push_edge", False):
            self._paused = not self._paused
        if self._paused or self.game_over:
            return

        edges = ctx.inputs.get("joystick_edge", frozenset())
        if "left" in edges:
            candidate = (self.pos[0] - 1, self.pos[1])
            if not self._collides(self.cells, candidate):
                self.pos = candidate
        if "right" in edges:
            candidate = (self.pos[0] + 1, self.pos[1])
            if not self._collides(self.cells, candidate):
                self.pos = candidate

        keys = ctx.inputs.get("mech_keys", frozenset())
        if "CLD" in keys:
            rotated = _rotate(self.cells)
            for kick in (0, -1, 1, -2, 2):
                candidate_pos = (self.pos[0] + kick, self.pos[1])
                if not self._collides(rotated, candidate_pos):
                    self.cells = rotated
                    self.pos = candidate_pos
                    break
        if "NEW" in keys:
            while not self._collides(self.cells, (self.pos[0], self.pos[1] + 1)):
                self.pos = (self.pos[0], self.pos[1] + 1)
            self._lock()

    def _fall(self, ctx: Context) -> None:
        if self._paused or self.game_over:
            return
        jx, jy = ctx.inputs.get("joystick", (0, 0))
        interval = SOFT_DROP_SECONDS if jy > 0 else FALL_SECONDS
        if ctx.now - self._last_fall < interval:
            return
        self._last_fall = ctx.now
        candidate = (self.pos[0], self.pos[1] + 1)
        if self._collides(self.cells, candidate):
            self._lock()
        else:
            self.pos = candidate

    def draw(self, canvas, ctx: Context) -> None:
        self._handle_input(ctx)
        self._fall(ctx)

        clear(canvas)
        ox = (canvas.get_width() - COLS * CELL) // 2 - 20
        for (x, y), kind in self.grid.items():
            pygame.draw.rect(canvas, _COLORS[kind], (ox + x * CELL, y * CELL, CELL - 1, CELL - 1))
        px, py = self.pos
        for x, y in self.cells:
            gy = py + y
            if gy >= 0:
                pygame.draw.rect(canvas, _COLORS[self.kind], (ox + (px + x) * CELL, gy * CELL, CELL - 1, CELL - 1))

        pygame.draw.rect(canvas, (90, 90, 96), (ox - 1, 0, COLS * CELL + 2, ROWS * CELL), 1)

        if self.game_over:
            draw_text(canvas, "game over", (ox + 8, canvas.get_height() // 2), size=9)
        elif self._paused:
            draw_text(canvas, "paused", (ox + 14, canvas.get_height() // 2), size=9)
