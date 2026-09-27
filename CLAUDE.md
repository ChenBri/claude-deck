# claude-deck

A hand-built desk instrument that shows Claude Code status on lamps, an animated
pixel screen and two analog needles, and lets you answer permission prompts
without touching the keyboard. Radxa ZERO 3W in a 3D printed retro
terminal shell.

**This repo is public.** Never commit anything employer-specific, any real
infrastructure identifier, any personal detail beyond what is already here, or
anything describing a real security posture. Keep examples generic.

## Read these before changing anything

- [DECISIONS.md](DECISIONS.md) is the source of truth. Fifty-odd locked decisions
  with reasoning. If a change contradicts one, say so explicitly rather than
  quietly diverging.
- [docs/HARDWARE.md](docs/HARDWARE.md) pinout, power budget, the constraints that
  forced the layout.
- [docs/SAFETY.md](docs/SAFETY.md) why the approve button is defensible. Treat
  its rules as load-bearing, not advisory.
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) software design.
- [docs/BOM.md](docs/BOM.md) parts, real prices, sourcing.

## Layout

```
firmware/   Python. Runs on the deck, and on a desktop as a full panel simulator.
daemon/     TypeScript. Cross-platform, Windows and macOS. Ingests Claude Code hooks.
hooks/      Hook scripts and the settings.json snippet.
case/       OpenSCAD source for the enclosure.
panel/      Inkscape SVG for the laser-cut engraved legend strip.
deploy/     Provisioning the deck: USB gadget, services, read-only root.
```

The hook event recorder and replayer live in `firmware/tools/`.

## Non-negotiables

These came out of a long design conversation and should not be relaxed without
asking:

1. **HID emits only F13 to F20.** Never a printable character, never Enter,
   never `y`. The daemon registers them as global hotkeys. This is what makes the
   box incapable of typing something destructive into the wrong window.
2. **Approve means "approve request X"**, verified against what is on screen,
   with a 90 second expiry. Never a blind keystroke.
3. **The denylist is load-bearing.** Database, destructive fs and git,
   infrastructure, secrets. Dangerous calls are un-approvable from the box on
   every machine.
4. **No route to the internet.** USB point-to-point only. WiFi is blocked at
   every boot and only comes on through Settings > wifi radio, with a red WIFI
   tag on the rail for as long as it's on. Anything needing the network comes
   from the daemon.
5. **Scrub before it leaves the PC.** The deck renders to a screen and writes to a
   card, so it must never hold anything worth stealing.

## Hardware constraints that bite

- It's a Rockchip RK3566, not a Pi: nothing Broadcom-specific runs (no
  `rpi_ws281x`). NeoPixels go out SPI3 MOSI (pin 19) encoded to WS2812 timing,
  capped at 40% brightness in the driver because that's the power budget.
- 3.3V logic everywhere. WS2812B wants 5V data, so the 74AHCT125 is not
  optional. The PCA9685's logic is 3.3V too, so it runs open-drain: LEDs sink
  from 5V, each meter has a 1k pull-up to 5V, and meter duty is inverted in
  software (DECISIONS.md #68).
- The main I2C bus is I2C4 on pins 27/28, for their built-in pull-ups. Pins 3
  and 5 carry the same extra pull-ups and misbehave as plain GPIO; leave them.
- 12V in for the display, a buck converter to 5V, and 5V into the GPIO header
  (pins 2/4). USB-C 1 is data only to the PC. Never power the board through it.
- No analog output. The needles are PWM through an RC filter, trimpot plus the
  calibration wizard.
- Root filesystem is read-only with a RAM overlay. The app, its venv and all
  writable data live on the DECKDATA partition at `/var/deck`. The firmware
  runs as the unprivileged `deck` user, not root (deploy/).
- Every press goes out twice, as its F13-F20 HID key and as an HTTP action,
  and the daemon only acts when the two pair up (DECISIONS.md #69). The
  simulator has no HID, so its daemon needs `DECK_REQUIRE_HID=0`.

## Working style

- Build against the simulator first. `SimPanel` and `RealPanel` implement the same
  interface, and the screen renderer is shared code. Nothing should be written twice.
- The state machine decides when the approve button is live, so it gets real tests.
- Match the existing style. Few comments unless genuinely needed. Add guards, but
  do not over-engineer.
- No emojis anywhere, including commit messages.
- Prefer small focused commits on `master`.
