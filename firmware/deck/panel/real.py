"""RealPanel: GPIO, SPI, I2C, PCA9685, MCP23017, rpi_ws281x.

No hardware has arrived yet (see docs/BUILD.md phase 0), so this is the wiring
this class needs once it does, not a working driver. Every method matches
Panel so main.py never has to know which backend it is holding.
"""
from __future__ import annotations

from deck.panel.base import InputEvent, Panel
from deck.ui.render import compose_output


class RealPanel(Panel):
    def __init__(self) -> None:
        # Deferred imports: these packages only exist on the Pi.
        #   import board, busio                    # I2C bus
        #   from adafruit_pca9685 import PCA9685    # lamps, button LEDs, meters
        #   from adafruit_mcp230xx.mcp23017 import MCP23017  # rotary, keys, toggles
        #   from rpi_ws281x import PixelStrip       # halo + underglow, GPIO12/PWM0, root
        #   import RPi.GPIO as GPIO                  # APPROVE/DENY/PANIC/encoder, real GPIO
        # No spidev: the display is HDMI now (DECISIONS.md #20, an 11.6in
        # 1366x768 panel + driver board), not the small SPI TFT this was
        # first written against. GPIO8-11 (SPI0), 22/23 (DC/RST) and 17
        # (backlight enable) are free as a result - see docs/HARDWARE.md.
        raise NotImplementedError(
            "RealPanel needs the Pi hardware libraries (adafruit-blinka, "
            "adafruit-circuitpython-pca9685, adafruit-circuitpython-mcp230xx, "
            "rpi_ws281x, RPi.GPIO), which are only installable on the "
            "Pi itself. Run the simulator with --panel sim until parts land."
        )

    def set_lamp(self, name: str, level: float) -> None:
        raise NotImplementedError

    def set_meter(self, name: str, level: float) -> None:
        raise NotImplementedError

    def set_pixels(self, colors) -> None:
        raise NotImplementedError

    def set_button_led(self, name: str, level: float) -> None:
        raise NotImplementedError

    def present(self, canvas) -> None:
        # Real display path: compose_output(canvas) -> present via pygame's
        # KMSDRM/fbcon SDL video driver onto the HDMI framebuffer. No manual
        # per-row transfer to a controller chip needed, unlike the old SPI
        # TFT plan - HDMI just wants a normal pygame display surface.
        compose_output(canvas)
        raise NotImplementedError

    def poll_inputs(self) -> list[InputEvent]:
        raise NotImplementedError

    def close(self) -> None:
        pass
