# claude-deck: decision log

A hand-built physical status panel for Claude Code. Lights, buttons, an animated
pixel-art screen and an analog needle, driven by Claude Code hooks.

## Locked

| # | Decision | Choice | Notes |
|---|---|---|---|
| 1 | Brain | Raspberry Pi Zero 2 W | Full Linux. 512MB, quad A53. Header is unpopulated, must be soldered. |
| 2 | PC link | USB gadget mode: HID keyboard + USB ethernet, WiFi as fallback | One data cable. HID needs no drivers; RNDIS on Win10 may need a fallback to WiFi. |
| 3 | Power | Separate 5V 3A supply into PWR IN port | Data port stays data-only. No USB current limits, no backfeed. |
| 4 | Indicators | Full panel: discrete labelled LEDs + NeoPixels + display | |
| 5 | Display | 2.4" IPS SPI, 320x240 (ST7789/ILI9341) | Rendered at low logical res, scaled. pygame on fbtft framebuffer. |
| 6 | Screen content | Animated pixel mascot + HUD strip + live tool ticker + idle dashboard | No stats/history screen. |
| 7 | Art pipeline | Generated as code-defined pixel grids to PNG sheets, refinable in Piskel | Original mascot, not Anthropic's asset. |
| 8 | Inputs | Lit arcade approve/deny/panic, rotary encoder, mech keys, mute toggle | |
| 9 | Analog | Moving-needle panel meter, PWM driven | |
| 10 | Audio | MAX98357A I2S DAC + speaker, physical mute | |
| 11 | Enclosure | Online 3D print service, retro terminal / tiny CRT form | |
| 12 | Tools | Buying a full soldering kit | |
| 13 | Budget | No hard ceiling, optimise for cool | |
| 14 | Name | claude-deck | |

## Hardware constraints already resolved

- **Pin budget.** NeoPixels on GPIO12 (PWM0, `rpi_ws281x`, root via systemd).
  Display on SPI0. Audio on I2S (GPIO18/19/21). Discrete LEDs offloaded to a
  PCA9685 over I2C so they cost zero GPIO and get 12-bit PWM for breathing.
  Buttons and encoder take the remainder.
- **Logic levels.** Pi is 3.3V, WS2812B wants 5V data. 74AHCT125 level shifter required.
- **No analog out.** The VU meter is driven by filtered PWM (or an MCP4725 DAC on I2C).

## Open

See the question rounds in the session. Nothing below the line is settled yet:
states and priority, multi-session handling, LED count and legends, exact button
map and keystrokes, meter source, sound design, wiring approach, sourcing, phases.
