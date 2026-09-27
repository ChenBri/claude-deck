"""MCP23017 16-bit I/O expander, used as 16 inputs with pull-ups. Every
switch on the panel is wired active low, so `pressed()` reports a bit as
True when its pin reads 0. Register addresses are for IOCON.BANK = 0, the
power-on default, where A and B registers alternate so one two-byte read
gets both ports."""
from __future__ import annotations

IODIRA = 0x00
GPPUA = 0x0C
GPIOA = 0x12


class MCP23017:
    def __init__(self, bus, address: int) -> None:
        self.bus = bus
        self.address = address
        bus.write_i2c_block_data(address, IODIRA, [0xFF, 0xFF])  # all inputs
        bus.write_i2c_block_data(address, GPPUA, [0xFF, 0xFF])  # all pull-ups

    def read(self) -> int:
        """Raw pin levels, port A in bits 0-7 and port B in bits 8-15."""
        a, b = self.bus.read_i2c_block_data(self.address, GPIOA, 2)
        return a | (b << 8)

    def pressed(self) -> int:
        """Active-low: a set bit means that switch is closed."""
        return ~self.read() & 0xFFFF


def bit(port: str, pin: int) -> int:
    """Bit index in read()/pressed() for a port letter and pin, e.g. ("B", 3) -> 11."""
    return pin + (8 if port == "B" else 0)
