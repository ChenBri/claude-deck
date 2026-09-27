from __future__ import annotations

import random

import pygame

from deck.ui.gfx import clear, draw_text
from deck.ui.name_entry import HighScoreFlow, draw_best
from deck.ui.scenes.base import Context, Scene

GAME_ID = "2048"

SIZE = 4
CELL = 24
GAP = 2

_COLORS = {
    0: (40, 34, 30),
    2: (224, 122, 42), 4: (214, 64, 48), 8: (190, 120, 220), 16: (100, 130, 220),
    32: (120, 200, 220), 64: (120, 200, 140), 128: (240, 210, 90), 256: (255, 178, 92),
    512: (224, 122, 42), 1024: (214, 64, 48), 2048: (255, 210, 140),
}


def _line_moves_left(line: list[int]) -> tuple[list[int], int]:
    """Compresses+merges one line toward index 0. Caller reverses/transposes
    to reuse this for all four directions."""
    vals = [v for v in line if v]
    merged: list[int] = []
    gained = 0
    i = 0
    while i < len(vals):
        if i + 1 < len(vals) and vals[i] == vals[i + 1]:
            merged.append(vals[i] * 2)
            gained += vals[i] * 2
            i += 2
        else:
            merged.append(vals[i])
            i += 1
    merged += [0] * (SIZE - len(merged))
    return merged, gained


class Twenty48Scene(Scene):
    """Joystick edges slide the board. Encoder push pauses/retries."""

    def __init__(self) -> None:
        self._rng = random.Random()
        self._hsf = HighScoreFlow(GAME_ID)
        self._reset()

    def _reset(self) -> None:
        self.grid = [[0] * SIZE for _ in range(SIZE)]
        self.score = 0
        self.game_over = False
        self._paused = False
        self._hsf.reset()
        self._spawn_tile()
        self._spawn_tile()

    def _empty_cells(self) -> list[tuple[int, int]]:
        return [(x, y) for y in range(SIZE) for x in range(SIZE) if self.grid[y][x] == 0]

    def _spawn_tile(self) -> None:
        free = self._empty_cells()
        if not free:
            return
        x, y = self._rng.choice(free)
        self.grid[y][x] = 4 if self._rng.random() < 0.1 else 2

    def _any_move_available(self) -> bool:
        if self._empty_cells():
            return True
        for y in range(SIZE):
            for x in range(SIZE):
                v = self.grid[y][x]
                if x + 1 < SIZE and self.grid[y][x + 1] == v:
                    return True
                if y + 1 < SIZE and self.grid[y + 1][x] == v:
                    return True
        return False

    def _move(self, direction: str) -> None:
        moved = False
        gained = 0
        if direction in ("left", "right"):
            for y in range(SIZE):
                line = self.grid[y][::-1] if direction == "right" else self.grid[y]
                new_line, g = _line_moves_left(line)
                gained += g
                if direction == "right":
                    new_line = new_line[::-1]
                if new_line != self.grid[y]:
                    moved = True
                self.grid[y] = new_line
        else:
            for x in range(SIZE):
                col = [self.grid[y][x] for y in range(SIZE)]
                line = col[::-1] if direction == "down" else col
                new_line, g = _line_moves_left(line)
                gained += g
                if direction == "down":
                    new_line = new_line[::-1]
                if new_line != col:
                    moved = True
                for y in range(SIZE):
                    self.grid[y][x] = new_line[y]

        if not moved:
            return
        self.score += gained
        self._spawn_tile()
        if not self._any_move_available():
            self.game_over = True
            self._hsf.on_game_over(self.score)

    def _handle_input(self, ctx: Context) -> None:
        if self._hsf.active:
            self._hsf.handle_input(ctx.inputs, self.score)
            return

        if ctx.inputs.get("encoder_push_edge", False):
            if self.game_over:
                self._reset()
            else:
                self._paused = not self._paused
        if self._paused or self.game_over:
            return

        edges = ctx.inputs.get("joystick_edge", frozenset())
        for direction in ("left", "right", "up", "down"):
            if direction in edges:
                self._move(direction)
                break

    def draw(self, canvas, ctx: Context) -> None:
        self._handle_input(ctx)

        clear(canvas)
        w = canvas.get_width()
        ox = (w - (SIZE * CELL + (SIZE - 1) * GAP)) // 2
        oy = 8
        draw_text(canvas, str(self.score), (4, 2), size=8, color=(160, 160, 160))

        for y in range(SIZE):
            for x in range(SIZE):
                v = self.grid[y][x]
                rx, ry = ox + x * (CELL + GAP), oy + y * (CELL + GAP)
                pygame.draw.rect(canvas, _COLORS.get(v, (255, 210, 140)), (rx, ry, CELL, CELL))
                if v:
                    size = 10 if v < 100 else 8 if v < 1000 else 7
                    tw = len(str(v)) * size * 0.6
                    draw_text(canvas, str(v), (rx + CELL / 2 - tw / 2, ry + CELL / 2 - size / 2), size=size, color=(20, 16, 14))

        board_h = SIZE * (CELL + GAP) - GAP
        if self._hsf.active:
            self._hsf.draw(canvas, self.score, ctx.now)
        elif self.game_over:
            cy = oy + board_h // 2
            pygame.draw.rect(canvas, (10, 8, 8), (ox, cy - 20, SIZE * (CELL + GAP), 50))
            draw_text(canvas, "game over", (ox + 12, cy - 16), size=9)
            draw_text(canvas, "push: retry", (ox + 6, cy - 2), size=7, color=(160, 160, 160))
            draw_best(canvas, GAME_ID, (ox + 6, cy + 10))
        elif self._paused:
            cy = oy + board_h // 2
            pygame.draw.rect(canvas, (10, 8, 8), (ox + 14, cy - 8, SIZE * (CELL + GAP) - 28, 16))
            draw_text(canvas, "paused", (ox + 30, cy - 4), size=9)
