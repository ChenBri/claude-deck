"""Analog meter calibration: a 5-point curve per meter mapping the reading
the deck wants to show (0, 25, 50, 75, 100%) to the PWM duty that actually
puts the needle there. The trimpot sets full scale in hardware; the curve
corrects what's left, since cheap VU movements are rarely linear.

Curves live in settings.yaml under meter_cal, written by the wizard below
(Settings > calibrate meters) and applied to every set_meter() in main.py.
"""
from __future__ import annotations

from deck.panel.base import METERS

POINTS = (0.0, 0.25, 0.5, 0.75, 1.0)
NUDGE = 0.005


def default_curve() -> list[float]:
    return list(POINTS)


def valid_curve(curve) -> bool:
    return (
        isinstance(curve, (list, tuple))
        and len(curve) == len(POINTS)
        and all(isinstance(v, (int, float)) for v in curve)
    )


def apply(level: float, curve) -> float:
    """Nominal level 0..1 -> calibrated duty 0..1. A missing or malformed
    curve passes the level straight through."""
    level = max(0.0, min(1.0, level))
    if not valid_curve(curve):
        return level
    segment = min(int(level * (len(POINTS) - 1)), len(POINTS) - 2)
    span = POINTS[segment + 1] - POINTS[segment]
    t = (level - POINTS[segment]) / span
    lo, hi = curve[segment], curve[segment + 1]
    return max(0.0, min(1.0, lo + (hi - lo) * t))


class CalibrationWizard:
    """pick (rotate: which meter) -> trimpot (needle parked at raw 100%,
    set full scale with the trimpot) -> point 0..4 (rotate nudges that
    point's duty) -> done. Nothing is saved until done; main.py writes
    `curves` back to settings when `finished` goes True."""

    def __init__(self) -> None:
        self.start({})

    def start(self, saved: dict) -> None:
        saved = saved or {}
        self.curves = {
            m: list(saved[m]) if valid_curve(saved.get(m)) else default_curve() for m in METERS
        }
        self.meter_index = 0
        self.step = "pick"
        self.point = 0
        self.finished = False

    @property
    def meter(self) -> str:
        return METERS[self.meter_index]

    def rotate(self, direction: int) -> None:
        if self.step == "pick":
            self.meter_index = (self.meter_index + direction) % len(METERS)
        elif self.step == "point":
            curve = self.curves[self.meter]
            # Keep the curve monotonic: a point never passes its neighbours.
            lo = curve[self.point - 1] if self.point > 0 else 0.0
            hi = curve[self.point + 1] if self.point < len(curve) - 1 else 1.0
            value = curve[self.point] + direction * NUDGE
            curve[self.point] = round(max(lo, min(hi, value)), 4)

    def push(self) -> None:
        if self.step == "pick":
            self.step = "trimpot"
        elif self.step == "trimpot":
            self.step = "point"
            self.point = 0
        elif self.step == "point":
            if self.point < len(POINTS) - 1:
                self.point += 1
            else:
                self.step = "done"
        elif self.step == "done":
            self.finished = True

    def drive(self) -> float:
        """Raw duty for the meter under calibration this frame."""
        if self.step == "trimpot":
            return 1.0
        if self.step == "point":
            return self.curves[self.meter][self.point]
        return 0.0
