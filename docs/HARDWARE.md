# Hardware

## Why the pinout looks like this

A full panel wants NeoPixels, an SPI display, I2S audio, an I2C bus, an encoder,
a 6-position rotary switch, four mech keys, three toggles and three buttons.
That does not fit on 26 usable GPIOs without thought, and several of the
peripherals collide on the same silicon.

The collisions and how they resolve:

- **I2S audio takes GPIO18, 19 and 21.** Those are also SPI1 and the PCM
  peripheral, so once audio is in, SPI1 is gone and `rpi_ws281x` cannot use PCM.
- **NeoPixels need precise timing**, which on a Pi means PWM, PCM or SPI DMA.
  PCM is gone to audio, SPI0 is wanted for the display, so NeoPixels go on
  **PWM0 via GPIO12**. `rpi_ws281x` needs root, so it runs in a systemd service.
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
| 8 | 24 | SPI0 CE0, display CS |
| 9 | 21 | SPI0 MISO, unused, reserved |
| 10 | 19 | SPI0 MOSI, display SDA |
| 11 | 23 | SPI0 SCLK, display SCL |
| 12 | 32 | NeoPixel data, PWM0, via 74AHCT125 |
| 13 | 33 | spare, PWM1 |
| 14 | 8 | spare, UART TX, serial console disabled |
| 15 | 10 | spare, UART RX |
| 16 | 36 | Encoder A |
| 17 | 11 | Display backlight enable |
| 18 | 12 | I2S BCLK, MAX98357A |
| 19 | 35 | I2S LRCLK |
| 20 | 38 | spare |
| 21 | 40 | I2S DIN |
| 22 | 15 | Display DC |
| 23 | 16 | Display RST |
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
| MCP23017 #2 | 0x21 (A0 high) | joystick push, Game Boy A/B/START/SELECT, spares |
| ADS1115 | 0x48 (ADDR to GND) | joystick X on A0, Y on A1; A2/A3 spare |

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

| Load | Typical | Peak |
|---|---|---|
| Pi Zero 2 W | 350mA | 600mA |
| Display with backlight | 80mA | 110mA |
| NeoPixels, 30 total, capped at 40% brightness | 250mA | 700mA |
| Speaker on transients | 80mA | 500mA |
| Lamps and legend backlight, 7 channels | 90mA | 110mA |
| Meters and their backlights | 40mA | 60mA |
| **Total** | **890mA** | **2.08A** |

A 5V 3A supply carries this with margin. A 2A supply will brown out the moment a
white NeoPixel flash lands on top of a sound.

**Wire the power correctly.** 5V from the barrel jack goes to the Pi through the
PWR IN micro-USB port. The USB data port only ever connects to the computer.
Never feed 5V into the GPIO header while the data port is attached to a host.

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
