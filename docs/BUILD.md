# Build plan

Software starts now. Parts ship in parallel. Nothing blocks on the slow boat.

---

## Phase 0, this week. No hardware needed.

Cost: nothing. Duration: a few evenings.

1. Install the hook scripts and start **recording real events** from your normal
   Claude Code use. Every day of recording makes the state machine better tuned.
2. Build the **simulator**: full panel in a pygame window on your desktop.
3. Build the **state machine** and its tests.
4. Build the **daemon** skeleton, hook ingest, scrub, classify, denylist.
5. First sprite set and the core scenes.

End of phase 0 you have the whole deck running on your monitor, reacting live to
your actual sessions. If you stopped here you would already have something.

## Phase 1, order week 1

**Fast order, about $60 plus the soldering station.** Local Tel Aviv shops or
Amazon so it lands in days: Pi Zero 2 W, SD card, PSU, header, the 2.4 inch
display, LEDs, resistors, breadboard, jumpers, soldering station and solder.

**Slow order, the rest.** AliExpress and LCSC, split into sub-threshold parcels.
Meters, arcade buttons, mushroom, flip cover, rotary switch, encoder, mech
switches, keycaps, toggles, PCA9685, MCP23017, NeoPixels, level shifter, I2S amp,
speaker, JST kit, wire, panel-mount connectors. 2 to 4 weeks.

**Order the print and the legend strip last**, once the case is modelled and the
real parts are in hand so every cutout is measured rather than guessed.

## Phase 2, when the fast parts land

1. Solder the 40-pin header. This is your first soldering ever, on a forgiving
   part, with 40 chances to get better at it. Do it slowly.
2. Flash the OS, set up USB gadget mode, confirm the link from both machines.
3. Blink one LED. Celebrate this more than it deserves.
4. Get the display running and put the simulator's rendering on it unchanged.
   This is the moment the project stops being abstract.
5. Overlay filesystem and the third partition.

## Phase 3, when the slow parts land

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

Only then wire it all together. Then the perfboard build, with a JST connector
on every subassembly so the panel can come out of the case without desoldering.

## Phase 4, the case

1. Model the enclosure in OpenSCAD from measured parts.
2. Print a **test panel only**, not the whole box, and check every cutout.
   This costs about $6 and saves a $35 mistake.
3. Print the full set in PETG.
4. Press in the heat-set inserts with the soldering iron.
5. Cut and fit the steel ballast plate, stick on the feet.
6. Laser-cut the engraved legend strip.
7. Final assembly.

## Phase 5, optional

- Custom PCB HAT in KiCad, five boards from JLCPCB for about $22 delivered.
  The second build is the one that lives in the case forever.
- MJF nylon reprint of the shell from the same STLs if you want the finish.

---

## Realistic timeline

| Week | What |
|---|---|
| 1 | Phase 0 software. Both orders placed. |
| 2 | Fast parts arrive. Header soldered, display running the real renderer. |
| 3-4 | Software polish. Sprite set finished. Case modelled. |
| 4-6 | Slow parts arrive. Subsystem bring-up on breadboard. |
| 6 | Perfboard build. Test panel printed and checked. |
| 7 | Full print, legend strip, assembly. |
| 8 | On your desk. |

Roughly two months, with most of it spent waiting rather than working.

## Skills you will pick up, in order

Through-hole soldering. Reading a datasheet for pinout and current limits.
I2C addressing and bus sharing. Debouncing. Why level shifting matters.
RC filtering as a poor man's DAC. Power budgeting. Parametric CAD. Design for
3D printing, tolerances, clearances and heat-set inserts. Panel layout
ergonomics.

None of it is hard. All of it is new, which is the point.
