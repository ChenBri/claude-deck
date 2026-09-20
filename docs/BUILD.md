# Build plan

One AliExpress order, placed once. Software gets built while it ships.

---

## Phase 0, now. No hardware.

1. Install the hook scripts and start **recording real events** from normal
   Claude Code use. Every day of recording tunes the state machine better.
2. Build the **simulator**: the full panel in a pygame window on the desktop.
3. Build the **state machine** and its tests.
4. Build the **daemon**: hook ingest, scrub, classify, denylist, actions for
   Windows and macOS.
5. First sprite set and the core scenes.

By the end of phase 0 the whole deck runs on the monitor, reacting live to real
sessions.

## Phase 1, order day one

The complete order from [BOM.md](BOM.md), all of it, sections A through J.
Different sellers ship separately, which arrives staggered over 2 to 5 weeks and
keeps most parcels under the import threshold.

The case print, the legend strip and the steel ballast plate (section L) are
ordered **after** the electronics arrive, cut from our files against measured
parts rather than guessed dimensions.

## Phase 2, first parts land

1. Solder the 40-pin header. First soldering, forgiving part, 40 chances to get
   better at it. Slowly.
2. Flash the OS, set up USB gadget mode, confirm the link from both machines.
3. Blink one LED.
4. Get the display running and put the simulator's renderer on it unchanged.
5. Overlay filesystem and the third partition.

## Phase 3, everything landed

Breadboard every subsystem **on its own** before combining anything:

| Test | Confirms |
|---|---|
| NeoPixels through the level shifter | Timing and logic levels |
| PCA9685 lamps | I2C address, breathing, dimming |
| One meter through its RC filter | Needle sweep, trimpot calibration |
| MCP23017 inputs | Rotary switch decoding, key and toggle reads |
| Encoder on real GPIO | No missed detents under load |
| I2S audio | Amp wiring, no whine, mute path |
| Three buttons on real GPIO | Debounce, panic latency |

Then wire it together, then the perfboard build. A JST connector on every
subassembly, so the panel comes out of the case without desoldering.

## Phase 4, the case

1. Model the enclosure in OpenSCAD from measured parts.
2. Print a **test panel only**, not the whole box, and check every cutout.
3. Print the full set in PETG, matte black.
4. Press in the heat-set inserts with the soldering iron.
5. Cut and fit the steel ballast plate, stick on the feet.
6. Laser-cut the engraved legend strip.
7. Final assembly.

## Phase 5, PCB revision

Custom HAT in KiCad, five boards from JLCPCB. The second build is the one that
lives in the case permanently.

---

## Timeline

| Week | What |
|---|---|
| 1 | Phase 0 software. Order placed. |
| 2-5 | Parts arrive staggered. Software polish, sprite set, case modelled. |
| 5 | Subsystem bring-up on breadboard. |
| 6 | Perfboard build. Case and legend strip ordered from measured parts. |
| 7 | Print and strip arrive. Assembly. |
| 8 | On the desk. |

Roughly two months, most of it waiting rather than working.

## Skills picked up, in order

Through-hole soldering. Reading a datasheet for pinout and current limits.
I2C addressing and bus sharing. Debouncing. Level shifting. RC filtering as a
poor man's DAC. Power budgeting. Parametric CAD. Design for 3D printing:
tolerances, clearances, heat-set inserts. Panel layout ergonomics.
