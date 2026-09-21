"""Ambient NeoPixel color for the halo + underglow: ties to whichever lamp
state is live, so the deck reads at a glance from across the room, and
breathes for the states that need your attention (docs/HARDWARE.md: "all
twelve channels breathe and dim in software... makes NIGHT mode and the
blocked-state pulse possible" - this is that pulse, just on the WS2812B
strip instead of a PCA9685 channel).
"""
from __future__ import annotations

import math

from deck.state import State

RGB = tuple[int, int, int]

COLOR_BY_STATE: dict[State, RGB] = {
    State.READY: (30, 160, 70),
    State.WORKING: (200, 140, 30),
    State.SUBAGENTS: (200, 140, 30),
    State.BLOCKED_PERMISSION: (180, 40, 30),
    State.BLOCKED_INPUT: (180, 40, 30),
    State.COMPACTING: (200, 140, 30),
    State.DONE: (40, 110, 190),
    State.ERROR: (180, 40, 30),
    State.IDLE: (8, 8, 12),
    State.OFFLINE: (50, 50, 56),
    State.INTERRUPTED: (150, 0, 0),
}

PULSE_STATES = {State.BLOCKED_PERMISSION, State.BLOCKED_INPUT, State.ERROR, State.INTERRUPTED}
PULSE_PERIOD_SECONDS = 1.6
PULSE_FLOOR = 0.35  # breathes, never blinks fully off


def pixels_for_state(state: State, now: float, brightness: float, count: int) -> list[RGB]:
    base = COLOR_BY_STATE.get(state, (0, 0, 0))
    factor = max(0.0, min(1.0, brightness))
    if state in PULSE_STATES:
        phase = (math.sin(2 * math.pi * now / PULSE_PERIOD_SECONDS) + 1) / 2
        factor *= PULSE_FLOOR + (1 - PULSE_FLOOR) * phase
    scaled = tuple(max(0, min(255, int(c * factor))) for c in base)
    return [scaled] * count
