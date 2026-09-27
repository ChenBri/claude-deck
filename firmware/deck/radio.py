"""WiFi on or off, from Settings > wifi radio. Real deck only.

WiFi is blocked at every boot (deploy/systemd/deck-radio-off.service), so
the deck has no route out unless you switch it on here, and the setting is
re-applied once at start-up so a saved "on" survives a reboot. The rails
show a WIFI tag while it's on. Bluetooth stays blocked, there's no toggle
for it.

The two rfkill commands are the only ones deploy/setup.sh's sudoers entry
allows the deck user besides poweroff, with these exact arguments.
"""
from __future__ import annotations

import subprocess

RFKILL = "/usr/sbin/rfkill"


class Radio:
    def __init__(self, run=subprocess.run) -> None:
        """`run` is replaceable for tests."""
        self._run = run

    def set_wifi(self, on: bool) -> bool:
        """Returns False if rfkill refused or isn't there; the setting then
        just doesn't take, and the deck stays as it was."""
        try:
            result = self._run(
                ["sudo", "-n", RFKILL, "unblock" if on else "block", "wifi"],
                check=False,
                capture_output=True,
                timeout=5,
            )
        except (OSError, subprocess.TimeoutExpired):
            return False
        return result.returncode == 0
