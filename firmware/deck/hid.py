"""USB HID keyboard gadget writer: the only way the deck ever "types".

docs/SAFETY.md rule 1: it can emit F13 to F20 and nothing else. That's
enforced three times over: the gadget's report descriptor only declares
those usages (deploy/usb-gadget.sh), the name -> key map below only holds
function keys, and tap() refuses any keycode outside 0x68-0x6F before a
byte is written.

The key a press sends must match daemon/src/link/hotkeys.ts HOTKEY_MAP;
the daemon pairs each key with the HTTP action carrying the request id
before acting on it.
"""
from __future__ import annotations

import os

F13, F20 = 0x68, 0x6F  # HID usage IDs, keyboard page

HOTKEYS = {
    "APPROVE": 0x68,  # F13
    "DENY": 0x69,  # F14
    "PANIC": 0x6A,  # F15
    "CLD": 0x6B,  # F16
    "NEW": 0x6C,  # F17
    "PLAN": 0x6D,  # F18
    "MIC": 0x6E,  # F19
}

HIDG_PATH = "/dev/hidg0"


class HidKeyboard:
    def __init__(self, path: str = HIDG_PATH, writer=None) -> None:
        """`writer(bytes)` replaces the device in tests."""
        self.path = path
        self._writer = writer
        self._fd: int | None = None

    def tap(self, name: str) -> bool:
        """Press and release the key for `name`. Returns False if the host
        isn't reading (unplugged, gadget unbound): a dropped key is safe,
        the daemon just never sees it and never acts."""
        code = HOTKEYS[name]
        if not F13 <= code <= F20:
            raise ValueError(f"refusing HID keycode {code:#x}: only F13-F20 may ever be sent")
        return self._write(bytes([0, 0, code, 0, 0, 0, 0, 0])) and self._write(bytes(8))

    def _write(self, report: bytes) -> bool:
        if self._writer is not None:
            self._writer(report)
            return True
        try:
            if self._fd is None:
                # Non-blocking: a host that isn't polling must never stall the frame loop.
                self._fd = os.open(self.path, os.O_WRONLY | os.O_NONBLOCK)
            os.write(self._fd, report)
            return True
        except OSError:
            if self._fd is not None:
                os.close(self._fd)
                self._fd = None
            return False
