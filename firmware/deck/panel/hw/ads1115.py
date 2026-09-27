"""ADS1115 16-bit ADC: joystick X/Y on A0/A1, volume pot on A2.

Single-shot conversions, round-robin, never blocking the frame: `poll()`
reads the conversion started on the previous call, stores it, and starts
the next channel. At 860 samples/s a conversion takes ~1.2ms, far inside a
33ms frame, so every channel refreshes every len(channels) frames.
"""
from __future__ import annotations

CONVERSION = 0x00
CONFIG = 0x01

FULL_SCALE_VOLTS = 4.096  # PGA setting below; the pots only ever reach 3.3V
SUPPLY_VOLTS = 3.3


def config_word(channel: int) -> int:
    return (
        0x8000  # OS: start a single conversion
        | ((0b100 + channel) << 12)  # MUX: AINx against GND
        | (0b001 << 9)  # PGA: +-4.096V
        | (1 << 8)  # MODE: single-shot
        | (0b111 << 5)  # DR: 860 SPS
        | 0b11  # comparator off
    )


def to_fraction(raw: int) -> float:
    """Signed 16-bit reading -> 0..1 of the 3.3V supply the pots sweep."""
    if raw >= 0x8000:
        raw -= 0x10000
    volts = max(0, raw) * FULL_SCALE_VOLTS / 0x8000
    return max(0.0, min(1.0, volts / SUPPLY_VOLTS))


class ADS1115:
    def __init__(self, bus, address: int = 0x48, channels: tuple[int, ...] = (0, 1, 2)) -> None:
        self.bus = bus
        self.address = address
        self.channels = channels
        self.values: dict[int, float | None] = {c: None for c in channels}
        self._index = 0
        self._start(self.channels[0])

    def _start(self, channel: int) -> None:
        word = config_word(channel)
        self.bus.write_i2c_block_data(self.address, CONFIG, [word >> 8, word & 0xFF])

    def poll(self) -> dict[int, float | None]:
        hi, lo = self.bus.read_i2c_block_data(self.address, CONVERSION, 2)
        self.values[self.channels[self._index]] = to_fraction((hi << 8) | lo)
        self._index = (self._index + 1) % len(self.channels)
        self._start(self.channels[self._index])
        return self.values
