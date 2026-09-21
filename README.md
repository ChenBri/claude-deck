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
cd firmware
python -m deck.main --panel sim
```

Replay a recorded session into it at speed:

```bash
python firmware/tools/replay.py sessions/2026-09-20.jsonl --speed 10
```

## Running the full stack locally (no hardware needed)

The simulator above and `tools/record.py` / `tools/replay.py` already cover
phase 0's workflow with no daemon involved (`python -m deck.main --panel sim
--no-link` runs the panel standalone). The one piece those don't exercise is
the daemon itself: hook ingest, scrub, classify, the denylist, and the
approve/deny round-trip. Here's how to run that too, still on one PC with
nothing ordered yet.

The daemon and firmware normally talk over the USB gadget's fixed addresses
(10.55.0.1 the Pi, 10.55.0.2 the host, see docs/HARDWARE.md); point both at
loopback instead so they don't try to bind an address that doesn't exist yet:

```powershell
# terminal 1: the daemon
cd daemon
npm install
npm run build
$env:DECK_PI_HOST = "127.0.0.1"; $env:DECK_PI_PORT = "17328"
$env:DECK_DAEMON_LISTEN_HOST = "127.0.0.1"; $env:DECK_DAEMON_LISTEN_PORT = "17329"
npm start
```

```powershell
# terminal 2: the simulator
cd firmware
pip install -r requirements.txt
$env:DECK_PI_LISTEN_HOST = "127.0.0.1"; $env:DECK_PI_LISTEN_PORT = "17328"
$env:DECK_DAEMON_HOST = "127.0.0.1"; $env:DECK_DAEMON_PORT = "17329"
python -m deck.main --panel sim
```

Then merge [hooks/settings.snippet.json](hooks/settings.snippet.json) into
your `~/.claude/settings.json` (see [hooks/README.md](hooks/README.md)),
pointing each command at this repo's `hooks/emit.js`. Use Claude Code
normally in a third window: every hook now flows hook -> daemon (scrub,
classify, denylist) -> simulator, live, and pressing APPROVE/DENY in the
simulator round-trips back to the daemon and performs the real action on
your machine. Same code path production will use, just addressed at
127.0.0.1 instead of the real link IPs.

### Env vars, and keeping secrets out of the repo

None of the four address/port variables above are secret - they only
exist so two local processes don't collide with the real hardware's fixed
IPs. Nothing in this repo needs an API key. Two optional daemon-side vars
touch something personal rather than secret, and both default to off:

- `DECK_LAT` / `DECK_LON` - idle-dashboard weather (open-meteo, no key).
  Unset means no call is made and the dashboard just omits it.
- `DECK_USER_NAME` - idle-dashboard display name.

There's also `DECK_TERMINAL_TITLE_HINT` / `DECK_TERMINAL_APP_HINT` /
`DECK_DICTATION_SHORTCUT` for tuning the Windows/macOS action backends to
your actual terminal - see `daemon/src/actions/windows.ts` and `macos.ts`.

Set any of these in your shell (or a local launch script), not in a
committed file. `.gitignore` already excludes `.env`, `.env.*`, and
`*.local.env`, `firmware/var/` (the settings the encoder menu writes),
`firmware/sessions/` and `sessions/` (recorded hook corpora), and
`daemon/audit.sqlite` - none of that should ever land in git regardless.
