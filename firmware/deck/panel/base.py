"""Abstract Panel: lamps, meters, pixels, inputs, screen surface.

RealPanel and SimPanel both implement this so the rendering and state-machine
code above never knows which one it is talking to.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

LAMPS = ("READY", "WORKING", "BLOCKED", "DONE", "LINK")
METERS = ("CONTEXT", "FIVE_HOUR")
BUTTON_LEDS = ("APPROVE", "DENY")
MECH_KEYS = ("CLD", "NEW", "PLAN", "MIC")
TOGGLES = ("MUTE", "NIGHT", "AUTO_ACCEPT")
ROTARY_POSITIONS = ("1", "2", "3", "4", "5", "ALL")
GB_BUTTONS = ("A", "B", "START", "SELECT")  # Game Boy app only, see ui/scenes/gameboy.py

# Logical canvas the scene compositor draws into; the panel scales it to the
# physical 320x240 display (2x, nearest-neighbour).
CANVAS_WIDTH = 160
CANVAS_HEIGHT = 120

# The Game Boy app draws into its own canvas instead: native GB resolution,
# scaled to fit the same physical panel letterboxed rather than 2x-filled.
GB_CANVAS_WIDTH = 160
GB_CANVAS_HEIGHT = 144

PIXEL_COUNT = 30  # WS2812B: halo + underglow, per docs/HARDWARE.md


@dataclass
class InputEvent:
    kind: str  # "button" | "toggle" | "rotary" | "encoder" | "joystick" | "mech_key" | "gb_button" | "panic"
    name: str
    value: object = None


class Panel(ABC):
    @abstractmethod
    def set_lamp(self, name: str, level: float) -> None:
        """name in LAMPS, level 0..1."""

    @abstractmethod
    def set_meter(self, name: str, level: float) -> None:
        """name in METERS, level 0..1."""

    @abstractmethod
    def set_pixels(self, colors: list[tuple[int, int, int]]) -> None:
        """len(colors) == PIXEL_COUNT, each an (r, g, b) 0..255 tuple."""

    @abstractmethod
    def set_button_led(self, name: str, level: float) -> None:
        """name in BUTTON_LEDS, level 0..1. 0 means dead: live only while a
        prompt is pending; NIGHT mode scales the "on" level down from there."""

    @abstractmethod
    def present(self, canvas) -> None:
        """Push one composited frame to the device: lamps, meters, pixels, and
        `canvas` (a CANVAS_WIDTH x CANVAS_HEIGHT surface owned by the renderer,
        scaled and CRT-processed via ui.render.compose_output)."""

    @abstractmethod
    def poll_inputs(self) -> list[InputEvent]:
        """Non-blocking: return every input event since the last poll."""

    @abstractmethod
    def close(self) -> None:
        ...
