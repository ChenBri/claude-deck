# Hardware

## Why the pinout looks like this

The brain changed from a Raspberry Pi Zero 2 W to a Radxa ZERO 3W on
2026-09-23 (DECISIONS.md #1, global Pi Zero 2 W shortage). This section is a
full redo, not a relabel: the RK3566's pin functions and numbering share
nothing with Broadcom's, so every assignment below was re-derived from
Radxa's own hardware interface reference
(docs.radxa.com/en/zero/zero3/hardware-design/hardware-interface), not
carried over. Provisional in the same sense case.scad is provisional
(DECISIONS.md #49/#52): real once hardware and overlays are in hand and
tested, a considered first pass until then.

A full panel wants NeoPixels, I2S audio, an I2C bus, an encoder, a 6-position
rotary switch, four mech keys, three toggles and three buttons. The display
is HDMI (DECISIONS.md #20, 11.6in 1366x768), which the ZERO 3W provides
natively via its own Micro HDMI port - no SPI or GPIO pins spent on it either
way.

The collisions and how they resolve on this SoC:

- **No PWM-DMA NeoPixel path like `rpi_ws281x` exists here** - that library is
  Broadcom PWM/PCM-DMA specific and does not run on Rockchip silicon. NeoPixel
  data instead goes out **SPI3's MOSI line (pin 19)**, bit-banged to WS2812
  timing the same way `rpi_ws281x` bit-bangs PWM - the peripheral is
  repurposed for its timing precision, not used as a real SPI transaction.
  Radxa's own docs cover WS2812B wiring directly. Needs root or a udev rule
  for `/dev/spidevX.Y`, same class of requirement `rpi_ws281x` had for GPIO.
- **The board has no analog output**, same as before. Both needles are driven
  from the PCA9685 at ~1.6kHz through an RC filter, with a trimpot per meter.
- **Not enough input pins.** An MCP23017 on I2C adds 16, which absorbs the
  rotary switch, the mech keys and the toggles. Latency-sensitive inputs (the
  three buttons and the encoder) stay on real GPIO.
- **3.3V logic, 5V LEDs**, same as before - the ZERO 3W's GPIOs are 3.3V
  (3.63V absolute max) same as the Pi's. WS2812B data still goes through a
  74AHCT125. Not optional.
- **Pins 3, 5, 27 and 28 carry extra pull-up resistors** for I2C device power
  (Radxa's own hardware note) and "work abnormally when used as GPIOs." The
  main I2C bus is deliberately placed on 27/28 to use those pull-ups rather
  than fight them; pins 3 and 5 are left spare rather than used as plain I/O.
- **Power comes in through the GPIO header, not a dedicated power port.** The
  ZERO 3W has exactly one OTG-capable port (USB-C 1) and it does both power
  and data - there's no second, power-only port like the Pi Zero 2 W's
  separate PWR IN. Confirmed on Radxa's own forum: pins 2 and 4 are tied
  directly to the same 5V rail as the USB-C 1 power path, so 5V from the buck
  converter goes there instead, and USB-C 1 stays data-only to the host -
  the same split the old "data port stays data-only" rule intended, just
  moved to a different physical pin. See "USB gadget mode" below.

## Pin map

| Pin | Radxa GPIO | Function |
|---|---|---|
| 1 | - | +3.3V |
| 2 | - | **+5V power in**, from the buck converter (see "Power comes in through the GPIO header" above) |
| 3 | GPIO1_A0 | spare (extra I2C pull-up present, see above - don't use as plain I/O) |
| 4 | - | +5V, same rail as pin 2 |
| 5 | GPIO1_A1 | spare (extra I2C pull-up present, same as pin 3) |
| 6 | - | GND |
| 7 | GPIO3_C4 | Encoder A |
| 8 | GPIO0_D1 | spare (UART2_M0 TX, the board's debug console - Radxa's own docs warn against repurposing it, leave the overlay off) |
| 9 | - | GND |
| 10 | GPIO0_D0 | spare (UART2_M0 RX, debug console, same caveat as pin 8) |
| 11 | GPIO3_A1 | APPROVE button, active low, internal pull-up |
| 12 | GPIO3_A3 | I2S3 BCLK (SCLK_M0), MAX98357A |
| 13 | GPIO3_A2 | spare (I2S3 MCLK_M0, unused - MAX98357A needs no MCLK) |
| 14 | - | GND |
| 15 | GPIO3_B0 | DENY button |
| 16 | GPIO3_B1 | Encoder B |
| 17 | - | +3.3V |
| 18 | GPIO3_B2 | Encoder push |
| 19 | GPIO4_C3 | NeoPixel data, SPI3 MOSI_M1, via 74AHCT125 |
| 20 | - | GND |
| 21 | GPIO4_C5 | spare (SPI3 MISO_M1, unused - NeoPixels are output-only) |
| 22 | GPIO3_C1 | Shutdown request / status |
| 23 | GPIO4_C2 | spare (SPI3 CLK_M1) |
| 24 | GPIO4_C6 | spare (SPI3 CS0_M1) |
| 25 | - | GND |
| 26 | - | not connected |
| 27 | GPIO4_B2 | I2C4 SDA, to PCA9685, two MCP23017, ADS1115 |
| 28 | GPIO4_B3 | I2C4 SCL |
| 29 | GPIO3_B3 | spare (I2C5 SCL_M0 - a second I2C bus, unused) |
| 30 | - | GND |
| 31 | GPIO3_B4 | spare (I2C5 SDA_M0) |
| 32 | GPIO3_C2 | spare |
| 33 | GPIO3_C3 | spare |
| 34 | - | GND |
| 35 | GPIO3_A4 | I2S3 LRCLK (LRCK_M0), MAX98357A |
| 36 | GPIO3_A7 | PANIC mushroom |
| 37 | GPIO1_A4 | MCP23017 INT, interrupt on input change |
| 38 | GPIO3_A6 | spare (I2S3 SDI_M0, unused - no audio input) |
| 39 | - | GND |
| 40 | GPIO3_A5 | I2S3 DIN (SDO_M0), into MAX98357A |

## PCA9685 channels, all outputs

| Ch | Drives |
|---|---|
| 0 | READY lamp |
| 1 | WORKING lamp |
| 2 | BLOCKED lamp |
| 3 | DONE lamp |
| 4 | LINK lamp |
| 5 | Legend strip backlight, left |
| 6 | Legend strip backlight, right |
| 7 | APPROVE button LED |
| 8 | DENY button LED |
| 9 | CONTEXT meter, through RC filter |
| 10 | FIVE_HOUR meter, through RC filter |
| 11 | Meter face backlight |
| 12-15 | spare |

Channel current limit is 25mA sinking, 10mA sourcing. Lamps are wired as sinks
from 5V with series resistors. All twelve channels breathe and dim in software,
which is what makes NIGHT mode and the blocked-state pulse possible.

**The PCA9685 runs in open-drain mode (MODE2 OUTDRV = 0), not the default
totem-pole.** Its logic supply has to be 3.3V: the breakout's I2C pull-ups go
to that same VCC, and the Radxa's pins are 3.63V absolute max. In totem-pole
mode an output's "high" is therefore 3.3V, which breaks both kinds of load on
this board. A lamp sinking from 5V still sees about 1.7V across it when its
channel is "off", enough for red and yellow LEDs to glow permanently; and the
meters would only ever see a 3.3V source. In open-drain mode an off channel is
high-impedance, so every LED load (lamps, legend and meter backlights, the
button rings) sinks cleanly from 5V, and each meter gets a 1k pull-up to 5V so
its drive is a true 0-5V swing again (see "Meter drive circuit" below). The
cost is that a meter channel's duty is inverted: sinking pulls the needle
down, so the driver writes `1 - level` for channels 9 and 10. No new parts:
the two 1k pull-ups come out of the resistor kit already ordered. DECISIONS.md
#68.

## I2C bus, addresses

On I2C4 (pins 27/28, see "Pin map" above - chosen for its built-in pull-ups).

| Device | Address | Job |
|---|---|---|
| PCA9685 | 0x40 | lamps, legend backlight, button LEDs, meters |
| MCP23017 #1 | 0x20 (A0-A2 low) | rotary switch, mech keys, toggles |
| MCP23017 #2 | 0x21 (A0 high) | joystick push, Game Boy A/B/START/SELECT, effort dial, spares |
| ADS1115 | 0x48 (ADDR to GND) | joystick X on A0, Y on A1; volume pot on A2; A3 spare |

Four devices, no address clashes, one bus. The second MCP23017 was ordered as a
spare from Digi-Key and is now the joystick's home.

## Joystick

KY-023 dual-axis thumbstick. VRx and VRy are 10k pots swept across 3.3V, read by
the ADS1115 at 16 bits; centre reads ~1.65V. SW is the push button, active low,
into MCP23017 #2 B0 with its internal pull-up. Deadzone and axis calibration live
in the settings file. Snake, Tetris and 2048 consume it as a 4-way plus centre,
Pong reads the raw y-axis continuously for paddle position; the Game Boy app
uses it as the d-pad.

## Game Boy buttons

A, B, START, SELECT: four Gateron G Pro switches, active low with pull-ups,
on MCP23017 #2 B1-B4, not 6x6mm tactile buttons. Game Boy app only; every
other scene ignores them. Laid out like the real thing rather than a row: A
and B diagonally offset, START/SELECT a smaller pair off to the side. This
is the one part of the panel where genuine ergonomics matter, since holding
down A while wiggling the joystick needs to not feel like poking a router's
reset button. See DECISIONS.md #55. The layout is provisional until the
case itself is designed (decision 49: case comes after the electronics
arrive), and may need the deck a little larger, same as the joystick did.

## Effort dial

A second SR16-family rotary switch (DECISIONS.md #59), same part as the
session selector, 5 of its 6 positions wired: LOW/MEDIUM/HIGH/XHIGH/MAX, on
MCP23017 #2's remaining spares, active low with pull-ups. Sends a labelled
action to the daemon, which types Claude Code's own `/effort <level>` slash
command into the terminal - a real, confirmed mechanism (see
`daemon/src/actions/`), not a guessed hotkey.

## Volume knob

A standalone panel-mount potentiometer (RV24YN20S, 10K ohm, docs/BOM.md E11),
not the joystick's KY-023 pots, wired the same way as the joystick's own
axes: swept across 3.3V, read by the ADS1115 at 16 bits on A2. Real 24mm
panel-mount part, nut-and-bushing mounted like the rotary switches, not a
PCB-mount type. Purely local to the deck - scales `chiptune.py`'s mixer
output, no daemon round-trip. Independent of the MUTE toggle.

## Game Boy audio

No new hardware. The emulator's audio goes out the same I2S path as every
other sound in this project: MAX98357A on GPIO18/19/21, into the 40mm
speaker. See DECISIONS.md #57.

## MCP23017 #1, all inputs with pull-ups

| Port | Pin | Input |
|---|---|---|
| A | 0-5 | Rotary switch positions: session 1-5, then ALL |
| A | 6-7 | spare |
| B | 0 | Mech key CLD, focus or launch Claude |
| B | 1 | Mech key NEW, new session |
| B | 2 | Mech key PLAN, plan mode |
| B | 3 | Mech key MIC, push to talk |
| B | 4 | Toggle MUTE |
| B | 5 | Toggle NIGHT |
| B | 6 | Toggle AUTO-ACCEPT |
| B | 7 | spare |

## MCP23017 #2, all inputs with pull-ups

| Port | Pin | Input |
|---|---|---|
| B | 0 | Joystick push (KY-023 SW) |
| B | 1 | Game Boy A |
| B | 2 | Game Boy B |
| B | 3 | Game Boy START |
| B | 4 | Game Boy SELECT |
| B | 5 | Effort dial LOW |
| B | 6 | Effort dial MEDIUM |
| B | 7 | Effort dial HIGH |
| A | 0 | Effort dial XHIGH |
| A | 1 | Effort dial MAX |
| A | 2-7 | spare |

## Meters, as ordered

Kaisaya 500µA / 630Ω analog panel meter, 34mm face, white dial, warm backlight.
Two ordered.

- **Series resistance.** Full scale needs 5V / 500µA = 10kΩ total, minus the 630Ω
  coil. The planned 2.2k fixed plus 10k trimpot covers this with room either side.
- **Backlight is specified 6-12V and our rail is 5V**, so the stock lamp will be
  dim or dead. Plan on replacing it with a white LED and series resistor driven
  from PCA9685 channel 11, which is already allocated to meter backlight. This is
  a known easy mod and it also gives the backlight dimming under NIGHT mode.
- **Case cutout is 34mm**, not the ~45x40mm the first draft assumed. Update the
  OpenSCAD panel parameters accordingly.

## Meter drive circuit, per meter

```
5V --[ 1k ]--+--[ 2.2k ]--+--[ 10k trimpot ]--> meter +
             |            |
       PCA9685 ch      [100uF]
   (open-drain, sinks)    |
                         GND                    meter - --> GND
```

The channel only ever pulls the 1k node low, so the needle reads high when the
channel is off and the driver inverts the duty (see the open-drain note under
"PCA9685 channels"). Sink current is 5V / 1k = 5mA plus the capacitor's
discharge through the 2.2k, well inside the 25mA sink limit. Series resistance
for full scale is still 10kΩ total: 1k + 2.2k + the 630Ω coil leaves the
trimpot at about 6.2k.

PWM at ~1.6kHz filtered to DC. Cutoff lands near 0.7Hz, which is slow enough to
be smooth and fast enough that the needle still visibly twitches with activity.
Set the trimpot so full software scale parks the needle exactly at the right-hand
stop. If a meter reads low, add an LM358 as a unity-gain buffer between the
filter and the movement.

## Power budget

**Confirmed, not a guess:** checked a real listing for the actual display
(Heyman Store, 11.6in 1366x768/1920x1080 HDMI/Type-C driver board kit,
₪145.48 for the 1366x768 variant, docs/BOM.md B1) - the board wants **12V
2A, DC 5.5mm barrel**, same connector standard already used elsewhere in
this project, just not the 5V this whole design otherwise runs on. That
changes which rail is "primary": the display needs 12V directly, and
everything else (the Radxa, PCA9685, MCP23017s, NeoPixels, amp) still wants 5V,
so the plan is now **one 12V input, with a small buck converter stepping
it down to 5V for the logic side** - a single wall wart and barrel jack,
not two power cords into the case.

| Load (5V side, through the buck converter) | Typical | Peak |
|---|---|---|
| Radxa ZERO 3W | 400mA | 700mA (a quad A55 @ 1.6GHz with WiFi 6 draws somewhat more than the Pi Zero 2 W did; treat as an estimate until measured) |
| NeoPixels, 30 total, capped at 40% brightness | 250mA | 700mA |
| Speaker on transients | 80mA | 500mA |
| Lamps and legend backlight, 7 channels | 90mA | 110mA |
| Meters and their backlights | 40mA | 60mA |
| **5V subtotal** | **860mA (4.30W)** | **2.07A (10.35W)** |

At an estimated 88% buck efficiency (a typical cheap module, not a
datasheet number for a specific one yet), that 5V load pulls roughly
**0.41A typical / 0.98A peak from the 12V rail.**

| Load (12V side) | Typical | Peak |
|---|---|---|
| 5V logic, via the buck converter | 0.41A | 0.98A |
| Display + driver board | ~0.3A (estimated; an LED-backlit panel this size doesn't really draw its full rated 2A continuously - that rating is the manufacturer's recommended supply headroom, not confirmed continuous draw) | up to 2A (the board's own rated max) |
| **12V total** | **~0.7A (8.5W)** | **~3.0A (36W)** |

Plan on a **12V 3A supply** (36W) for real margin over that estimated peak,
the same proportional headroom the old 5V 3A recommendation had over its
own computed peak. The buck converter module itself is a cheap BOM line
(docs/BOM.md); everything downstream of it (the Radxa's GPIO 5V pins,
PCA9685, MCP23017s) is unchanged, it just now receives 5V from the
converter instead of straight off the barrel jack.

One nice side effect: the KCD1 rocker switch's built-in LED (docs/BOM.md's
"Rocker switch LED note") is speced for 12V and used to need a resistor mod
to not look dim on this design's old 5V rail. Wired on the raw 12V input
side of the switch, ahead of the buck converter, it just works at full
brightness now - no mod needed.

**Wire the power correctly.** 12V from the barrel jack feeds the display board
and the buck converter directly; the buck converter's 5V output goes to the
Radxa through GPIO **pin 2 or 4** (see "Pin map" and the note above on why
there's no separate power port on this board). Never feed the raw 12V rail
into the Radxa or its GPIO header - only the buck converter's 5V output goes
there. The USB-C OTG port only ever carries data to the computer, never
power. Never feed 5V (or 12V) into the USB-C OTG port itself.

## USB gadget mode

The Radxa presents a composite USB device over its USB-C 1 (OTG) port - the
board's second port, USB-C 2, is host-mode only and cannot do this, see the
"Power comes in through the GPIO header" note above:

- **CDC-ECM** for macOS and Linux, **RNDIS** for Windows. Each host picks the
  configuration it understands. This is the status and control channel:
  a private point-to-point link at 10.55.0.1 (deck) and 10.55.0.2 (host),
  not routable, not on your LAN.
- **HID keyboard**, which only ever emits F13 through F20. See SAFETY.md.

If Windows refuses to bind RNDIS cleanly, the fallback is WiFi for the data
channel with HID still over USB. The `WIFI` toggle exists for exactly this.

**Planned: a third gadget function, mass storage, for ROM transfer.** The
composite gadget already carries CDC-ECM/RNDIS plus HID; a `g_mass_storage`
function can sit alongside them, backed by a FAT32 image file on the
writable `/var/deck` partition (root is read-only, so the backing file has
to live on partition 3, see SD card layout below). Normal operation: the
deck loop-mounts that image at `/var/deck/roms` and the Game Boy app reads
it like any other folder. Flip a new "USB drive mode" toggle in Settings:
the deck unmounts its own loop mount, binds the mass storage function via
configfs, and the same image appears as a drive on the connected PC to drag
ROMs onto. Flip it back and the deck unbinds the function and re-mounts
locally. Not implemented yet: no hardware to build the gadget config
against, same status as RealPanel (see docs/BUILD.md phase 0). Decision 56.

## SD card layout

| Partition | Mount | Mode |
|---|---|---|
| 1 | /boot | read-only |
| 2 | / | read-only with a RAM overlay |
| 3 | /var/deck | read-write, history and settings |

Root runs read-only so pulling the power can never corrupt the OS. The third
partition holds the settings file the encoder menu writes and the stats history,
mounted with `sync` and only written on state transitions.
