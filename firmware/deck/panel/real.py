"""RealPanel: the physical deck. PCA9685 for lamps, LEDs and meters,
two MCP23017s and an ADS1115 for the panel controls, WS2812B over SPI for
the halo and underglow, real GPIO for the buttons, mushroom and encoder,
and the HDMI panel through pygame. Every method matches Panel, so main.py
never has to know which backend it is holding.

The chip drivers and the input logic live in deck/panel/hw/ and are
tested against fakes; this class only wires them to the pin and channel
assignments in docs/HARDWARE.md. Bus numbers and device paths marked
"verify" are the ones to confirm on first boot.
"""
from __future__ import annotations

import pygame

from deck.panel.base import BUTTON_LEDS, LAMPS, METERS, PIXEL_COUNT, Panel, InputEvent
from deck.panel.hw.ads1115 import ADS1115
from deck.panel.hw.gpio import EdgeDecoder, GpioInputs
from deck.panel.hw.inputs import AnalogInputs, ExpanderInputs
from deck.panel.hw.mcp23017 import MCP23017
from deck.panel.hw.pca9685 import PCA9685
from deck.panel.hw.ws2812 import WS2812
from deck.ui.render import OUTPUT_HEIGHT, OUTPUT_WIDTH, compose_output

I2C_BUS = 4  # I2C4 on pins 27/28; verify /dev/i2c-4 on first boot
SPI_BUS, SPI_DEVICE = 3, 0  # SPI3 MOSI on pin 19; verify /dev/spidev3.0
FPS = 30

LAMP_CHANNELS = {"READY": 0, "WORKING": 1, "BLOCKED": 2, "DONE": 3, "LINK": 4}
LEGEND_CHANNELS = (5, 6)
BUTTON_LED_CHANNELS = {"APPROVE": 7, "DENY": 8}
METER_CHANNELS = {"CONTEXT": 9, "FIVE_HOUR": 10}
METER_BACKLIGHT_CHANNEL = 11

JOY_X, JOY_Y, VOLUME = 0, 1, 2  # ADS1115 inputs


class RealPanel(Panel):
    def __init__(self, settings: dict | None = None, bus=None, spi=None, gpio=None, display: bool = True) -> None:
        """bus/spi/gpio default to the real devices; tests pass fakes and display=False."""
        settings = settings or {}
        if bus is None:
            from smbus2 import SMBus

            bus = SMBus(I2C_BUS)
        if spi is None:
            import spidev

            spi = spidev.SpiDev()
            spi.open(SPI_BUS, SPI_DEVICE)

        self._pwm = PCA9685(bus, 0x40)
        self._mcp1 = MCP23017(bus, 0x20)
        self._mcp2 = MCP23017(bus, 0x21)
        self._adc = ADS1115(bus, 0x48, channels=(JOY_X, JOY_Y, VOLUME))
        self._strip = WS2812(spi)
        self._gpio = gpio if gpio is not None else GpioInputs(EdgeDecoder(bool(settings.get("encoder_invert", False))))
        self._expanders = ExpanderInputs()
        self._analog = AnalogInputs(settings.get("joystick"))

        self._lamps = {name: 0.0 for name in LAMPS}
        self._leds = {name: 0.0 for name in BUTTON_LEDS}
        self._meters = {name: 0.0 for name in METERS}
        self._pixels = [(0, 0, 0)] * PIXEL_COUNT
        self._backlight = 1.0

        self._screen = None
        self._clock = pygame.time.Clock()
        if display:
            # SDL_VIDEODRIVER=kmsdrm comes from deck.service; straight onto the HDMI framebuffer.
            pygame.display.init()
            pygame.font.init()
            self._screen = pygame.display.set_mode((OUTPUT_WIDTH, OUTPUT_HEIGHT), pygame.FULLSCREEN)
            pygame.mouse.set_visible(False)

    # -- outputs ---------------------------------------------------------------

    def set_lamp(self, name: str, level: float) -> None:
        self._lamps[name] = level

    def set_meter(self, name: str, level: float) -> None:
        self._meters[name] = level

    def set_pixels(self, colors) -> None:
        self._pixels = list(colors)

    def set_button_led(self, name: str, level: float) -> None:
        self._leds[name] = level

    def set_backlight(self, level: float) -> None:
        self._backlight = level

    def _flush_outputs(self) -> None:
        for name, channel in LAMP_CHANNELS.items():
            self._pwm.set_sink(channel, self._lamps[name])
        for name, channel in BUTTON_LED_CHANNELS.items():
            self._pwm.set_sink(channel, self._leds[name])
        for channel in (*LEGEND_CHANNELS, METER_BACKLIGHT_CHANNEL):
            self._pwm.set_sink(channel, self._backlight)
        # Open-drain with a pull-up: sinking pulls the needle down (DECISIONS.md #68).
        for name, channel in METER_CHANNELS.items():
            self._pwm.set_sink(channel, 1.0 - max(0.0, min(1.0, self._meters[name])))
        self._strip.show(self._pixels)

    def present(self, canvas, rails=None, screen_level: float = 1.0) -> None:
        self._flush_outputs()
        if self._screen is not None:
            self._screen.blit(compose_output(canvas, rails, screen_level), (0, 0))
            pygame.display.flip()
        self._clock.tick(FPS)

    # -- inputs ----------------------------------------------------------------

    def poll_inputs(self) -> list[InputEvent]:
        if self._screen is not None:
            pygame.event.pump()  # keeps SDL's display alive; there's no keyboard to read
        events = self._gpio.drain()
        events += self._expanders.update(self._mcp1.pressed(), self._mcp2.pressed())
        values = self._adc.poll()
        events += self._analog.update(values[JOY_X], values[JOY_Y], values[VOLUME])
        return events

    def close(self) -> None:
        self._pwm.all_off()
        # an "off" meter channel lets the pull-up peg the needle, so park them at zero
        for channel in METER_CHANNELS.values():
            self._pwm.set_sink(channel, 1.0)
        self._strip.show([(0, 0, 0)] * PIXEL_COUNT)
        self._gpio.close()
        if self._screen is not None:
            pygame.display.quit()
