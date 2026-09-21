# Hardware

## Why the pinout looks like this

A full panel wants NeoPixels, I2S audio, an I2C bus, an encoder, a 6-position
rotary switch, four mech keys, three toggles and three buttons. That does not
fit on 26 usable GPIOs without thought, and several of the peripherals collide
on the same silicon. The display used to be SPI (an early collision point,
see below); it's HDMI now (DECISIONS.md #20, 11.6in 1366x768), which frees
GPIO8-11, 17, 22 and 23 entirely rather than resolving a collision on them.

The collisions and how they resolve:

- **I2S audio takes GPIO18, 19 and 21.** Those are also SPI1 and the PCM
  peripheral, so once audio is in, SPI1 is gone and `rpi_ws281x` cannot use PCM.
- **NeoPixels need precise timing**, which on a Pi means PWM, PCM or SPI DMA.
  PCM is gone to audio, so NeoPixels go on **PWM0 via GPIO12**. `rpi_ws281x`
  needs root, so it runs in a systemd service. (SPI0 was the other DMA option
  and is free now the display moved to HDMI, but PWM0 already works and
  there's no reason to redo it.)
- **The Pi has no analog output.** Both needles are driven from the PCA9685 at
  ~1.6kHz through an RC filter, with a trimpot per meter for full-scale calibration.
- **Not enough input pins.** An MCP23017 on I2C adds 16, which absorbs the rotary
  switch, the mech keys and the toggles. Latency-sensitive inputs (the three
  buttons and the encoder) stay on real GPIO.
- **3.3V logic, 5V LEDs.** WS2812B data goes through a 74AHCT125. Skipping this
  works until it randomly does not, and then you debug it for an evening.

## Pin map

| GPIO | Pin | Function |
|---|---|---|
| 2 | 3 | I2C1 SDA, to PCA9685, two MCP23017, ADS1115 |
| 3 | 5 | I2C1 SCL |
| 4 | 7 | APPROVE button, active low, internal pull-up |
| 5 | 29 | DENY button |
| 6 | 31 | PANIC mushroom |
| 7 | 26 | MCP23017 INT, interrupt on input change |
| 8 | 24 | spare, SPI0 CE0 (was display CS on the old SPI TFT) |
| 9 | 21 | spare, SPI0 MISO |
| 10 | 19 | spare, SPI0 MOSI (was display SDA) |
| 11 | 23 | spare, SPI0 SCLK (was display SCL) |
| 12 | 32 | NeoPixel data, PWM0, via 74AHCT125 |
| 13 | 33 | spare, PWM1 |
| 14 | 8 | spare, UART TX, serial console disabled |
| 15 | 10 | spare, UART RX |
| 16 | 36 | Encoder A |
| 17 | 11 | spare (was display backlight enable; HDMI panel's driver board handles its own backlight) |
| 18 | 12 | I2S BCLK, MAX98357A |
| 19 | 35 | I2S LRCLK |
| 20 | 38 | spare |
| 21 | 40 | I2S DIN |
| 22 | 15 | spare (was display DC) |
| 23 | 16 | spare (was display RST) |
| 24 | 18 | spare |
| 25 | 22 | Shutdown request / status |
| 26 | 37 | Encoder B |
| 27 | 13 | Encoder push |

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

## I2C bus, addresses

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
in the settings file. Snake and Tetris consume it as a 4-way plus centre; the
Game Boy app uses it as the d-pad.

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

A standalone panel-mount potentiometer, not the joystick's KY-023 pots, wired
the same way as the joystick's own axes: swept across 3.3V, read by the
ADS1115 at 16 bits on A2. Purely local to the Pi - scales `chiptune.py`'s
mixer output, no daemon round-trip. Independent of the MUTE toggle.

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
PCA9685 ch --[ 2.2k ]--+--[ 10k trimpot ]--> meter +
                       |
                     [100uF]
                       |
                      GND                    meter - --> GND
```

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
everything else (Pi, PCA9685, MCP23017s, NeoPixels, amp) still wants 5V,
so the plan is now **one 12V input, with a small buck converter stepping
it down to 5V for the logic side** - a single wall wart and barrel jack,
not two power cords into the case.

| Load (5V side, through the buck converter) | Typical | Peak |
|---|---|---|
| Pi Zero 2 W | 350mA | 600mA |
| NeoPixels, 30 total, capped at 40% brightness | 250mA | 700mA |
| Speaker on transients | 80mA | 500mA |
| Lamps and legend backlight, 7 channels | 90mA | 110mA |
| Meters and their backlights | 40mA | 60mA |
| **5V subtotal** | **810mA (4.05W)** | **1.97A (9.85W)** |

At an estimated 88% buck efficiency (a typical cheap module, not a
datasheet number for a specific one yet), that 5V load pulls roughly
**0.38A typical / 0.93A peak from the 12V rail.**

| Load (12V side) | Typical | Peak |
|---|---|---|
| 5V logic, via the buck converter | 0.38A | 0.93A |
| Display + driver board | ~0.3A (estimated; an LED-backlit panel this size doesn't really draw its full rated 2A continuously - that rating is the manufacturer's recommended supply headroom, not confirmed continuous draw) | up to 2A (the board's own rated max) |
| **12V total** | **~0.7A (8.4W)** | **~2.9A (35W)** |

Plan on a **12V 3A supply** (36W) for real margin over that estimated peak,
the same proportional headroom the old 5V 3A recommendation had over its
own computed peak. The buck converter module itself is a new, cheap BOM
line (docs/BOM.md); everything downstream of it (Pi's own micro-USB power
in, PCA9685, MCP23017s) is unchanged, it just now receives 5V from the
converter instead of straight off the barrel jack.

One nice side effect: the KCD1 rocker switch's built-in LED (docs/BOM.md's
"Rocker switch LED note") is speced for 12V and used to need a resistor mod
to not look dim on this design's old 5V rail. Wired on the raw 12V input
side of the switch, ahead of the buck converter, it just works at full
brightness now - no mod needed.

**Wire the power correctly.** 12V from the barrel jack feeds the display board
and the buck converter directly; the buck converter's 5V output goes to the
Pi through the PWR IN micro-USB port exactly as before. Never feed the raw
12V rail into the Pi or its GPIO header - only the buck converter's 5V
output goes there. The USB data port only ever connects to the computer.
Never feed 5V (or 12V) into the GPIO header while the data port is attached
to a host.

## USB gadget mode

The Pi presents a composite USB device over the data port:

- **CDC-ECM** for macOS and Linux, **RNDIS** for Windows. Each host picks the
  configuration it understands. This is the status and control channel:
  a private point-to-point link at 10.55.0.1 (Pi) and 10.55.0.2 (host),
  not routable, not on your LAN.
- **HID keyboard**, which only ever emits F13 through F20. See SAFETY.md.

If Windows refuses to bind RNDIS cleanly, the fallback is WiFi for the data
channel with HID still over USB. The `WIFI` toggle exists for exactly this.

**Planned: a third gadget function, mass storage, for ROM transfer.** The
composite gadget already carries CDC-ECM/RNDIS plus HID; a `g_mass_storage`
function can sit alongside them, backed by a FAT32 image file on the
writable `/var/deck` partition (root is read-only, so the backing file has
to live on partition 3, see SD card layout below). Normal operation: the Pi
loop-mounts that image at `/var/deck/roms` and the Game Boy app reads it
like any other folder. Flip a new "USB drive mode" toggle in Settings: the
Pi unmounts its own loop mount, binds the mass storage function via
configfs, and the same image appears as a drive on the connected PC to drag
ROMs onto. Flip it back and the Pi unbinds the function and re-mounts
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
