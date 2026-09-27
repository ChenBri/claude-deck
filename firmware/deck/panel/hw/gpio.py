"""Real-GPIO inputs: APPROVE, DENY, the mushroom, and the encoder. These
stay off the I2C expanders because they're latency-sensitive (the encoder
would drop detents at a 30fps poll), so a thread waits on kernel edge
events and hands them to EdgeDecoder, which is pure and tested.

Every line is on GPIO bank 3 (docs/HARDWARE.md pin map), active low with
the SoC's internal pull-up. Line offset within the bank is letter * 8 +
number, e.g. GPIO3_C4 -> 2 * 8 + 4 = 20.
"""
from __future__ import annotations

import queue
import threading
import time

from deck.panel.base import InputEvent

GPIO_CHIP = "/dev/gpiochip3"  # verify on first boot: bank 3's chip on Radxa's kernel
LINES = {
    "APPROVE": 1,  # pin 11, GPIO3_A1
    "PANIC": 7,  # pin 36, GPIO3_A7
    "DENY": 8,  # pin 15, GPIO3_B0
    "ENC_B": 9,  # pin 16, GPIO3_B1
    "ENC_PUSH": 10,  # pin 18, GPIO3_B2
    "ENC_A": 20,  # pin 7, GPIO3_C4
}
DEBOUNCE_SECONDS = 0.02

# (previous AB, current AB) -> step. Any other pair is bounce or a skipped
# state and counts for nothing.
_QUADRATURE = {
    (0b11, 0b01): 1, (0b01, 0b00): 1, (0b00, 0b10): 1, (0b10, 0b11): 1,
    (0b11, 0b10): -1, (0b10, 0b00): -1, (0b00, 0b01): -1, (0b01, 0b11): -1,
}
_DETENT = 0b11  # PEC11R-4215F-S0024: both contacts open at rest, pulled high


class EdgeDecoder:
    """Edges in, InputEvents out. Buttons and the mushroom are debounced by
    accepting an edge at once and then ignoring that line for
    DEBOUNCE_SECONDS; settle() catches a line that ended up somewhere other
    than its last accepted level once the bouncing stops."""

    _SWITCHES = ("APPROVE", "DENY", "PANIC", "ENC_PUSH")

    def __init__(self, invert_encoder: bool = False) -> None:
        self.invert_encoder = invert_encoder
        self._raw = {name: 1 for name in LINES}
        self._accepted = {name: 1 for name in self._SWITCHES}
        self._accepted_at = {name: -1.0 for name in self._SWITCHES}
        self._last_edge_at = {name: -1.0 for name in self._SWITCHES}
        self._ab = _DETENT
        self._steps = 0

    def seed(self, levels: dict[str, int]) -> list[InputEvent]:
        """Initial levels at start-up. A mushroom already latched at boot
        must still stop everything, so it reports straight away."""
        self._raw.update(levels)
        for name in self._SWITCHES:
            self._accepted[name] = self._raw[name]
        self._ab = (self._raw["ENC_A"] << 1) | self._raw["ENC_B"]
        return [InputEvent("panic", "panic", True)] if self._raw["PANIC"] == 0 else []

    def feed(self, name: str, level: int, t: float) -> list[InputEvent]:
        self._raw[name] = level
        if name in ("ENC_A", "ENC_B"):
            return self._quadrature()
        self._last_edge_at[name] = t
        if t - self._accepted_at[name] < DEBOUNCE_SECONDS or level == self._accepted[name]:
            return []
        return self._accept(name, level, t)

    def settle(self, t: float) -> list[InputEvent]:
        events: list[InputEvent] = []
        for name in self._SWITCHES:
            if self._raw[name] != self._accepted[name] and t - self._last_edge_at[name] >= DEBOUNCE_SECONDS:
                events += self._accept(name, self._raw[name], t)
        return events

    def _accept(self, name: str, level: int, t: float) -> list[InputEvent]:
        self._accepted[name] = level
        self._accepted_at[name] = t
        pressed = level == 0
        if name in ("APPROVE", "DENY"):
            return [InputEvent("button", name)] if pressed else []
        if name == "PANIC":
            return [InputEvent("panic", "panic", pressed)]
        return [InputEvent("encoder", "push_down" if pressed else "push_up")]

    def _quadrature(self) -> list[InputEvent]:
        ab = (self._raw["ENC_A"] << 1) | self._raw["ENC_B"]
        self._steps += _QUADRATURE.get((self._ab, ab), 0)
        self._ab = ab
        if ab != _DETENT:
            return []
        steps, self._steps = self._steps, 0
        if abs(steps) < 2:  # a bounce that came back to rest
            return []
        clockwise = (steps > 0) != self.invert_encoder
        return [InputEvent("encoder", "cw" if clockwise else "ccw")]


class GpioInputs:
    """Owns the gpiod line request and the thread reading it. Untestable off
    the board; everything with logic in it is in EdgeDecoder."""

    def __init__(self, decoder: EdgeDecoder, chip: str = GPIO_CHIP, lines: dict[str, int] = LINES) -> None:
        import gpiod
        from gpiod.line import Bias, Direction, Edge, Value

        self._decoder = decoder
        self._by_offset = {offset: name for name, offset in lines.items()}
        settings = gpiod.LineSettings(direction=Direction.INPUT, edge_detection=Edge.BOTH, bias=Bias.PULL_UP)
        self._request = gpiod.request_lines(chip, consumer="claude-deck", config={tuple(lines.values()): settings})
        values = self._request.get_values(list(lines.values()))
        levels = {name: 1 if v == Value.ACTIVE else 0 for name, v in zip(lines, values)}
        self._events: queue.SimpleQueue[InputEvent] = queue.SimpleQueue()
        for ev in decoder.seed(levels):
            self._events.put(ev)
        self._rising = gpiod.EdgeEvent.Type.RISING_EDGE
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, name="deck-gpio", daemon=True)
        self._thread.start()

    def _run(self) -> None:
        from datetime import timedelta

        while not self._stop.is_set():
            if self._request.wait_edge_events(timedelta(milliseconds=10)):
                for edge in self._request.read_edge_events():
                    name = self._by_offset.get(edge.line_offset)
                    if name is None:
                        continue
                    level = 1 if edge.event_type == self._rising else 0
                    # kernel edge timestamps are CLOCK_MONOTONIC, same clock as time.monotonic()
                    for ev in self._decoder.feed(name, level, edge.timestamp_ns / 1e9):
                        self._events.put(ev)
            for ev in self._decoder.settle(time.monotonic()):
                self._events.put(ev)

    def drain(self) -> list[InputEvent]:
        out = []
        while True:
            try:
                out.append(self._events.get_nowait())
            except queue.Empty:
                return out

    def close(self) -> None:
        self._stop.set()
        self._thread.join(timeout=1.0)
        self._request.release()
