# claude-deck

A hand-built desk instrument that shows what Claude Code is doing, and lets you
answer it without touching the keyboard.

Raspberry Pi Zero 2 W behind a 3D printed retro terminal shell. Five labelled
lamps behind a backlit engraved legend strip, a 2.4" pixel-art screen with an
animated mascot, two analog needles, a NeoPixel halo and underglow, lit arcade
buttons, a mushroom interrupt under a flip cover, two knobs, four mech keys and
three toggles.

It is driven by Claude Code hooks. It never touches the internet.

```
Claude Code  --hooks-->  daemon (your PC)  --USB link-->  claude-deck (Pi Zero 2 W)
                              ^                                  |
                              +--------- button events ----------+
```

## Status

Design complete. Software phase in progress, hardware not yet ordered.

- [DECISIONS.md](DECISIONS.md) every choice made and why
- [docs/BOM.md](docs/BOM.md) parts, prices, suppliers
- [docs/HARDWARE.md](docs/HARDWARE.md) pinout, power budget, wiring
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) software design
- [docs/SAFETY.md](docs/SAFETY.md) why the approve button is not a footgun
- [docs/BUILD.md](docs/BUILD.md) phased build plan

## Repo layout

```
firmware/   Python. Runs on the Pi. Also runs on your desktop as a simulator.
daemon/     TypeScript. Runs on Windows and macOS. Talks to Claude Code hooks.
hooks/      Hook scripts and the settings.json snippet.
case/       OpenSCAD source for the enclosure.
panel/      Inkscape SVG for the laser-cut engraved legend strip.
tools/      Hook event recorder and replayer.
docs/       Everything above.
```

## The simulator

The entire panel runs on your desktop with no hardware. `SimPanel` draws the
lamps, needles, halo, buttons and screen in a pygame window, and the screen
renders with the exact same code the real display uses.

```bash
python -m deck.main --panel sim
```

Replay a recorded session into it at speed:

```bash
python tools/replay.py sessions/2026-09-20.jsonl --speed 10
```
