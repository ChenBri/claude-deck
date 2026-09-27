from __future__ import annotations

import random

import pygame

from deck.ui.gfx import clear, draw_text
from deck.ui.name_entry import HighScoreFlow, draw_best
from deck.ui.scenes.base import Context, Scene

GAME_ID = "pong"

PADDLE_W = 3
PADDLE_H = 20
PADDLE_MARGIN = 6
PADDLE_SPEED = 90.0  # px/s, player
AI_SPEED = 55.0  # px/s, deliberately slower than the player can move - beatable
BALL_RADIUS = 2
BALL_SPEED_START = 55.0
BALL_SPEED_MAX = 110.0
BALL_SPEED_STEP = 4.0  # per paddle hit


class PongScene(Scene):
    """Joystick up/down moves the player's paddle (left edge), continuously,
    like a real analog stick would. Single life: missing the ball ends the
    round, score is how many times you got it past the AI first. Encoder
    push pauses/retries."""

    def __init__(self) -> None:
        self._rng = random.Random()
        self._hsf = HighScoreFlow(GAME_ID)
        self._reset()

    def _reset(self) -> None:
        self.score = 0
        self.game_over = False
        self._paused = False
        self._hsf.reset()
        self.player_y = 60.0
        self.ai_y = 60.0
        self._serve(toward_player=False)

    def _serve(self, toward_player: bool) -> None:
        self.ball = [80.0, 60.0]
        angle = self._rng.uniform(-0.5, 0.5)
        vx = -BALL_SPEED_START if toward_player else BALL_SPEED_START
        self.ball_v = [vx, BALL_SPEED_START * angle]

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

        _, jy = ctx.inputs.get("joystick", (0, 0))
        h = 120
        self.player_y = max(PADDLE_H / 2, min(h - PADDLE_H / 2, self.player_y + jy * PADDLE_SPEED * ctx.dt))

    def _step(self, ctx: Context) -> None:
        if self._paused or self.game_over or self._hsf.active:
            return
        w, h = 160, 120

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
                self.score += 1
                self._serve(toward_player=self._rng.random() < 0.5)
                return

        self.ball = [bx, by]

    def draw(self, canvas, ctx: Context) -> None:
        self._handle_input(ctx)
        self._step(ctx)

        clear(canvas)
        w, h = canvas.get_width(), canvas.get_height()
        draw_text(canvas, str(self.score), (w // 2 - 4, 2), size=8, color=(160, 160, 160))
        for y in range(0, h, 6):
            pygame.draw.rect(canvas, (60, 56, 52), (w // 2 - 1, y, 1, 3))

        player_x = PADDLE_MARGIN
        pygame.draw.rect(canvas, (255, 178, 92), (player_x, self.player_y - PADDLE_H / 2, PADDLE_W, PADDLE_H))
        ai_x = w - PADDLE_MARGIN - PADDLE_W
        pygame.draw.rect(canvas, (120, 130, 220), (ai_x, self.ai_y - PADDLE_H / 2, PADDLE_W, PADDLE_H))
        pygame.draw.circle(canvas, (214, 64, 48), (round(self.ball[0]), round(self.ball[1])), BALL_RADIUS)

        if self._hsf.active:
            self._hsf.draw(canvas, self.score, ctx.now)
        elif self.game_over:
            cx, cy = w // 2, h // 2
            pygame.draw.rect(canvas, (10, 8, 8), (cx - 34, cy - 26, 68, 56))
            draw_text(canvas, "game over", (cx - 24, cy - 22), size=9)
            draw_text(canvas, "push: retry", (cx - 28, cy - 8), size=7, color=(160, 160, 160))
            draw_best(canvas, GAME_ID, (cx - 28, cy + 4))
        elif self._paused:
            cx, cy = w // 2, h // 2
            pygame.draw.rect(canvas, (10, 8, 8), (cx - 24, cy - 6, 48, 16))
            draw_text(canvas, "paused", (cx - 18, cy), size=10)
