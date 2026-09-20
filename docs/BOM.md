# Bill of materials

Prices in USD, typical AliExpress / LCSC pricing unless noted. Local Israeli
shops run roughly 1.5x to 2.5x on the same parts, which is worth paying for the
few items you want this week.

**Israeli import note.** Personal imports under **$75** are exempt from VAT and
customs. Above that, VAT applies to goods plus shipping. Splitting the AliExpress
order into several sub-$75 parcels is a deliberate saving, not a trick. Verify
the current threshold and rate before ordering, both have moved in recent years.

---

## A. Core computer

| # | Part | Qty | Unit | Total | Notes |
|---|---|---|---|---|---|
| A1 | Raspberry Pi Zero 2 W | 1 | 25.00 | 25.00 | Official price is $15, real-world in Israel is $22-35. Buy from a reputable seller, not the cheapest. |
| A2 | microSD 32GB A1 (SanDisk / Samsung) | 1 | 7.00 | 7.00 | The A1 rating matters for random IO. Do not buy no-name. |
| A3 | 2x20 male GPIO header | 1 | 1.00 | 1.00 | Ships unpopulated. This is your first 40 solder joints. |
| A4 | 5V 3A PSU, barrel output | 1 | 9.00 | 9.00 | See the power budget in HARDWARE.md. 2A is not enough. |
| A5 | USB-A to micro-USB data cable, 0.5m | 1 | 3.00 | 3.00 | Must be a data cable. Many are charge-only. |
| | | | | **45.00** | |

## B. Display

| # | Part | Qty | Unit | Total | Notes |
|---|---|---|---|---|---|
| B1 | 2.4 inch IPS SPI TFT, ST7789 or ILI9341, 320x240 | 1 | 10.00 | 10.00 | Confirm it exposes DC, RST and BL pins separately. |
| | | | | **10.00** | |

## C. Light

| # | Part | Qty | Unit | Total | Notes |
|---|---|---|---|---|---|
| C1 | PCA9685 16-channel PWM board | 1 | 4.00 | 4.00 | Drives all lamps and both meters over I2C. Frees the hardware PWM on the Pi. |
| C2 | MCP23017 I2C GPIO expander | 1 | 2.50 | 2.50 | 16 extra inputs for the rotary switch, mech keys and toggles. |
| C3 | 5mm diffused LEDs, assorted colours | 10 | 0.25 | 2.50 | Five lamps plus spares. Diffused, not water-clear. |
| C4 | Chrome LED bezel holders, 5mm | 5 | 0.50 | 2.50 | The cheapest upgrade to how the panel looks. |
| C5 | WS2812B ring, 12 LED | 1 | 4.00 | 4.00 | Halo around the screen bezel. |
| C6 | WS2812B strip, 60/m, 300mm cut | 1 | 3.00 | 3.00 | Underglow. |
| C7 | 74AHCT125 level shifter | 2 | 0.75 | 1.50 | 3.3V to 5V for NeoPixel data. Buy two, they are cheap. |
| C8 | 3mm white LEDs for legend backlight | 4 | 0.30 | 1.20 | Behind the engraved acrylic. |
| C9 | Resistor and capacitor assortment kit | 1 | 8.00 | 8.00 | You will use this on every future project. |
| C10 | 10k trimpots, meter calibration | 2 | 0.60 | 1.20 | |
| C11 | LM358 op-amp, meter buffer | 2 | 0.50 | 1.00 | Optional. Use if the needles read low through the RC filter. |
| | | | | **28.90** | |

## D. Analog meters

| # | Part | Qty | Unit | Total | Notes |
|---|---|---|---|---|---|
| D1 | Analog VU panel meter, ~45x40mm, backlit | 2 | 9.00 | 18.00 | Get the backlit type. Buy both from one seller so they match. |
| | | | | **18.00** | |

## E. Controls

| # | Part | Qty | Unit | Total | Notes |
|---|---|---|---|---|---|
| E1 | 24mm illuminated arcade button, 5V LED | 2 | 3.50 | 7.00 | APPROVE green, DENY red. |
| E2 | 22mm mushroom head pushbutton | 1 | 5.00 | 5.00 | Emergency-stop style. Momentary, not latching. |
| E3 | Hinged safety flip cover, red | 1 | 4.00 | 4.00 | Check the diameter matches the mushroom. |
| E4 | 6-position rotary switch, 1 pole | 1 | 3.00 | 3.00 | Session selector: 1 to 5 plus ALL. |
| E5 | Pointer knob for E4 | 1 | 2.00 | 2.00 | The pointer is the whole point. |
| E6 | EC11 rotary encoder with push | 1 | 1.50 | 1.50 | |
| E7 | Knurled knob for E6 | 1 | 1.50 | 1.50 | |
| E8 | Mechanical key switches, Gateron or Cherry | 4 | 1.00 | 4.00 | Tactile browns or clicky blues, your call. |
| E9 | Blank or custom keycaps | 4 | 1.00 | 4.00 | Legends: CLD / NEW / PLAN / MIC. |
| E10 | SPDT mini toggle switches | 3 | 1.20 | 3.60 | MUTE, NIGHT, AUTO-ACCEPT. |
| | | | | **35.60** | |

## F. Audio

| # | Part | Qty | Unit | Total | Notes |
|---|---|---|---|---|---|
| F1 | MAX98357A I2S amplifier board | 1 | 4.00 | 4.00 | |
| F2 | 3W 4ohm speaker, 40mm | 1 | 3.00 | 3.00 | |
| | | | | **7.00** | |

## G. Back panel and wiring

| # | Part | Qty | Unit | Total | Notes |
|---|---|---|---|---|---|
| G1 | Panel-mount USB-C to micro-USB pigtail, USB 2.0 data | 1 | 6.00 | 6.00 | Data, not charge-only. |
| G2 | Panel-mount 5.5x2.1 barrel jack pigtail | 1 | 3.00 | 3.00 | |
| G3 | Illuminated rocker switch, 16mm | 1 | 3.00 | 3.00 | Power switch on the back. |
| G4 | JST-XH connector kit with crimps | 1 | 9.00 | 9.00 | Every subassembly gets a connector. Future you will be grateful. |
| G5 | Silicone hookup wire, 24 and 26 AWG, multi-colour | 1 | 10.00 | 10.00 | Silicone, not PVC. It does not melt when you solder next to it. |
| G6 | Heat shrink assortment | 1 | 4.00 | 4.00 | |
| G7 | Dupont jumper wires, M-M / M-F / F-F | 1 | 4.00 | 4.00 | For the breadboard phase. |
| | | | | **39.00** | |

## H. Structure

| # | Part | Qty | Unit | Total | Notes |
|---|---|---|---|---|---|
| H1 | FDM PETG print: shell, bezel, deck, back panel, brackets | 1 | 35.00 | 35.00 | Online service or a Tel Aviv print shop. Matte black. |
| H2 | Laser-cut and engraved acrylic legend strip | 1 | 18.00 | 18.00 | Usually a minimum order charge. Get two while you are there. |
| H3 | 3mm steel or aluminium ballast plate, cut to size | 1 | 8.00 | 8.00 | Any metal shop will shear it in two minutes. |
| H4 | M2.5 / M3 screw and standoff assortment | 1 | 9.00 | 9.00 | |
| H5 | M3 brass heat-set inserts | 1 | 5.00 | 5.00 | Pressed in with the soldering iron. Turns a printed box into a real one. |
| H6 | Rubber feet, self-adhesive | 4 | 0.50 | 2.00 | |
| | | | | **77.00** | |

## I. Prototyping

| # | Part | Qty | Unit | Total | Notes |
|---|---|---|---|---|---|
| I1 | Solderless breadboard, 830 point | 2 | 4.00 | 8.00 | Phase 2 happens here before anything gets soldered. |
| I2 | Double-sided perfboard / stripboard | 3 | 2.00 | 6.00 | Buy spares. You will redo at least one. |
| | | | | **14.00** | |

## J. Tools, one-time

| # | Part | Qty | Unit | Total | Notes |
|---|---|---|---|---|---|
| J1 | Temperature-controlled soldering station (Yihua 939D+, or Pinecil V2 plus PSU) | 1 | 45.00 | 45.00 | Do not buy a fixed-temperature pencil iron. This is the difference between enjoying the build and hating it. |
| J2 | Solder 0.6mm 100g, plus flux pen | 1 | 12.00 | 12.00 | Leaded 63/37 is far easier to learn on. Ventilate and wash your hands. |
| J3 | Wire strippers, flush cutters, fine pliers | 1 | 18.00 | 18.00 | |
| J4 | Digital multimeter | 1 | 18.00 | 18.00 | The continuity beep alone will save you hours. |
| J5 | Helping hands with magnifier, or a small PCB vise | 1 | 12.00 | 12.00 | |
| J6 | Desoldering wick and pump | 1 | 6.00 | 6.00 | You will need this. Everyone needs this. |
| J7 | JST and Dupont crimping tool, SN-28B | 1 | 16.00 | 16.00 | |
| J8 | Hot glue gun and sticks | 1 | 9.00 | 9.00 | Strain relief, not structure. |
| J9 | Precision screwdriver set | 1 | 12.00 | 12.00 | |
| J10 | Silicone soldering mat | 1 | 8.00 | 8.00 | Saves your desk. |
| J11 | Isopropyl alcohol and brush | 1 | 5.00 | 5.00 | Flux residue cleanup. |
| J12 | Small fume fan | 1 | 15.00 | 15.00 | Optional, strongly recommended if you solder indoors. |
| | | | | **176.00** | |

## K. Phase 4, optional PCB revision

| # | Part | Qty | Unit | Total | Notes |
|---|---|---|---|---|---|
| K1 | JLCPCB 2-layer HAT, 5 boards | 1 | 2.00 | 2.00 | The boards genuinely cost $2. |
| K2 | Shipping to Israel | 1 | 20.00 | 20.00 | The shipping is the cost. |
| | | | | **22.00** | |

---

## Totals

| Group | USD |
|---|---|
| A Core computer | 45.00 |
| B Display | 10.00 |
| C Light | 28.90 |
| D Meters | 18.00 |
| E Controls | 35.60 |
| F Audio | 7.00 |
| G Back panel and wiring | 39.00 |
| H Structure | 77.00 |
| I Prototyping | 14.00 |
| **Parts subtotal** | **274.50** |
| J Tools, one-time | 176.00 |
| **Build total, first time** | **450.50** |
| K PCB revision, later | 22.00 |

Add roughly **$25 to $40** for shipping across several orders, plus VAT on any
single parcel over the exemption threshold.

**Realistic all-in: $500 to $520** for the first build including every tool.
**A second one would cost about $275**, because the tools are already yours.

## If you want it cheaper

| Drop | Saves | Costs you |
|---|---|---|
| Both analog meters | 18.00 | The best-looking parts on the panel. |
| Engraved legend strip, print the labels instead | 18.00 | The detail people notice first. |
| Audio entirely | 7.00 | Knowing it finished without looking up. |
| Mech keys, use cheap tactile buttons | 6.00 | Feel. |
| Panel-mount connectors, use grommets | 12.00 | Looking like a product. |
| Minimum viable tools instead of a proper kit | 90.00 | Enjoying the build. Not recommended. |

## Start-this-week order, about $60

Enough to have something blinking on your desk before the main order lands:
Pi Zero 2 W, SD card, PSU, header, the 2.4 inch display, a handful of LEDs and
resistors, a breadboard and jumpers, and the soldering station. Everything else
can wait for the slow boat.
