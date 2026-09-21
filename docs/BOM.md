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

Twenty-one lines, verified against the cart on 2026-09-20.

| Item | Variant | Qty | Price |
|---|---|---|---|
| Kaisaya VU panel meter | 500µA 630Ω, 34mm, white face, warm backlight | 2 | ₪22.68 |
| WS2812B strip | **Black PCB, 1m, 60 LED/m, IP30** | 1 | ₪12.02 |
| MAX98357A I2S amp | 5-pack (spares for learning to solder) | 1 | ₪17.96 |
| Speaker | **4Ω 3W, 40mm** | 1 | ₪10.84 |
| PCA9685 16ch PWM | 1PCS | 1 | ₪9.94 |
| PTEN metal pushbutton, APPROVE | **green ring, 3-6V, 19mm, self-reset, pre-wired** | 1 | ₪9.18 |
| PTEN metal pushbutton, DENY | **red ring, 3-6V, 19mm, self-reset, pre-wired** | 1 | ₪9.58 |
| XB2-542 mushroom | **1NO1NC**, 22mm, latching e-stop | 1 | ₪14.90 |
| SR16 rotary band switch | **1 Pole 6 position**, 15mm shaft | 2 | ₪10.62 |
| Aluminium pointer knob | 20x15mm, 6mm knurled shaft, black | 4 | ₪5.78 |
| RV24YN20S potentiometer | **10K ohm**, 1 set/3 units, with A03 knob + dial plate | 1 | ₪4.22 |
| MTS-102 toggle switch | SPDT ON/ON, 10-pack | 1 | ₪9.06 |
| Gateron G Pro 3.0 switch | **G Brown 3.0** tactile, pre-lubed, 10-pack | 1 | ₪10.53 |
| DSA blank keycaps | **orange**, 1U, PBT, 20-pack | 1 | ₪15.10 |
| Chrome LED bezel holder | 5mm metal, 10-pack | 1 | ₪7.26 |
| Breadboard | **830 tie points**, MB-102 | 2 | ₪15.67 |
| Perfboard | double-sided, **8x12cm** | 1 | ₪5.64 |
| Resistor kit | 820pcs, 30 values, 1% metal film, 10Ω-1MΩ | 1 | ₪17.40 |
| Electrolytic cap kit | 12 values x 10pcs | 1 | ₪10.06 |
| LED assortment | 5mm box, 100pcs | 1 | ₪3.06 |
| CHANZON Dupont kit | 3x40pin M-M/M-F/F-F, 20cm | 1 | ₪3.06 |
| 2.54mm connector kit | 310pcs, housings 1-8 pin + male/female crimps | 1 | ₪10.99 |
| Silicone hookup wire | **22AWG**, 5 colours x 5m, dispenser box | 1 | ₪31.36 |
| Heat shrink assortment | **560pcs with box**, multiple diameters and colours | 1 | ₪20.94 |
| USB-C panel pigtail | **USB-C female screw flange to micro-USB male**, ~32cm, variant A3 | 1 | ₪10.04 |
| DC panel jack | **5.5x2.1mm**, pre-wired, with nut | 1 | ₪7.15 |
| KCD1 rocker switch | round 20mm, **3-pin red illuminated** (LED is 12V, see note) | 1 | ₪3.63 |
| KY-023 joystick | dual-axis analog thumbstick with push | 1 | ₪5.18 |
| ADS1115 ADC | 16-bit, 4 channel, I2C, reads the joystick | 1 | ₪4.83 |
| | | **Parts subtotal** | **₪318.68** |
| FNIRSI HS-02A soldering kit | 100-450°C, **6 tips + 100W PD adapter + stand + case**, EU plug | 1 | ₪241.79 |
| MECHANIC HX-T100 solder | **63% tin leaded**, rosin core, **0.6mm**, 55g | 1 | ₪16.84 |
| ANENG 620A multimeter | 6000 counts, true RMS, capacitance, temp, AC/DC current | 1 | ₪62.21 |
| SN-58B ratcheting crimper | **6 interchangeable jaws**, covers XH2.54 and DuPont2.54, cased | 1 | ₪46.88 |
| Plier set | 4-piece: sprue cutter, needle nose, diagonal cutter, combination | 1 | ₪73.87 |
| Toolour helping hands | flexible arms, vise clamp base, PCB holder | 1 | ₪17.85 |
| Desoldering braid | **2.5mm x 1.5M** | 1 | ₪4.81 |
| Desoldering pump | all-aluminium | 1 | ₪12.40 |
| Silicone soldering mat | anti-static, magnetic, 932°F | 1 | ₪11.73 |
| Hot glue gun | 20W, **EU plug**, 10 sticks | 1 | ₪6.68 |
| | | **Tools subtotal** | **₪495.06** |
| | | **Cart total, 39 lines** | **~₪814** |

Read the exact total at checkout after pressing **Select all items**; the sidebar
figure only reflects the ticked lines. Promotional prices also drift day to day
(the helping hands charged ₪31.70 when added and read ₪17.85 a day later), so
treat every figure here as approximate until the order confirmation.

Plus ₪16.01 shipping on the meters. Everything else ships free.

**Checkout trap: AliExpress does not auto-select newly added cart lines.** At 21
lines in the cart, only 10 were ticked for checkout and the estimated total read
₪94.42 instead of ₪232.97. Hit **Select all items** on the cart page before
checking out, or you will buy less than half the order and not notice.

Also at checkout: re-tick the meters and switch their shipping from Standard
₪16.01 back to Economy ₪7.91.

**Not in the cart, buy locally:** wire stripper, precision screwdriver set, fume
fan, M2.5/M3 screws and standoffs, M3 heat-set inserts, rubber feet. The first
three are behind the Max Combo wall below; the fasteners are cheaper and faster
from any Tel Aviv hardware shop than shipped. The 3mm white LEDs line is dropped:
the 100-piece 5mm assortment includes white and backlights the legend strip fine.

**Rocker switch LED note, resolved.** The KCD1's internal LED is sized for
12V. Originally flagged as dim/dark on this design's 5V rail; now that the
main input is 12V (the display forced that, see below), wiring the switch
on the raw 12V side ahead of the buck converter means it just works at full
brightness, no resistor mod needed.

**Display pulled from the verified cart, then re-verified against a real
listing.** The 2.4in SPI TFT that was ₪20.83 above is gone along with the
decision to use it (DECISIONS.md #20): the real display is an 11.6in
1366x768 HDMI/Type-C panel + driver board, ₪145.48, checked against a real
AliExpress listing (Heyman Store) on 2026-09-22 - see section B. That
listing also confirmed the driver board wants **12V, not 5V**, which is why
section A's power supply and the whole power budget in docs/HARDWARE.md
changed to a 12V-primary design with a buck converter for the logic side.

**Game Boy buttons upgraded to real switches.** First pass spec'd cheap 6x6mm
tactile pushbuttons; revised after actually thinking about how it'd feel
under a thumb, which is closer to a router reset button than a Game Boy face
button. A/B/START/SELECT now use the same Gateron G Pro switch and DSA
keycap already in the cart for CLD/NEW/PLAN/MIC (**the verified cart's
Gateron 10-pack and keycap 20-pack already cover all eight**, only 4 of each
were spoken for before, so this is a like-for-like part with zero new
listings to check, not a new sourcing job). A/B sit in a diagonal offset
(A upper-right, B lower-left) rather than a straight row, and START/SELECT
are a smaller pair off to the side, both matching a real Game Boy's layout
more than the panel's other rows-of-identical-switches do. MCP23017 #2 still
just needs its existing spare pins, no new IC either way.

**Game Boy audio needs nothing new.** It plays out the same F1 MAX98357A amp
and F2 speaker every other sound already uses. No BOM line, no section F
change.

**Effort dial, volume knob, speaker grille - added 2026-09-22.** The dial
reuses parts already in the cart (a second SR16 switch, a second pointer
knob). The volume pot was a placeholder price at first; sourced properly the
same day against a real listing (RV24YN20S, 10,000+ sold, 4.9/458 reviews) -
₪4.22 for a set of 3 with the knob and dial plate already included, cheaper
than the placeholder guessed and with 2 spares for free. The speaker grille
is a case feature, not a part - no BOM line at all.

**The "Max Combo" wall.** Whole tool categories on AliExpress are dominated by
listings that only sell through the Max Combo bundle flow, which has no quick-add
and opens a bundle-builder page instead. Wire strippers, precision screwdriver
sets and illuminated arcade buttons were all blocked this way. These need either
a direct product-page visit or buying locally.

**Third pricing trap: switching a variant can change the price several-fold, and
the modal updates silently.** The plier set showed ₪12.18 for the single 5-inch
plier; selecting the 4-piece variant made it **₪73.87**. Read the price back
*after* every variant change, not just before.

**Age gate.** Searching "automatic wire stripper" triggers an AliExpress
age-verification interstitial. Route around it with a different query rather than
confirming, or confirm it yourself.

**JST-XH dropped in favour of a 2.54mm Dupont-style kit.** Every JST-XH listing
sells housings and crimp terminals as separate one-per-account variants, so a
usable set cannot be assembled from one order. The 310-piece 2.54mm kit contains
housings from 1 to 8 pin plus both male and female crimps in a single SKU, works
with the same SN-28B crimper, and still gives polarised, serviceable connectors
between subassemblies. Decision 46's intent is unchanged.

**Wire is 22AWG rather than the 24/26AWG first specified.** One gauge has to
carry both the 5V LED run, which approaches an amp, and the signal wiring. 22AWG
covers both; 24AWG would be marginal on the power leg.

**The mushroom latches, and that is now deliberate.** Every 22mm mushroom on
AliExpress is an emergency-stop head: push to lock, twist to release. Genuine
spring-return mushrooms (XB2-BA42) did not surface. Rather than substitute a
non-mushroom button, the latching head is kept and the firmware handles it: fire
the interrupt on the press edge, then hold an INTERRUPTED state until the twist
releases the contact. The physically latched button becomes a visible indicator
that a run was killed, which is arguably better than a momentary. The 1NO1NC
contact block gives the Pi a clean normally-open contact. Decision 24 amended.

**The flip-up safety cover is dropped.** The e-stop head is already ~40mm and
guarded by its own collar, and covers are sized for 22mm flat buttons rather than
mushroom heads. The latching behaviour supplies the deliberateness the cover was
there to provide.

**Arcade buttons resolved: illuminated metal pushbuttons instead.** Approve and
Deny must light, because going dark when a call is un-approvable is the visible
half of the safety model. Cheap arcade buttons at ₪0.53 are not illuminated, and
every illuminated arcade listing found was a "Max Combo" bundle with no quick-add
or was 45mm, too large for a 160mm deck that also carries a mushroom, two knobs,
four keycaps and three toggles. The PTEN 19mm metal pushbutton lights properly,
panel mounts with a nut, suits the matte black instrument look, and ships with
wires attached, which spares soldering to tiny terminals.

**Two specs on these that are easy to get wrong.** The listing offers
**self-reset** and self-locking; self-locking would latch and break the button
semantics entirely. And it offers 3-6V, 12-24V and **220V** LEDs on the same
dropdown, which resets to 220V whenever the colour is changed. Both were verified
per button before adding.

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
| A4 | 12V 3A PSU, 5.5x2.1 barrel output | 1 | 8.00 | 8.00 | Was 5V 3A: the display's driver board wants 12V (confirmed against a real listing, see section B), so that's the main rail now. 3A minimum, see power budget in HARDWARE.md. |
| A5 | USB-A to micro-USB data cable, 0.5m | 1 | 2.00 | 2.00 | Data cable, not charge-only. |
| A6 | 12V to 5V buck converter module, 3A | 1 | 1.50 | 1.50 | Steps the main 12V rail down for the Pi/PCA9685/MCP23017s/amp, same as before - only the display taps 12V directly. |
| | | | | **42.50** | |

## B. Display

| # | Part | Qty | Unit | Total | Notes |
|---|---|---|---|---|---|
| B1 | 11.6in 1366x768 HDMI/Type-C LCD panel + driver board | 1 | 40.00 | 40.00 | Sourced 2026-09-22: Heyman Store on AliExpress, ₪145.48 for the 1366x768 variant (the 1920x1080 variant is ₪201.20, a real ~$17 premium for four times the pixels to push - not worth it on an 11.6in panel). Confirmed **12V 2A, DC 5.5mm** - not 5V, see the power budget rework in docs/HARDWARE.md. Thin data on this specific listing (8 sold, one adjacent review notes limited viewing angle/brightness, typical for this class of budget universal driver board) - worth a last look at the actual listing before checkout, not a guarantee. |
| | | | | **40.00** | |

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
| E4 | 6-position rotary switch, 1 pole | 2 | 2.50 | 5.00 | One is the session selector, one is the effort dial (5 of its 6 positions wired: LOW/MEDIUM/HIGH/XHIGH/MAX, Claude Code's real `/effort` levels). |
| E5 | Pointer knob for E4 | 2 | 1.50 | 3.00 | |
| E6 | EC11 rotary encoder with push | 2 | 1.20 | 2.40 | Second is a spare. |
| E7 | Knurled knob for E6 | 1 | 1.20 | 1.20 | |
| E8 | Mechanical key switches, Gateron | 8 | 0.75 | 6.00 | 4 for CLD/NEW/PLAN/MIC, 4 for Game Boy A/B/START/SELECT. Real switches with travel, not 6x6mm tacts, so the Game Boy buttons feel like something instead of a router reset button. |
| E9 | Blank keycaps | 8 | 0.90 | 7.00 | Legends: CLD / NEW / PLAN / MIC / A / B / START / SELECT. |
| E10 | SPDT mini toggle switches | 3 | 1.00 | 3.00 | MUTE, NIGHT, AUTO-ACCEPT. |
| E11 | RV24YN20S potentiometer, 10K ohm, with A03 knob + dial | 1 | 1.20 | 1.20 | Volume. Into the ADS1115's other spare channel (A2), same wiring style as the joystick's own axes. Real 24mm panel-mount part (RV24 series), same nut-and-bushing mounting as the rotary switches, not a PCB-mount type - comes 3 to a set, 2 spares free. |
| | | | | **42.80** | |

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
| A Core computer | 42.50 |
| B Display | 40.00 |
| C Light and IO expansion | 29.30 |
| D Analog meters | 17.00 |
| E Controls | 42.80 |
| F Audio | 6.00 |
| G Back panel and wiring | 33.00 |
| H Fasteners | 14.00 |
| I Prototyping | 11.00 |
| J Tools | 131.00 |
| **AliExpress order** | **366.60** |
| L Local fabrication | 66.00 |
| **Build total** | **432.60** |
| Shipping across parcels | ~20.00 |
| **All in** | **~453** |
| M PCB revision, later | 22.00 |

A second deck would cost about **$200**, since the tools and the spares are
already yours.
