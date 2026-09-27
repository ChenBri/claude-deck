"""RealPanel: GPIO, SPI, I2C, PCA9685, MCP23017, WS2812-over-SPI.

No hardware has arrived yet (see docs/BUILD.md phase 0), so this is the wiring
this class needs once it does, not a working driver. Every method matches
Panel so main.py never has to know which backend it is holding.
"""
from __future__ import annotations

from deck.panel.base import InputEvent, Panel
from deck.ui.render import compose_output


class RealPanel(Panel):
    def __init__(self) -> None:
        # Deferred imports: these packages only exist on the Radxa ZERO 3W
        # (DECISIONS.md #1, swapped in from a Raspberry Pi Zero 2 W on
        # 2026-09-23 - see docs/HARDWARE.md for the full pin redo).
        #   import board, busio                    # I2C4 bus, pins 27/28
        #   from adafruit_pca9685 import PCA9685    # lamps, button LEDs, meters
        #   from adafruit_mcp230xx.mcp23017 import MCP23017  # rotary, keys, toggles
        #   import spidev                            # halo + underglow, SPI3 MOSI/pin 19,
        #                                             # bit-banged to WS2812 timing - no
        #                                             # rpi_ws281x here, it's Broadcom
        #                                             # PWM/PCM-DMA specific and doesn't
        #                                             # run on this SoC. Needs root or a
        #                                             # udev rule for /dev/spidevX.Y.
        #   import gpiod or RPi-compatible GPIO lib   # APPROVE/DENY/PANIC/encoder, real GPIO
        # Display is HDMI (DECISIONS.md #20, an 11.6in 1366x768 panel +
        # driver board), out the board's own Micro HDMI port - no SPI or
        # GPIO pins spent on it either way.
        raise NotImplementedError(
            "RealPanel needs the Radxa hardware libraries (adafruit-blinka, "
            "adafruit-circuitpython-pca9685, adafruit-circuitpython-mcp230xx, "
            "spidev for the WS2812-over-SPI driver, a GPIO library for the "
            "Rockchip GPIO banks), which are only installable on the board "
            "itself. Run the simulator with --panel sim until parts land."
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
