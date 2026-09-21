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
        #   import spidev                            # display, SPI0
        #   import RPi.GPIO as GPIO                  # APPROVE/DENY/PANIC/encoder, real GPIO
        raise NotImplementedError(
            "RealPanel needs the Pi hardware libraries (adafruit-blinka, "
            "adafruit-circuitpython-pca9685, adafruit-circuitpython-mcp230xx, "
            "rpi_ws281x, spidev, RPi.GPIO), which are only installable on the "
            "Pi itself. Run the simulator with --panel sim until parts land."
        )

    def set_lamp(self, name: str, level: float) -> None:
        raise NotImplementedError

    def set_meter(self, name: str, level: float) -> None:
        raise NotImplementedError

    def set_pixels(self, colors) -> None:
        raise NotImplementedError

    def set_button_led(self, name: str, on: bool) -> None:
        raise NotImplementedError

    def present(self, canvas) -> None:
        # Real display path: compose_output(canvas) -> blit RGB565 rows over
        # SPI0 to the ST7789/ILI9341 controller via spidev, DC/RST on GPIO22/23.
        compose_output(canvas)
        raise NotImplementedError

    def poll_inputs(self) -> list[InputEvent]:
        raise NotImplementedError

    def close(self) -> None:
        pass
