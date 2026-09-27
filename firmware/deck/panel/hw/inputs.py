"""Turns raw expander and ADC readings into the same InputEvents SimPanel
produces, so main.py can't tell the panels apart. Pure: RealPanel feeds it
one reading per frame.

Pin assignments are docs/HARDWARE.md's MCP23017 #1 and #2 tables.
"""
from __future__ import annotations

from deck.panel.base import EFFORT_POSITIONS, InputEvent, ROTARY_POSITIONS
from deck.panel.hw.mcp23017 import bit

SELECTOR_BITS = [bit("A", i) for i in range(6)]  # MCP #1, positions 1-5 then ALL
MECH_KEY_BITS = {"CLD": bit("B", 0), "NEW": bit("B", 1), "PLAN": bit("B", 2), "MIC": bit("B", 3)}
TOGGLE_BITS = {"MUTE": bit("B", 4), "NIGHT": bit("B", 5), "AUTO_ACCEPT": bit("B", 6)}

JOY_PUSH_BIT = bit("B", 0)  # MCP #2
GB_BITS = {"A": bit("B", 1), "B": bit("B", 2), "START": bit("B", 3), "SELECT": bit("B", 4)}
EFFORT_BITS = [bit("B", 5), bit("B", 6), bit("B", 7), bit("A", 0), bit("A", 1)]

EDGE_ON = 0.6  # joystick deflection that counts as a menu "press"
EDGE_OFF = 0.3  # ...and has to come back under this before it can fire again
VOLUME_SMOOTHING = 0.3

DEFAULT_JOYSTICK = {"center_x": 0.5, "center_y": 0.5, "deadzone": 0.12, "invert_x": False, "invert_y": False}


def _set(mask: int, b: int) -> bool:
    return bool(mask >> b & 1)


def _single(mask: int, bits: list[int]) -> int | None:
    """Index of the one closed contact, or None mid-rotation (break-before-
    make: nothing closed) or on a fault (more than one closed)."""
    closed = [i for i, b in enumerate(bits) if _set(mask, b)]
    return closed[0] if len(closed) == 1 else None


def axis(fraction: float, center: float, deadzone: float) -> float:
    """ADC fraction 0..1 -> -1..1, exactly 0 inside the deadzone so games
    that only read the sign stay still at rest."""
    span = max(center, 1 - center) or 0.5
    value = (fraction - center) / span
    if abs(value) < deadzone:
        return 0.0
    scaled = (abs(value) - deadzone) / (1 - deadzone)
    return max(-1.0, min(1.0, scaled if value > 0 else -scaled))


class ExpanderInputs:
    """Debounces both MCP23017s by requiring the same reading on two frames
    in a row (~66ms at 30fps), then reports what changed. The first stable
    reading reports the positional controls (selector, effort, toggles) so
    the deck starts in sync with the physical panel; momentary ones only
    ever report presses."""

    def __init__(self) -> None:
        self._pending: tuple[int, int] | None = None
        self._stable: tuple[int, int] | None = None
        self._selector: str | None = None
        self._effort: str | None = None

    def update(self, mcp1: int, mcp2: int) -> list[InputEvent]:
        reading = (mcp1, mcp2)
        if reading != self._pending:
            self._pending = reading
            return []
        if reading == self._stable:
            return []
        prev1, prev2 = self._stable if self._stable is not None else (None, None)
        self._stable = reading
        return self._diff(prev1, prev2, mcp1, mcp2)

    def _diff(self, prev1, prev2, mcp1: int, mcp2: int) -> list[InputEvent]:
        events: list[InputEvent] = []
        first = prev1 is None

        position = _single(mcp1, SELECTOR_BITS)
        if position is not None and ROTARY_POSITIONS[position] != self._selector:
            self._selector = ROTARY_POSITIONS[position]
            events.append(InputEvent("rotary", "selector", self._selector))

        position = _single(mcp2, EFFORT_BITS)
        if position is not None and EFFORT_POSITIONS[position] != self._effort:
            self._effort = EFFORT_POSITIONS[position]
            events.append(InputEvent("rotary", "effort", self._effort))

        for name, b in TOGGLE_BITS.items():
            if first or _set(mcp1, b) != _set(prev1, b):
                events.append(InputEvent("toggle", name, _set(mcp1, b)))

        if first:
            return events  # a key held at boot is not a press

        for name, b in MECH_KEY_BITS.items():
            if _set(mcp1, b) and not _set(prev1, b):
                events.append(InputEvent("mech_key", name))
        if _set(mcp2, JOY_PUSH_BIT) and not _set(prev2, JOY_PUSH_BIT):
            events.append(InputEvent("joystick", "push_edge", True))
        for name, b in GB_BITS.items():
            if _set(mcp2, b) != _set(prev2, b):
                events.append(InputEvent("gb_button", name, _set(mcp2, b)))
        return events


class AnalogInputs:
    """Joystick axes, menu edges from them, and the volume knob. Emits axis
    and volume every frame, the same as SimPanel."""

    def __init__(self, joystick_settings: dict | None = None) -> None:
        self.cfg = {**DEFAULT_JOYSTICK, **(joystick_settings or {})}
        self._armed = {"x": True, "y": True}
        self._volume: float | None = None

    def update(self, x_raw: float | None, y_raw: float | None, vol_raw: float | None) -> list[InputEvent]:
        events: list[InputEvent] = []
        cfg = self.cfg
        x = 0.0 if x_raw is None else axis(x_raw, cfg["center_x"], cfg["deadzone"])
        y = 0.0 if y_raw is None else axis(y_raw, cfg["center_y"], cfg["deadzone"])
        if cfg["invert_x"]:
            x = -x
        if cfg["invert_y"]:
            y = -y
        events.append(InputEvent("joystick", "axis", (x, y)))

        edges = set()
        for name, value, neg, pos in (("x", x, "left", "right"), ("y", y, "up", "down")):
            if self._armed[name] and abs(value) >= EDGE_ON:
                edges.add(pos if value > 0 else neg)
                self._armed[name] = False
            elif abs(value) <= EDGE_OFF:
                self._armed[name] = True
        if edges:
            events.append(InputEvent("joystick", "edge", edges))

        if vol_raw is not None:
            self._volume = vol_raw if self._volume is None else self._volume + VOLUME_SMOOTHING * (vol_raw - self._volume)
            events.append(InputEvent("volume", "level", round(self._volume, 3)))
        return events
