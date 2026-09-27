"""Stand-ins for smbus2.SMBus and spidev.SpiDev, recording every write."""
from __future__ import annotations


class FakeI2C:
    def __init__(self) -> None:
        self.regs: dict[int, dict[int, int]] = {}
        self.writes: list[tuple[int, int, list[int]]] = []

    def _dev(self, addr: int) -> dict[int, int]:
        return self.regs.setdefault(addr, {})

    def write_byte_data(self, addr: int, reg: int, value: int) -> None:
        self._dev(addr)[reg] = value
        self.writes.append((addr, reg, [value]))

    def write_i2c_block_data(self, addr: int, reg: int, data: list[int]) -> None:
        for i, v in enumerate(data):
            self._dev(addr)[reg + i] = v
        self.writes.append((addr, reg, list(data)))

    def read_i2c_block_data(self, addr: int, reg: int, length: int) -> list[int]:
        dev = self._dev(addr)
        return [dev.get(reg + i, 0) for i in range(length)]


class FakeSPI:
    def __init__(self) -> None:
        self.max_speed_hz = 0
        self.mode = None
        self.frames: list[bytes] = []

    def writebytes2(self, data) -> None:
        self.frames.append(bytes(data))


class FakeGpio:
    def __init__(self) -> None:
        self.pending = []
        self.closed = False

    def drain(self):
        out, self.pending = self.pending, []
        return out

    def close(self) -> None:
        self.closed = True
