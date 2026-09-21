from __future__ import annotations

import random

import pygame

from deck.ui.gfx import clear, draw_text
from deck.ui.scenes.base import Context, Scene

CELL = 8
COLS = 20
ROWS = 15
STEP_SECONDS = 0.15

_DIRS = {(0, -1), (0, 1), (-1, 0), (1, 0)}


class SnakeScene(Scene):
    """Joystick steers, encoder push pauses. autoplay=True runs a simple
    self-playing demo for the idle screensaver, ignoring the joystick."""

    def __init__(self, autoplay: bool = False) -> None:
        self.autoplay = autoplay
        self._rng = random.Random()
        self._reset()
        self._last_step = 0.0
        self._paused = False

    def _reset(self) -> None:
        cx, cy = COLS // 2, ROWS // 2
        self.body = [(cx - 1, cy), (cx - 2, cy), (cx - 3, cy)]
        self.direction = (1, 0)
        self.food = self._spawn_food()
        self.game_over = False

    def _spawn_food(self):
        free = [(x, y) for x in range(COLS) for y in range(ROWS) if (x, y) not in getattr(self, "body", [])]
        return self._rng.choice(free) if free else (0, 0)

    def on_enter(self, ctx: Context) -> None:
        self._reset()
        self._last_step = ctx.now

    def _autoplay_direction(self):
        head = self.body[0]
        best = None
        best_dist = None
        for dx, dy in _DIRS:
            if (dx, dy) == (-self.direction[0], -self.direction[1]) and len(self.body) > 1:
                continue
            nx, ny = head[0] + dx, head[1] + dy
            if not (0 <= nx < COLS and 0 <= ny < ROWS):
                continue
            if (nx, ny) in self.body:
                continue
            dist = abs(nx - self.food[0]) + abs(ny - self.food[1])
            if best_dist is None or dist < best_dist:
                best_dist = dist
                best = (dx, dy)
        return best or self.direction

    def _handle_input(self, ctx: Context) -> None:
        if ctx.inputs.get("encoder_push_edge", False):
            if self.game_over:
                self._reset()
            else:
                self._paused = not self._paused

        jx, jy = ctx.inputs.get("joystick", (0, 0))
        if jx or jy:
            candidate = (1 if jx > 0 else -1 if jx < 0 else 0, 1 if jy > 0 else -1 if jy < 0 else 0)
            # only one axis at a time, and never reverse straight into yourself
            if candidate[0] and candidate[1]:
                candidate = (candidate[0], 0)
            if candidate != (-self.direction[0], -self.direction[1]) or len(self.body) == 1:
                self.direction = candidate

    def _step(self) -> None:
        if self.game_over or self._paused:
            return
        direction = self._autoplay_direction() if self.autoplay else self.direction
        head = (self.body[0][0] + direction[0], self.body[0][1] + direction[1])
        if not (0 <= head[0] < COLS and 0 <= head[1] < ROWS) or head in self.body:
            if self.autoplay:
                self._reset()
                return
            self.game_over = True
            return
        self.direction = direction
        self.body.insert(0, head)
        if head == self.food:
            self.food = self._spawn_food()
        else:
            self.body.pop()

    def draw(self, canvas, ctx: Context) -> None:
        if not self.autoplay:
            self._handle_input(ctx)
        if ctx.now - self._last_step >= STEP_SECONDS:
            self._last_step = ctx.now
            self._step()

        clear(canvas)
        fx, fy = self.food
        pygame.draw.rect(canvas, (214, 64, 48), (fx * CELL, fy * CELL, CELL, CELL))
        for i, (x, y) in enumerate(self.body):
            color = (255, 178, 92) if i == 0 else (224, 122, 42)
            pygame.draw.rect(canvas, color, (x * CELL, y * CELL, CELL - 1, CELL - 1))

        if self.game_over:
            cx, cy = canvas.get_width() // 2, canvas.get_height() // 2
            pygame.draw.rect(canvas, (10, 8, 8), (cx - 34, cy - 10, 68, 32))
            draw_text(canvas, "game over", (cx - 24, cy - 6), size=10)
            draw_text(canvas, "push: retry", (cx - 28, cy + 8), size=7, color=(160, 160, 160))
        elif self._paused:
            cx, cy = canvas.get_width() // 2, canvas.get_height() // 2
            pygame.draw.rect(canvas, (10, 8, 8), (cx - 24, cy - 6, 48, 16))
            draw_text(canvas, "paused", (cx - 18, cy), size=10)
