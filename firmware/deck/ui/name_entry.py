"""Retro arcade-style high score initials entry: three letters, joystick
up/down cycles the focused slot's character, left/right moves between
slots, encoder push confirms. Owned by a game scene as a sub-state of
"game over" - not routed through SceneManager, same reasoning as the
game-over/paused overlays each game already draws inline.
"""
from __future__ import annotations

import string

import pygame

from deck import scores
from deck.ui.gfx import draw_text

CHARSET = string.ascii_uppercase + string.digits
NAME_LENGTH = 3
BLINK_SECONDS = 0.4


class NameEntry:
    def __init__(self) -> None:
        self.letters = ["A"] * NAME_LENGTH
        self.cursor = 0
        self.done = False

    def handle_input(self, inputs: dict) -> None:
        if self.done:
            return
        edges = inputs.get("joystick_edge", frozenset())
        if "up" in edges:
            self._cycle(1)
        if "down" in edges:
            self._cycle(-1)
        if "left" in edges:
            self.cursor = max(0, self.cursor - 1)
        if "right" in edges:
            self.cursor = min(NAME_LENGTH - 1, self.cursor + 1)
        if inputs.get("encoder_push_edge", False):
            self.done = True

    def _cycle(self, step: int) -> None:
        i = CHARSET.index(self.letters[self.cursor])
        self.letters[self.cursor] = CHARSET[(i + step) % len(CHARSET)]

    @property
    def name(self) -> str:
        return "".join(self.letters)

    def draw(self, canvas, score: int, now: float) -> None:
        w, h = canvas.get_width(), canvas.get_height()
        pygame.draw.rect(canvas, (10, 8, 8), (w // 2 - 50, h // 2 - 34, 100, 68))
        draw_text(canvas, "new high score", (w // 2 - 42, h // 2 - 30), size=8, color=(224, 122, 42))
        draw_text(canvas, str(score), (w // 2 - 8, h // 2 - 18), size=10)

        box = 16
        total_w = NAME_LENGTH * box + (NAME_LENGTH - 1) * 4
        ox = w // 2 - total_w // 2
        oy = h // 2
        blink_on = int(now / BLINK_SECONDS) % 2 == 0
        for i, ch in enumerate(self.letters):
            x = ox + i * (box + 4)
            focused = i == self.cursor
            border = (255, 210, 140) if focused else (90, 90, 96)
            pygame.draw.rect(canvas, border, (x, oy, box, box), 1)
            if not focused or blink_on:
                draw_text(canvas, ch, (x + 4, oy + 2), size=10)
        draw_text(canvas, "joy: letter/slot  push: done", (w // 2 - 54, oy + box + 6), size=6, color=(160, 160, 160))


class HighScoreFlow:
    """Wraps the entering-name sub-state after game_over turns True. One
    instance per game scene: call on_game_over(score) once at the
    game_over transition, handle_input/draw every frame while active is
    True, and fall through to the plain game-over overlay otherwise."""

    def __init__(self, game_id: str) -> None:
        self.game_id = game_id
        self._entry: NameEntry | None = None

    def on_game_over(self, score: int) -> None:
        self._entry = NameEntry() if scores.qualifies(self.game_id, score) else None

    @property
    def active(self) -> bool:
        return self._entry is not None

    def handle_input(self, inputs: dict, score: int) -> None:
        if self._entry is None:
            return
        self._entry.handle_input(inputs)
        if self._entry.done:
            scores.add(self.game_id, self._entry.name, score)
            self._entry = None

    def draw(self, canvas, score: int, now: float) -> None:
        if self._entry is not None:
            self._entry.draw(canvas, score, now)

    def reset(self) -> None:
        self._entry = None


def draw_best(canvas, game_id: str, pos: tuple[int, int], n: int = 3) -> None:
    """Compact "best" list for a game-over screen: up to n "NAM 1234" lines."""
    x, y = pos
    for name, score in scores.top(game_id, n):
        draw_text(canvas, f"{name} {score}", (x, y), size=7, color=(160, 160, 160))
        y += 9
