from __future__ import annotations

import random

import pygame

from deck.ui.gfx import clear, draw_text, get_font
from deck.ui.name_entry import HighScoreFlow, draw_best
from deck.ui.scenes.base import Context, Scene

GAME_ID = "pong"

PADDLE_W = 3
PADDLE_H = 20
PADDLE_MARGIN = 6
PADDLE_SPEED = 90.0  # px/s, joystick player
KNOB_STEP = 6.0  # px per encoder detent, player 2
AI_SPEED = 55.0  # px/s, deliberately slower than the player can move - beatable
BALL_RADIUS = 2
BALL_SPEED_START = 55.0
BALL_SPEED_MAX = 110.0
BALL_SPEED_STEP = 4.0  # per paddle hit
WIN_SCORE = 7  # 2 player match length

P1_COLOR = (255, 178, 92)
P2_COLOR = (120, 130, 220)
MODES = ("1 PLAYER", "2 PLAYERS")


class PongScene(Scene):
    """Entering shows a mode picker (stick up/down, knob push to start).

    1 player: the joystick moves the left paddle against a beatable AI.
    Single life, score is how many times you got it past the AI; high
    scores as in the other games.

    2 players: joystick on the left paddle, encoder knob on the right one,
    a step per detent like an original Pong cabinet's paddle knob. First
    to WIN_SCORE wins; no high score entry, there's no single score to rank.

    Encoder push pauses, and restarts once a game is over (same mode).
    Joystick push backs out to the launcher, as everywhere.
    """

    def __init__(self) -> None:
        self._rng = random.Random()
        self._hsf = HighScoreFlow(GAME_ID)
        self.mode_index = 0
        self.choosing = True
        self._reset()

    def on_enter(self, ctx: Context) -> None:
        self.choosing = True
        self._reset()

    @property
    def two_player(self) -> bool:
        return self.mode_index == 1

    def _reset(self) -> None:
        self.score = 0  # 1P: points against the AI
        self.scores = [0, 0]  # 2P: left, right
        self.game_over = False
        self.winner: int | None = None
        self._paused = False
        self._hsf.reset()
        self.player_y = 60.0
        self.ai_y = 60.0  # the right paddle: AI in 1P, player 2 in 2P
        self._serve(toward_player=False)

    def _serve(self, toward_player: bool) -> None:
        self.ball = [80.0, 60.0]
        angle = self._rng.uniform(-0.5, 0.5)
        vx = -BALL_SPEED_START if toward_player else BALL_SPEED_START
        self.ball_v = [vx, BALL_SPEED_START * angle]

    def _handle_input(self, ctx: Context) -> None:
        if self.choosing:
            edges = ctx.inputs.get("joystick_edge", ())
            if "up" in edges or "down" in edges:
                self.mode_index = 1 - self.mode_index
            if ctx.inputs.get("encoder_push_edge", False):
                self.choosing = False
                self._reset()
            return

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

        _, jy = ctx.inputs.get("joystick", (0, 0))
        h = 120
        self.player_y = max(PADDLE_H / 2, min(h - PADDLE_H / 2, self.player_y + jy * PADDLE_SPEED * ctx.dt))
        if self.two_player:
            # clockwise moves the paddle down
            self.ai_y += ctx.inputs.get("encoder_steps", 0) * KNOB_STEP
            self.ai_y = max(PADDLE_H / 2, min(h - PADDLE_H / 2, self.ai_y))

    def _point(self, left_scored: bool) -> None:
        """Only reached in 2 player mode; 1P scoring stays inline in _step."""
        self.scores[0 if left_scored else 1] += 1
        if max(self.scores) >= WIN_SCORE:
            self.game_over = True
            self.winner = 0 if left_scored else 1
            return
        self._serve(toward_player=left_scored)  # serve toward whoever just conceded

    def _step(self, ctx: Context) -> None:
        if self.choosing or self._paused or self.game_over or self._hsf.active:
            return
        w, h = 160, 120

        if not self.two_player:
            target = self.ball[1]
            if self.ai_y < target:
                self.ai_y = min(target, self.ai_y + AI_SPEED * ctx.dt)
            else:
                self.ai_y = max(target, self.ai_y - AI_SPEED * ctx.dt)
            self.ai_y = max(PADDLE_H / 2, min(h - PADDLE_H / 2, self.ai_y))

        bx, by = self.ball
        bx += self.ball_v[0] * ctx.dt
        by += self.ball_v[1] * ctx.dt

        if by <= BALL_RADIUS or by >= h - BALL_RADIUS:
            by = max(BALL_RADIUS, min(h - BALL_RADIUS, by))
            self.ball_v[1] *= -1

        player_x = PADDLE_MARGIN + PADDLE_W
        if bx <= player_x and self.ball_v[0] < 0:
            if abs(by - self.player_y) <= PADDLE_H / 2:
                bx = player_x
                offset = (by - self.player_y) / (PADDLE_H / 2)
                speed = min(BALL_SPEED_MAX, abs(self.ball_v[0]) + BALL_SPEED_STEP)
                self.ball_v[0] = speed
                self.ball_v[1] = speed * offset
            elif bx < 0:
                if self.two_player:
                    self._point(left_scored=False)
                    return
                self.game_over = True
                self._hsf.on_game_over(self.score)
                self.ball = [bx, by]
                return

        ai_x = w - PADDLE_MARGIN - PADDLE_W
        if bx >= ai_x and self.ball_v[0] > 0:
            if abs(by - self.ai_y) <= PADDLE_H / 2:
                bx = ai_x
                offset = (by - self.ai_y) / (PADDLE_H / 2)
                speed = min(BALL_SPEED_MAX, abs(self.ball_v[0]) + BALL_SPEED_STEP)
                self.ball_v[0] = -speed
                self.ball_v[1] = speed * offset
            elif bx > w:
                if self.two_player:
                    self._point(left_scored=True)
                    return
                self.score += 1
                self._serve(toward_player=self._rng.random() < 0.5)
                return

        self.ball = [bx, by]

    def _draw_mode_picker(self, canvas) -> None:
        w, h = canvas.get_width(), canvas.get_height()
        cx = w // 2
        title = "PONG"
        draw_text(canvas, title, (cx - get_font(14).size(title)[0] // 2, 18), size=14, color=P1_COLOR)
        for i, label in enumerate(MODES):
            focused = i == self.mode_index
            text = f"> {label} <" if focused else label
            color = (255, 210, 140) if focused else (140, 140, 140)
            draw_text(canvas, text, (cx - get_font(9).size(text)[0] // 2, 48 + i * 16), size=9, color=color)
        detail = "stick vs computer" if self.mode_index == 0 else "left: stick   right: knob"
        draw_text(canvas, detail, (cx - get_font(7).size(detail)[0] // 2, 86), size=7, color=(160, 160, 160))
        hint = "stick: choose  knob push: start"
        draw_text(canvas, hint, (cx - get_font(7).size(hint)[0] // 2, h - 12), size=7, color=(120, 120, 120))

    def draw(self, canvas, ctx: Context) -> None:
        self._handle_input(ctx)
        self._step(ctx)

        clear(canvas)
        w, h = canvas.get_width(), canvas.get_height()
        if self.choosing:
            self._draw_mode_picker(canvas)
            return

        if self.two_player:
            draw_text(canvas, str(self.scores[0]), (w // 2 - 16, 2), size=8, color=P1_COLOR)
            draw_text(canvas, str(self.scores[1]), (w // 2 + 10, 2), size=8, color=P2_COLOR)
        else:
            draw_text(canvas, str(self.score), (w // 2 - 4, 2), size=8, color=(160, 160, 160))
        for y in range(0, h, 6):
            pygame.draw.rect(canvas, (60, 56, 52), (w // 2 - 1, y, 1, 3))

        player_x = PADDLE_MARGIN
        pygame.draw.rect(canvas, P1_COLOR, (player_x, self.player_y - PADDLE_H / 2, PADDLE_W, PADDLE_H))
        ai_x = w - PADDLE_MARGIN - PADDLE_W
        pygame.draw.rect(canvas, P2_COLOR, (ai_x, self.ai_y - PADDLE_H / 2, PADDLE_W, PADDLE_H))
        pygame.draw.circle(canvas, (214, 64, 48), (round(self.ball[0]), round(self.ball[1])), BALL_RADIUS)

        cx, cy = w // 2, h // 2
        if self._hsf.active:
            self._hsf.draw(canvas, self.score, ctx.now)
        elif self.game_over and self.two_player:
            label = "LEFT WINS" if self.winner == 0 else "RIGHT WINS"
            color = P1_COLOR if self.winner == 0 else P2_COLOR
            pygame.draw.rect(canvas, (10, 8, 8), (cx - 40, cy - 20, 80, 40))
            draw_text(canvas, label, (cx - get_font(10).size(label)[0] // 2, cy - 14), size=10, color=color)
            score = f"{self.scores[0]} - {self.scores[1]}"
            draw_text(canvas, score, (cx - get_font(8).size(score)[0] // 2, cy), size=8)
            draw_text(canvas, "push: rematch", (cx - 30, cy + 10), size=7, color=(160, 160, 160))
        elif self.game_over:
            pygame.draw.rect(canvas, (10, 8, 8), (cx - 34, cy - 26, 68, 56))
            draw_text(canvas, "game over", (cx - 24, cy - 22), size=9)
            draw_text(canvas, "push: retry", (cx - 28, cy - 8), size=7, color=(160, 160, 160))
            draw_best(canvas, GAME_ID, (cx - 28, cy + 4))
        elif self._paused:
            pygame.draw.rect(canvas, (10, 8, 8), (cx - 24, cy - 6, 48, 16))
            draw_text(canvas, "paused", (cx - 18, cy), size=10)
