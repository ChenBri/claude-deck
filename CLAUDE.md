# claude-deck

A hand-built desk instrument that shows Claude Code status on lamps, an animated
pixel screen and two analog needles, and lets you answer permission prompts
without touching the keyboard. Raspberry Pi Zero 2 W in a 3D printed retro
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
firmware/   Python. Runs on the Pi, and on a desktop as a full panel simulator.
daemon/     TypeScript. Cross-platform, Windows and macOS. Ingests Claude Code hooks.
hooks/      Hook scripts and the settings.json snippet.
case/       OpenSCAD source for the enclosure.
panel/      Inkscape SVG for the laser-cut engraved legend strip.
tools/      Hook event recorder and replayer.
```

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
4. **No route to the internet.** USB point-to-point only, WiFi behind a physical
   toggle. Anything needing the network comes from the daemon.
5. **Scrub before it leaves the PC.** The Pi renders to a screen and writes to a
   card, so it must never hold anything worth stealing.

## Hardware constraints that bite

- I2S audio claims GPIO18/19/21, which kills SPI1 and PCM. NeoPixels therefore
  run on GPIO12 (PWM0) via `rpi_ws281x` as root in a systemd service.
- The Pi is 3.3V, WS2812B wants 5V data. The 74AHCT125 is not optional.
- No analog output. The needles are PWM through an RC filter, trimpot calibrated.
- Root filesystem is read-only with a RAM overlay. Writable data lives on a third
  partition at `/var/deck`.

## Working style

- Build against the simulator first. `SimPanel` and `RealPanel` implement the same
  interface, and the screen renderer is shared code. Nothing should be written twice.
- The state machine decides when the approve button is live, so it gets real tests.
- Match the existing style. Few comments unless genuinely needed. Add guards, but
  do not over-engineer.
- No emojis anywhere, including commit messages.
- Prefer small focused commits on `master`.
