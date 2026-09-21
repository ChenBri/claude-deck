# claude-deck: decision log

A hand-built physical status panel for Claude Code. Lights, buttons, an animated
pixel-art screen and two analog needles, driven by Claude Code hooks.

## System

| # | Decision | Choice | Notes |
|---|---|---|---|
| 1 | Brain | Raspberry Pi Zero 2 W | Full Linux. Header unpopulated, must be soldered. |
| 2 | PC link | USB gadget: HID keyboard + USB ethernet | Composite device. ECM for macOS, RNDIS for Windows. |
| 3 | Network | USB point-to-point only, WiFi behind a panel toggle | 10.55.0.1 to 10.55.0.2. Not on the LAN, not routable. |
| 4 | Power | Separate 5V 3A supply into PWR IN | Data port stays data-only. No backfeed, no current limits. |
| 5 | Filesystem | Read-only root with RAM overlay | Power loss can never corrupt the OS. |
| 6 | History | Third writable partition, /var/deck | Settings and stats. Written only on state transitions. |
| 7 | Shutdown | Long-press the encoder, plus a lit rocker on the back | Clean shutdown with a goodbye animation. |
| 8 | Stack | Python on the Pi, TypeScript daemon on Windows and macOS | One daemon codebase, platform-specific action implementations. |
| 9 | Config | Encoder menu as the interface, YAML underneath | Regexes cannot be typed on a knob, so the menu writes the file. |

## Safety

| # | Decision | Choice |
|---|---|---|
| 10 | Button path | Daemon-verified. HID emits only F13-F20, never a printable key. |
| 11 | Approve semantics | "Approve request X", matched against what is on screen, 90s expiry. |
| 12 | Denylist | All four categories: database, destructive fs and git, infrastructure, secrets. |
| 13 | Machines | Full action set on Windows and on the Mac alike. The denylist, not a profile, is what protects production access. |
| 14 | Scrubbing | Truncate and redact before anything leaves the PC. |
| 15 | Audit | SQLite log on the PC of every deck-originated action. |

Full reasoning in [docs/SAFETY.md](docs/SAFETY.md).

## Panel

| # | Decision | Choice |
|---|---|---|
| 16 | Lamps | 5: READY, WORKING, BLOCKED, DONE, LINK |
| 17 | Legends | Backlit engraved acrylic strip, laser cut |
| 18 | Ambient | WS2812B strip for both the bezel halo and the underglow. Amended while sourcing: a circular ring does not fit a rectangular bezel, and 1m of 60/m strip covers the ~300mm halo perimeter and the ~300mm underglow with spare. |
| 19 | Meters | Two analog needles: CONTEXT and ACTIVITY |
| 20 | Display | 2.4 inch IPS SPI, 320x240, in a recessed CRT bezel |
| 21 | Session selector | 6-position rotary switch, 1-5 plus ALL |
| 22 | Encoder | Menu, scrolling, long-press shutdown. Snake steering moved to the joystick. |
| 23 | APPROVE / DENY | 19mm illuminated metal pushbuttons, 3-6V ring LED, momentary self-reset, pre-wired. Live only when a prompt is pending. Amended while sourcing: illuminated arcade buttons were either unavailable outside bundle listings or 45mm, too large for the deck. |
| 24 | Panic | 22mm XB2-542 mushroom e-stop, 1NO1NC, **latching**. Amended while sourcing: spring-return mushrooms are not sold on AliExpress. Firmware fires on the press edge and holds an INTERRUPTED state until the twist-release, so the latched head visibly shows a killed run. Flip cover dropped as redundant. |
| 25 | Mech keys | 4: CLD (focus or launch), NEW, PLAN, MIC (push to talk) |
| 26 | Toggles | MUTE, NIGHT, AUTO-ACCEPT |
| 27 | Back panel | Panel-mount USB-C, barrel jack, lit rocker, SD cutout |

## Screen

| # | Decision | Choice |
|---|---|---|
| 28 | Style | Warm CRT phosphor UI, full-colour mascot, scanlines and slight bloom |
| 29 | Art pipeline | Code-defined pixel grids rendered to PNG, refinable in Piskel |
| 30 | Mascot | Original starburst character, not Anthropic artwork |
| 31 | HUD | Session name, elapsed time, context bar |
| 32 | Ticker | Live tool name and target, sanitized |
| 33 | Idle dashboard | Clock, date, your name, weather from the daemon, git status of the last repo, today's totals |
| 34 | Games | Snake and Tetris as first-class scenes, launched from the encoder menu when idle. Joystick steers, mech keys rotate and drop, encoder push pauses. |
| 35 | DONE behaviour | Auto-clears back to READY after a few minutes |

## Sound

| # | Decision | Choice |
|---|---|---|
| 36 | Style | Chiptune blips generated in code, one per event |
| 37 | Events | Blocked, finished, error, task start and subagent spawn |
| 38 | Output | MAX98357A I2S amp, 40mm speaker, hard MUTE toggle |

## Enclosure

| # | Decision | Choice |
|---|---|---|
| 39 | Form | Retro terminal. Vertical face with a recessed CRT bezel, sloped control deck. |
| 40 | Size | 160 x 120 x 100 mm. Upper face 95mm, deck 55mm deep. |
| 41 | Colour | Matte black with orange accents |
| 42 | Process | FDM PETG via a print service. MJF nylon reprint later if wanted. |
| 43 | CAD | OpenSCAD, case as parametric code in this repo |
| 44 | Ballast | 3mm steel plate in the base plus rubber feet, about 1kg total |
| 45 | Fasteners | M3 brass heat-set inserts |

## Build

| # | Decision | Choice |
|---|---|---|
| 46 | Wiring | Perfboard first, custom PCB HAT as a later revision |
| 47 | Tools | Full soldering kit purchased new |
| 48 | Sourcing | AliExpress only, one order, everything at once. Case, legend strip, ballast plate and isopropyl fabricated or bought locally because they cannot be catalogue items. |
| 49 | Sequencing | Software and simulator now, single order in parallel, one build when it all lands. No early partial build. |
| 50 | Budget | No hard ceiling. Landed at roughly $416 all-in including every tool. |
| 51 | MIC key | Daemon receives the hotkey and invokes the OS dictation shortcut: Win+H on Windows, the configured dictation shortcut on macOS. |
| 52 | Fabrication | Local Tel Aviv print shop for the PETG case and the laser-cut legend strip, ordered after the electronics arrive so every cutout is measured. |
| 53 | Joystick | KY-023 analog thumbstick read through an ADS1115 I2C ADC, push button on the second MCP23017. Added 2026-09-21 for games and menu navigation. The deck gains a ~26mm square cutout; case width may grow to 170mm. |
| 54 | Game Boy app | PyBoy (GB/GBC) headless core, added 2026-09-21. Fourth home-screen app alongside Settings/Snake/Tetris. Draws into its own 160x144 canvas (native GB resolution), letterboxed onto the panel instead of the 160x120 canvas every other scene shares. |
| 55 | Game Boy buttons | A, B, START, SELECT: four small tactile buttons wired to the second MCP23017's remaining spares, no new IC. The d-pad reuses the existing joystick rather than adding a fifth control. |
| 56 | ROM handling | Never shipped in this public repo: each person drops their own legally-dumped .gb/.gbc files into firmware/roms/, which is gitignored except for its own README. Planned, not yet built: a fifth USB gadget function (mass storage, backed by a FAT image file on the writable partition, toggled from the Settings app) so ROMs can be dragged onto the deck as a drive from the connected PC instead of swapping the SD card. No hardware exists yet to build this against; see docs/HARDWARE.md. |
| 57 | Game Boy audio | No new hardware: PyBoy's emulated audio is queued onto the existing `chiptune` mixer (now stereo) through a channel it reserves so a running game's stream and the deck's own event blips never steal each other's channel. Same MAX98357A amp and speaker, same MUTE toggle. |

## Hardware constraints resolved

- **Pin budget.** I2S audio claims GPIO18/19/21, which kills SPI1 and PCM.
  NeoPixels therefore run on GPIO12 (PWM0) via `rpi_ws281x` as root in a systemd
  service. Display on SPI0. Lamps and both meters offloaded to a PCA9685 on I2C.
  Rotary switch, mech keys and toggles offloaded to an MCP23017. Buttons and the
  encoder stay on real GPIO for latency.
- **Logic levels.** 74AHCT125 between the Pi and the WS2812B data line.
- **No analog output.** Meters driven by PCA9685 PWM through an RC filter with a
  calibration trimpot each.
- **Power.** 2.08A peak, so a 5V 3A supply.

Details in [docs/HARDWARE.md](docs/HARDWARE.md).
