"""Ambient mode: what the screen shows while nothing needs you. A rotation
of data cards (ui/cards.py) with a mascot-life scene (ui/scenes/life.py)
after every couple of cards. Replaces the old IDLE dashboard and its
attract-mode snake.

Shown for IDLE straight away, and for READY/DONE once the session has been
quiet for `ambient_after_seconds`. Purely a choice of what to draw: the
state machine, lamps, LEDs and approve logic never see it, and any state
that wants you (or live work) gets the normal scene back immediately
because SceneManager re-decides every frame.
"""
from __future__ import annotations

import pygame

from deck.screen import wall_clock
from deck.state import State
from deck.ui import cards
from deck.ui.scenes import life
from deck.ui.scenes.base import Context, Scene

CARD_ORDER = ("clock", "weather", "usage", "git", "five_hour")
CARDS_PER_MASCOT = 2
FADE_SECONDS = 0.25

DEFAULT_AFTER_SECONDS = 60
DEFAULT_CARD_SECONDS = 20
DEFAULT_MASCOT_SECONDS = 60

_QUIET_STATES = {State.READY, State.DONE}


def ambient_due(state: State, session, now: float, after_seconds: float) -> bool:
    if state == State.IDLE:
        return True
    return state in _QUIET_STATES and session is not None and now - session.last_event_at >= after_seconds


def build_cycle(available: set[str]) -> list[str]:
    items: list[str] = []
    shown = 0
    for card in CARD_ORDER:
        if card not in available:
            continue
        items.append(card)
        shown += 1
        if shown % CARDS_PER_MASCOT == 0:
            items.append("mascot")
    if not items or items[-1] != "mascot":
        items.append("mascot")
    return items


class Rotation:
    """Which item is up and for how long it has been. The cycle is rebuilt
    from whatever data is available each frame, so a card whose data goes
    missing is skipped rather than shown empty."""

    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.item: str | None = None
        self.index = -1
        self.started = 0.0

    def update(self, now: float, available: set[str], card_seconds: float, mascot_seconds: float, skip: int = 0):
        cycle = build_cycle(available)
        if self.item is None:
            self._go(cycle, 0, now)
        elif skip:
            self._go(cycle, self.index + skip, now)
        else:
            duration = mascot_seconds if self.item == "mascot" else card_seconds
            if self.item not in cycle or now - self.started >= duration:
                self._go(cycle, self.index + 1, now)
        return self.item, now - self.started

    def _go(self, cycle: list[str], index: int, now: float) -> None:
        self.index = index % len(cycle)
        self.item = cycle[self.index]
        self.started = now


class AmbientScene(Scene):
    def __init__(self) -> None:
        self.rotation = Rotation()

    def on_enter(self, ctx: Context) -> None:
        self.rotation.reset()  # always open on the clock

    def draw(self, canvas, ctx: Context) -> None:
        settings = ctx.settings
        edge = ctx.inputs.get("encoder_edge")
        skip = 1 if edge == "cw" else -1 if edge == "ccw" else 0
        item, elapsed = self.rotation.update(
            ctx.now,
            cards.available(ctx.idle_info),
            float(settings.get("ambient_card_seconds", DEFAULT_CARD_SECONDS)),
            float(settings.get("ambient_mascot_seconds", DEFAULT_MASCOT_SECONDS)),
            skip,
        )

        clock = wall_clock(ctx.idle_info)
        if item == "mascot":
            life.draw_life(canvas, ctx, clock)
        else:
            cards.draw_card(item, canvas, ctx.idle_info, clock, ctx.now)

        if elapsed < FADE_SECONDS:
            k = round(255 * elapsed / FADE_SECONDS)
            canvas.fill((k, k, k), special_flags=pygame.BLEND_RGB_MULT)
