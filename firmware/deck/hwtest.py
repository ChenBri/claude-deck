"""Hardware test (Settings > hardware test): for bring-up on the bench.

Inputs: every InputEvent is recorded and shown live, so a miswired switch
is obvious the moment you touch it. Outputs: run on an automatic loop, one
at a time and named on screen - each lamp, each button LED, each meter
swept 0 -> 100% -> 0, then an R/G/B chase down the pixel strip - so a dead
or swapped channel is obvious too.

Momentary inputs (APPROVE, DENY, mech keys) are never forwarded to the
daemon while this is showing; main.py enforces that. The mushroom still
works and still takes the screen over, by design.

Exit is a double push on the encoder, since every single input here is
something to test, joystick push included.
"""
from __future__ import annotations

from deck.panel.base import BUTTON_LEDS, LAMPS, METERS

DOUBLE_PUSH_SECONDS = 0.5
FLASH_SECONDS = 0.4

_STEPS: list[tuple[str, str, float]] = (
    [("lamp", name, 0.6) for name in LAMPS]
    + [("led", name, 0.6) for name in BUTTON_LEDS]
    + [("meter", name, 2.0) for name in METERS]
    + [("pixels", "chase", 3.0)]
)
_CYCLE_SECONDS = sum(d for _, _, d in _STEPS)
_CHASE_COLORS = ((255, 0, 0), (0, 255, 0), (0, 0, 255))


class HardwareTest:
    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.flashes: dict[str, float] = {}
        self.held: set[str] = set()
        self.toggles: dict[str, bool] = {}
        self.selector: str | None = None
        self.effort: str | None = None
        self.encoder_count = 0
        self.joystick = (0, 0)
        self.volume: float | None = None
        self.exit_requested = False
        self._last_push: float | None = None
        self._started: float | None = None

    def observe(self, ev, now: float) -> bool:
        """Record one input event. Returns True on a momentary press, so the
        caller can click the speaker and prove audio at the same time."""
        kind, name = ev.kind, ev.name
        if kind in ("button", "mech_key"):
            self.flashes[name] = now
            return True
        if kind == "gb_button":
            if ev.value:
                self.held.add(name)
                return True
            self.held.discard(name)
        elif kind == "toggle":
            self.toggles[name] = bool(ev.value)
        elif kind == "rotary":
            if name == "effort":
                self.effort = ev.value
            else:
                self.selector = ev.value
        elif kind == "volume":
            self.volume = float(ev.value)
        elif kind == "joystick":
            if name == "axis":
                self.joystick = tuple(ev.value)
            elif name == "push_edge":
                self.flashes["JOY"] = now
                return True
        elif kind == "encoder":
            if name == "cw":
                self.encoder_count += 1
            elif name == "ccw":
                self.encoder_count -= 1
            elif name == "push_down":
                if self._last_push is not None and now - self._last_push <= DOUBLE_PUSH_SECONDS:
                    self.exit_requested = True
                self._last_push = now
                self.flashes["ENC"] = now
                return True
        return False

    def flashing(self, name: str, now: float) -> bool:
        at = self.flashes.get(name)
        return at is not None and now - at < FLASH_SECONDS

    def outputs(self, now: float, pixel_count: int) -> dict:
        """What every output should show this frame. Exactly one output is
        exercised at a time; everything else is off."""
        if self._started is None:
            self._started = now
        t = (now - self._started) % _CYCLE_SECONDS

        out = {
            "label": "",
            "lamps": {n: 0.0 for n in LAMPS},
            "leds": {n: 0.0 for n in BUTTON_LEDS},
            "meters": {n: 0.0 for n in METERS},
            "pixels": [(0, 0, 0)] * pixel_count,
        }
        for kind, name, duration in _STEPS:
            if t >= duration:
                t -= duration
                continue
            phase = t / duration
            if kind == "lamp":
                out["lamps"][name] = 1.0
                out["label"] = f"lamp {name}"
            elif kind == "led":
                out["leds"][name] = 1.0
                out["label"] = f"led {name}"
            elif kind == "meter":
                level = 1 - abs(2 * phase - 1)  # 0 -> 1 -> 0
                out["meters"][name] = level
                out["label"] = f"meter {name} {round(level * 100):3d}%"
            else:
                pass_index = min(int(phase * len(_CHASE_COLORS)), len(_CHASE_COLORS) - 1)
                lit = int(phase * len(_CHASE_COLORS) * pixel_count) % pixel_count
                pixels = list(out["pixels"])
                pixels[lit] = _CHASE_COLORS[pass_index]
                out["pixels"] = pixels
                out["label"] = f"pixel {lit + 1}/{pixel_count} {'RGB'[pass_index]}"
            break
        return out
