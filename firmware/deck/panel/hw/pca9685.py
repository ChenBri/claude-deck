"""PCA9685 16-channel PWM: lamps, backlights, button LEDs and both meters.

Runs open-drain (MODE2 OUTDRV = 0) with INVRT = 1, so a channel sinks
current during its ON count and is high-impedance otherwise. That makes
`set_sink(ch, x)` mean "fraction of the time this channel pulls low": LED
brightness for everything wired as a sink from 5V, and the inverse of the
needle position for the meters, which sit on a 1k pull-up to 5V
(docs/HARDWARE.md, DECISIONS.md #68). Verify on the bench with Settings >
hardware test: if every lamp is inverted, INVRT is the bit to flip.
"""
from __future__ import annotations

import time

MODE1 = 0x00
MODE2 = 0x01
LED0_ON_L = 0x06
PRESCALE = 0xFE

MODE1_SLEEP = 0x10
MODE1_AUTO_INCREMENT = 0x20
MODE2_INVRT = 0x10  # OUTDRV (0x04) deliberately left clear: open-drain

OSCILLATOR_HZ = 25_000_000
STEPS = 4096
FULL = 0x10  # bit 4 of ON_H / OFF_H: full on / full off


def prescale_for(freq_hz: float) -> int:
    return max(3, min(255, round(OSCILLATOR_HZ / (STEPS * freq_hz)) - 1))


def channel_registers(fraction: float) -> list[int]:
    """ON_L, ON_H, OFF_L, OFF_H for a sink fraction 0..1. The ends use the
    full-on/full-off bits so 0 and 1 are exact rather than one count off."""
    fraction = max(0.0, min(1.0, fraction))
    if fraction <= 0.0:
        return [0, 0, 0, FULL]
    if fraction >= 1.0:
        return [0, FULL, 0, 0]
    off = max(1, min(STEPS - 1, round(fraction * STEPS)))
    return [0, 0, off & 0xFF, off >> 8]


class PCA9685:
    def __init__(self, bus, address: int = 0x40, freq_hz: float = 1600) -> None:
        self.bus = bus
        self.address = address
        self._last: dict[int, list[int]] = {}
        # Prescale can only be written while asleep.
        bus.write_byte_data(address, MODE1, MODE1_SLEEP)
        bus.write_byte_data(address, PRESCALE, prescale_for(freq_hz))
        bus.write_byte_data(address, MODE2, MODE2_INVRT)
        bus.write_byte_data(address, MODE1, MODE1_AUTO_INCREMENT)
        time.sleep(0.0005)  # oscillator start-up, datasheet 500us

    def set_sink(self, channel: int, fraction: float) -> None:
        """Skips the bus write when nothing changed: set every frame, written rarely."""
        regs = channel_registers(fraction)
        if self._last.get(channel) == regs:
            return
        self.bus.write_i2c_block_data(self.address, LED0_ON_L + 4 * channel, regs)
        self._last[channel] = regs

    def all_off(self) -> None:
        for channel in range(16):
            self.set_sink(channel, 0.0)
