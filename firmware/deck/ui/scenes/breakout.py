from __future__ import annotations

import math
import random

import pygame

from deck.ui.gfx import clear, draw_text
from deck.ui.name_entry import HighScoreFlow, draw_best
from deck.ui.scenes.base import Context, Scene

GAME_ID = "breakout"

W, H = 160, 120
COLS = 8
ROWS = 5
BRICK_W = 18
BRICK_H = 5
BRICK_GAP = 2
BRICK_TOP = 14
PADDLE_W = 24
PADDLE_H = 3
PADDLE_Y = 110
PADDLE_SPEED = 110.0  # px/s, joystick
ENCODER_STEP = 8.0  # px per encoder detent
BALL_RADIUS = 2
BALL_SPEED_START = 70.0
BALL_SPEED_LEVEL_STEP = 10.0
BALL_SPEED_MAX = 140.0
LIVES = 3
MAX_DT = 0.05

# top row first: warm to cool, top rows are worth more
ROW_COLORS = [(214, 64, 48), (224, 122, 42), (240, 210, 90), (120, 200, 140), (120, 130, 220)]
ROW_POINTS = [5, 4, 3, 2, 1]


class BreakoutScene(Scene):
    """Encoder turns move the paddle a detent at a time, like a real paddle
    knob; joystick left/right moves it continuously. Encoder push launches
    the ball, and pauses/retries once it's in play. Three lives; clearing
    the wall starts the next level a little faster."""

    def __init__(self) -> None:
        self._rng = random.Random()
        self._hsf = HighScoreFlow(GAME_ID)
        self._reset()

    def on_enter(self, ctx: Context) -> None:
        self._reset()

    def _reset(self) -> None:
        self.score = 0
        self.lives = LIVES
        self.level = 1
        self.game_over = False
        self._paused = False
        self._hsf.reset()
        self.paddle_x = W / 2
        self._build_wall()
        self._hold_ball()

    def _build_wall(self) -> None:
        self.bricks: list[tuple[pygame.Rect, int]] = []
        for row in range(ROWS):
            for col in range(COLS):
                rect = pygame.Rect(
                    BRICK_GAP // 2 + col * (BRICK_W + BRICK_GAP), BRICK_TOP + row * (BRICK_H + BRICK_GAP), BRICK_W, BRICK_H
                )
                self.bricks.append((rect, row))

    def _hold_ball(self) -> None:
        self.held = True
        self.ball = [self.paddle_x, PADDLE_Y - BALL_RADIUS - 1]
        self.ball_v = [0.0, 0.0]

    def _launch(self) -> None:
        speed = min(BALL_SPEED_MAX, BALL_SPEED_START + (self.level - 1) * BALL_SPEED_LEVEL_STEP)
        angle = self._rng.uniform(-0.6, 0.6)
        self.ball_v = [speed * math.sin(angle), -speed * math.cos(angle)]
        self.held = False

    def _handle_input(self, ctx: Context) -> None:
        if self._hsf.active:
            self._hsf.handle_input(ctx.inputs, self.score)
            return

        if ctx.inputs.get("encoder_push_edge", False):
            if self.game_over:
                self._reset()
                return
            if self.held:
                self._launch()
            else:
                self._paused = not self._paused
        if self._paused or self.game_over:
            return

        edge = ctx.inputs.get("encoder_edge")
        if edge == "cw":
            self.paddle_x += ENCODER_STEP
        elif edge == "ccw":
            self.paddle_x -= ENCODER_STEP
        jx, _ = ctx.inputs.get("joystick", (0, 0))
        self.paddle_x += jx * PADDLE_SPEED * min(ctx.dt, MAX_DT)
        self.paddle_x = max(PADDLE_W / 2, min(W - PADDLE_W / 2, self.paddle_x))

    def _step(self, dt: float) -> None:
        if self._paused or self.game_over or self._hsf.active:
            return
        if self.held:
            self.ball = [self.paddle_x, PADDLE_Y - BALL_RADIUS - 1]
            return

        # Substep so a fast ball can't tunnel through a 5px brick in one frame.
        dt = min(dt, MAX_DT)
        distance = math.hypot(*self.ball_v) * dt
        steps = max(1, math.ceil(distance / 2))
        for _ in range(steps):
            if self._substep(dt / steps):
                return

    def _substep(self, dt: float) -> bool:
        """Returns True if the ball was lost or the wall cleared, ending this frame's motion."""
        px, py = self.ball
        bx = px + self.ball_v[0] * dt
        by = py + self.ball_v[1] * dt

        if bx <= BALL_RADIUS or bx >= W - BALL_RADIUS:
            bx = max(BALL_RADIUS, min(W - BALL_RADIUS, bx))
            self.ball_v[0] *= -1
        if by <= BALL_RADIUS:
            by = BALL_RADIUS
            self.ball_v[1] = abs(self.ball_v[1])

        paddle_left = self.paddle_x - PADDLE_W / 2
        if (
            self.ball_v[1] > 0
            and PADDLE_Y - BALL_RADIUS <= by <= PADDLE_Y + PADDLE_H
            and paddle_left - BALL_RADIUS <= bx <= paddle_left + PADDLE_W + BALL_RADIUS
        ):
            # Where it lands on the paddle steers it, same as Pong.
            offset = max(-1.0, min(1.0, (bx - self.paddle_x) / (PADDLE_W / 2)))
            speed = math.hypot(*self.ball_v)
            # up to ~60 degrees off vertical; the jitter stops a dead-centre
            # hit looping straight up and down one cleared column forever
            angle = offset * 1.05 + self._rng.uniform(-0.08, 0.08)
            self.ball_v = [speed * math.sin(angle), -speed * math.cos(angle)]
            by = PADDLE_Y - BALL_RADIUS

        ball_rect = pygame.Rect(round(bx) - BALL_RADIUS, round(by) - BALL_RADIUS, BALL_RADIUS * 2, BALL_RADIUS * 2)
        for i, (rect, row) in enumerate(self.bricks):
            if not rect.colliderect(ball_rect):
                continue
            del self.bricks[i]
            self.score += ROW_POINTS[row]
            # Came in from the side if it was already level with the brick last step.
            if rect.top - BALL_RADIUS < py < rect.bottom + BALL_RADIUS:
                self.ball_v[0] *= -1
            else:
                self.ball_v[1] *= -1
            break

        self.ball = [bx, by]

        if not self.bricks:
            self.level += 1
            self._build_wall()
            self._hold_ball()
            return True

        if by > H + BALL_RADIUS:
            self.lives -= 1
            if self.lives <= 0:
                self.game_over = True
                self._hsf.on_game_over(self.score)
            else:
                self._hold_ball()
            return True
        return False

    def draw(self, canvas, ctx: Context) -> None:
        self._handle_input(ctx)
        self._step(ctx.dt)

        clear(canvas)
        w, h = canvas.get_width(), canvas.get_height()
        draw_text(canvas, f"{self.score}", (2, 1), size=8, color=(160, 160, 160))
        draw_text(canvas, f"L{self.level}", (w // 2 - 6, 1), size=8, color=(120, 120, 120))
        for i in range(self.lives):
            pygame.draw.rect(canvas, (255, 178, 92), (w - 8 - i * 7, 4, 5, 3))

        for rect, row in self.bricks:
            pygame.draw.rect(canvas, ROW_COLORS[row], rect)

        pygame.draw.rect(canvas, (255, 178, 92), (round(self.paddle_x - PADDLE_W / 2), PADDLE_Y, PADDLE_W, PADDLE_H))
        pygame.draw.circle(canvas, (235, 235, 235), (round(self.ball[0]), round(self.ball[1])), BALL_RADIUS)

        cx, cy = w // 2, h // 2 + 10
        if self._hsf.active:
            self._hsf.draw(canvas, self.score, ctx.now)
        elif self.game_over:
            pygame.draw.rect(canvas, (10, 8, 8), (cx - 34, cy - 26, 68, 56))
            draw_text(canvas, "game over", (cx - 24, cy - 22), size=9)
            draw_text(canvas, "push: retry", (cx - 28, cy - 8), size=7, color=(160, 160, 160))
            draw_best(canvas, GAME_ID, (cx - 28, cy + 4))
        elif self._paused:
            pygame.draw.rect(canvas, (10, 8, 8), (cx - 24, cy - 6, 48, 16))
            draw_text(canvas, "paused", (cx - 18, cy), size=10)
        elif self.held:
            draw_text(canvas, "push: launch", (cx - 30, cy + 8), size=7, color=(160, 160, 160))
