"""WS2812B over SPI3 MOSI (pin 19, docs/HARDWARE.md): the SPI peripheral is
used only for its timing. At 2.4MHz one SPI bit is ~417ns, so each LED bit
becomes three SPI bits, 110 for a 1 (~833ns high) and 100 for a 0 (~417ns
high), inside the WS2812B's tolerances. Colour order on the wire is G, R, B.

Brightness is capped here, not by callers, because the cap is a power
budget limit (docs/HARDWARE.md: 30 pixels at 40%), not a style choice.
"""
from __future__ import annotations

SPI_HZ = 2_400_000
BRIGHTNESS_CAP = 0.4
# >280us low latches the frame on newer WS2812B parts; 90 bytes at 2.4MHz is 300us.
RESET_BYTES = 90

_ONE, _ZERO = 0b110, 0b100


def _encode_byte(value: int) -> bytes:
    bits = 0
    for i in range(7, -1, -1):
        bits = (bits << 3) | (_ONE if value >> i & 1 else _ZERO)
    return bits.to_bytes(3, "big")


_TABLE = [_encode_byte(v) for v in range(256)]


def encode(colors, cap: float = BRIGHTNESS_CAP) -> bytes:
    out = bytearray()
    for r, g, b in colors:
        for channel in (g, r, b):
            out += _TABLE[max(0, min(255, round(channel * cap)))]
    out += bytes(RESET_BYTES)
    return bytes(out)


class WS2812:
    def __init__(self, spi) -> None:
        """`spi` is an open spidev.SpiDev (or a fake with writebytes2)."""
        self.spi = spi
        self.spi.max_speed_hz = SPI_HZ
        self.spi.mode = 0
        self._last: bytes | None = None

    def show(self, colors) -> None:
        data = encode(colors)
        if data == self._last:
            return
        self.spi.writebytes2(data)
        self._last = data
