# Bill of materials

Three suppliers, all ordered the same day. Prices in USD unless shown in shekels.

| Source | Covers | Why |
|---|---|---|
| **Digi-Key** | Pi Zero 2 W, and the genuine ICs (see `digikey-bom.csv`) | $15 for the Pi against ₪234 on AliExpress. In stock today. Removes counterfeit risk on the logic chips. Upload the CSV to their BOM tool. |
| **piitel.co.il** | SanDisk 32GB Ultra microSD, ₪50 | A real card from an Israeli reseller. AliExpress offers only fake-capacity listings at this size. |
| **AliExpress** | Everything else: sections C through J | Genuinely the best value for modules, LEDs, mechanical parts and tools. |

**Sourcing checked 2026-09-20.** There is no Pi Zero 2 W shortage. It was in stock
at eleven distributors that day: The Pi Hut £14.40, Digi-Key $15.00, Pi-Shop CHF
17.10, BerryBase €17.90, Kubii €18.00, Botland PLN 72.90 and others. Farnell
Israel lists the correct $14.89 price but cannot deliver until April 2027 on a
54-week lead time, which is a Farnell supply situation and not a market one.
piitel has the right price, ₪85 bare and ₪105 with headers, but both were out of
stock. The ₪234 on AliExpress is pure markup.

Lead time is 2 to 5 weeks. Items ship from different sellers and will arrive
staggered over that window.

**Israeli import note.** Personal imports under **$75** are exempt from VAT and
customs. Orders from different sellers ship as separate parcels, which keeps most
of them under the threshold on their own. Verify the current threshold and rate
before ordering, both have moved in recent years.

**Spares.** A few cheap, critical parts are ordered in twos. A dead display or a
cooked level shifter three weeks into the build otherwise stops everything.

## Cart in progress, verified prices

Prices below are read from the cart, not from the search tile. See the pricing
trap note underneath for why that distinction matters.

| Item | Variant | Qty | Price | Shipping |
|---|---|---|---|---|
| 2.4in 240x320 SPI TFT | With Touch ILI9341, 14-pin, 42.8x77mm | 1 | ₪20.83 | free |
| Kaisaya VU panel meter | 500µA 630Ω, 34mm, white face, warm backlight | 2 | ₪11.34 ea | ₪16.01 |
| WS2812B strip | Black PCB, 1m, 60 LED/m, IP30 | 1 | ₪12.02 | free |
| CHANZON Dupont kit | 3x40pin M-M/M-F/F-F, 20cm | 1 | ₪3.06 | free |

Still to add: PCA9685, arcade buttons, mushroom and flip cover, rotary switch and
knobs, mech switches and keycaps, toggles, MAX98357A and speaker, LEDs and
bezels, R/C kit, breadboards and perfboard, JST kit, silicone wire, heat shrink,
panel connectors, fasteners, and the tools.

**Two pricing traps, both verified.**

1. **Welcome-deal pricing is one per account.** Huge numbers of listings advertise
   ₪3.06 or ₪3.40. That is a first-order promotional price, and it is consumed by
   whichever item uses it first. The display tile said ₪3.06 and landed in the
   cart at **₪20.83**. The LED strip tile said ₪3.40 and landed at **₪12.02**.
   Always read the price back from the cart.
2. **The variant trap.** Multi-variant listings advertise the cheapest variant,
   not the one in the title. Checked on 2026-09-20: the top-selling "Raspberry Pi
   Zero 2 W" listing at ₪93.77 defaults to bundle **Zero V1.3**, the original 2015
   single-core board, which cannot run this project. Its actual Zero 2 W variant
   is ₪234.22. Select and confirm the variant on every multi-variant line.

**Design change made while sourcing.** The NeoPixel ring is dropped. A circular
ring does not fit a rectangular CRT bezel, and the halo around an ~80x70mm bezel
is about 300mm of perimeter, which is 18 LEDs of 60/m strip. Underglow is another
18. One metre of strip covers both jobs, fits the geometry, and costs less than a
ring plus a strip. Decision 18 is amended accordingly.

**Variant trap, verified.** Most AliExpress listings for these parts are
multi-variant, and the advertised price is always the cheapest variant, not the
one in the title. Checked on 2026-09-20: the top-selling "Raspberry Pi Zero 2 W"
listing at ₪93.77 defaults to bundle **Zero V1.3**, the original 2015 single-core
board, which cannot run this project. The Zero 2 W variant is a different price.
Sorting search results by price and buying the top hit will put the wrong part in
the cart. Select and confirm the variant on every multi-variant line: the Pi, the
display, the meters, the arcade buttons, the toggles, the encoder and the
soldering station.

---

## A. Core computer

| # | Part | Qty | Unit | Total | Notes |
|---|---|---|---|---|---|
| A1 | Raspberry Pi Zero 2 W | 1 | 24.00 | 24.00 | Seller with high ratings and real feedback photos. |
| A2 | microSD 32GB A1 (SanDisk or Samsung) | 1 | 6.00 | 6.00 | A1 rating required for random IO. |
| A3 | 2x20 male GPIO header, 2.54mm | 1 | 1.00 | 1.00 | Ships unpopulated. |
| A4 | 5V 3A PSU, 5.5x2.1 barrel output | 1 | 7.00 | 7.00 | 3A minimum, see power budget in HARDWARE.md. |
| A5 | USB-A to micro-USB data cable, 0.5m | 1 | 2.00 | 2.00 | Data cable, not charge-only. |
| | | | | **40.00** | |

## B. Display

| # | Part | Qty | Unit | Total | Notes |
|---|---|---|---|---|---|
| B1 | 2.4 inch IPS SPI TFT, ST7789 or ILI9341, 320x240 | 2 | 9.00 | 18.00 | Must expose DC, RST and BL pins separately. Second is a spare. |
| | | | | **18.00** | |

## C. Light and IO expansion

| # | Part | Qty | Unit | Total | Notes |
|---|---|---|---|---|---|
| C1 | PCA9685 16-channel PWM board | 1 | 3.50 | 3.50 | Drives all lamps and both meters over I2C. |
| C2 | MCP23017 I2C GPIO expander | 2 | 2.00 | 4.00 | 16 inputs for rotary switch, keys and toggles. Second is a spare. |
| C3 | 5mm diffused LEDs, assorted colours | 10 | 0.20 | 2.00 | Diffused, not water-clear. |
| C4 | Chrome LED bezel holders, 5mm | 5 | 0.50 | 2.50 | |
| C5 | WS2812B ring, 12 LED | 1 | 3.50 | 3.50 | Bezel halo. |
| C6 | WS2812B strip, 60 LED/m, 1m | 1 | 2.50 | 2.50 | 300mm cut for underglow, rest is spare. |
| C7 | 74AHCT125 level shifter, DIP | 2 | 0.75 | 1.50 | 3.3V to 5V for NeoPixel data. |
| C8 | 3mm white LEDs | 4 | 0.25 | 1.00 | Legend strip backlight. |
| C9 | Resistor and capacitor assortment kit | 1 | 7.00 | 7.00 | |
| C10 | 10k trimpots | 2 | 0.50 | 1.00 | Meter full-scale calibration. |
| C11 | LM358 op-amp, DIP | 2 | 0.40 | 0.80 | Meter buffer if the needles read low. |
| | | | | **29.30** | |

## D. Analog meters

| # | Part | Qty | Unit | Total | Notes |
|---|---|---|---|---|---|
| D1 | Analog VU panel meter, ~45x40mm, backlit | 2 | 8.50 | 17.00 | Both from one seller so the faces match. |
| | | | | **17.00** | |

## E. Controls

| # | Part | Qty | Unit | Total | Notes |
|---|---|---|---|---|---|
| E1 | 24mm illuminated arcade button, 5V LED | 2 | 3.00 | 6.00 | APPROVE green, DENY red. |
| E2 | 22mm mushroom head pushbutton | 1 | 4.50 | 4.50 | Momentary, not latching. |
| E3 | Hinged safety flip cover, red | 1 | 3.50 | 3.50 | Diameter must match E2. |
| E4 | 6-position rotary switch, 1 pole | 1 | 2.50 | 2.50 | Sessions 1-5 plus ALL. |
| E5 | Pointer knob for E4 | 1 | 1.50 | 1.50 | |
| E6 | EC11 rotary encoder with push | 2 | 1.20 | 2.40 | Second is a spare. |
| E7 | Knurled knob for E6 | 1 | 1.20 | 1.20 | |
| E8 | Mechanical key switches, Gateron | 4 | 0.75 | 3.00 | |
| E9 | Blank keycaps | 4 | 0.90 | 3.50 | Legends: CLD / NEW / PLAN / MIC. |
| E10 | SPDT mini toggle switches | 3 | 1.00 | 3.00 | MUTE, NIGHT, AUTO-ACCEPT. |
| | | | | **31.10** | |

## F. Audio

| # | Part | Qty | Unit | Total | Notes |
|---|---|---|---|---|---|
| F1 | MAX98357A I2S amplifier board | 1 | 3.50 | 3.50 | |
| F2 | 3W 4ohm speaker, 40mm | 1 | 2.50 | 2.50 | |
| | | | | **6.00** | |

## G. Back panel and wiring

| # | Part | Qty | Unit | Total | Notes |
|---|---|---|---|---|---|
| G1 | Panel-mount USB-C to micro-USB pigtail, USB 2.0 data | 1 | 5.00 | 5.00 | Data, not charge-only. |
| G2 | Panel-mount 5.5x2.1 barrel jack pigtail | 1 | 2.50 | 2.50 | |
| G3 | Illuminated rocker switch, 16mm | 1 | 2.00 | 2.00 | |
| G4 | JST-XH connector kit with crimps | 1 | 8.00 | 8.00 | |
| G5 | Silicone hookup wire, 24 and 26 AWG, multi-colour | 1 | 9.00 | 9.00 | Silicone, not PVC. |
| G6 | Heat shrink assortment | 1 | 3.50 | 3.50 | |
| G7 | Dupont jumper wires, M-M / M-F / F-F | 1 | 3.00 | 3.00 | Breadboard phase. |
| | | | | **33.00** | |

## H. Fasteners

| # | Part | Qty | Unit | Total | Notes |
|---|---|---|---|---|---|
| H1 | M2.5 and M3 screw and standoff assortment | 1 | 8.00 | 8.00 | |
| H2 | M3 brass heat-set inserts | 1 | 4.50 | 4.50 | Pressed in with the soldering iron. |
| H3 | Rubber feet, self-adhesive | 4 | 0.40 | 1.50 | |
| | | | | **14.00** | |

## I. Prototyping

| # | Part | Qty | Unit | Total | Notes |
|---|---|---|---|---|---|
| I1 | Solderless breadboard, 830 point | 2 | 3.00 | 6.00 | |
| I2 | Double-sided perfboard / stripboard | 3 | 1.70 | 5.00 | |
| | | | | **11.00** | |

## J. Tools

| # | Part | Qty | Unit | Total | Notes |
|---|---|---|---|---|---|
| J1 | Temperature-controlled soldering station, Yihua 939D+ | 1 | 35.00 | 35.00 | Adjustable temperature required. |
| J2 | Solder 0.6mm 63/37, 100g, plus flux pen | 1 | 9.00 | 9.00 | Ventilate, wash hands after. |
| J3 | Wire strippers, flush cutters, fine pliers set | 1 | 14.00 | 14.00 | |
| J4 | Digital multimeter | 1 | 13.00 | 13.00 | |
| J5 | Helping hands with magnifier | 1 | 9.00 | 9.00 | |
| J6 | Desoldering wick and pump | 1 | 4.00 | 4.00 | |
| J7 | JST and Dupont crimping tool, SN-28B | 1 | 13.00 | 13.00 | |
| J8 | Hot glue gun and sticks | 1 | 7.00 | 7.00 | Strain relief only. |
| J9 | Precision screwdriver set | 1 | 9.00 | 9.00 | |
| J10 | Silicone soldering mat | 1 | 6.00 | 6.00 | |
| J11 | Small fume fan | 1 | 12.00 | 12.00 | |
| | | | | **131.00** | |

---

## L. Local fabrication

Four items that cannot be an AliExpress catalogue order. The case and the legend
strip are cut from our own files to fit measured parts, so they are made locally
after the electronics are in hand and dimensions are confirmed. Isopropyl is
flammable and does not ship.

| # | Item | Total | Notes |
|---|---|---|---|
| L1 | FDM PETG print: shell, bezel, deck, back panel, brackets. Matte black. | 35.00 | Tel Aviv print shop, from the OpenSCAD STLs. |
| L2 | Laser-cut and engraved acrylic legend strip | 18.00 | Same shop or a laser service, from the Inkscape SVG. Order two. |
| L3 | 3mm steel plate, cut to base size | 8.00 | Any metal shop will shear it in two minutes. |
| L4 | Isopropyl alcohol and brush | 5.00 | Flux residue cleanup. Local pharmacy or hardware shop. |
| | | **66.00** | |

## M. PCB revision

Ordered later, once the perfboard build is proven and the layout is final.

| # | Item | Total |
|---|---|---|
| M1 | JLCPCB 2-layer HAT, 5 boards | 2.00 |
| M2 | Shipping to Israel | 20.00 |
| | | **22.00** |

---

## Totals

| Group | USD |
|---|---|
| A Core computer | 40.00 |
| B Display | 18.00 |
| C Light and IO expansion | 29.30 |
| D Analog meters | 17.00 |
| E Controls | 31.10 |
| F Audio | 6.00 |
| G Back panel and wiring | 33.00 |
| H Fasteners | 14.00 |
| I Prototyping | 11.00 |
| J Tools | 131.00 |
| **AliExpress order** | **330.40** |
| L Local fabrication | 66.00 |
| **Build total** | **396.40** |
| Shipping across parcels | ~20.00 |
| **All in** | **~416** |
| M PCB revision, later | 22.00 |

A second deck would cost about **$200**, since the tools and the spares are
already yours.
