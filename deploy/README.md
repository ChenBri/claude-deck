# Deploying to the deck

Everything here runs on the Radxa ZERO 3W except `deploy.ps1`, which runs on
the PC. Written before the board arrived: anything marked **verify** is a
guess about the board or image to confirm on first boot, not a known fact.

| File | Does |
|---|---|
| `setup.sh` | One-time provisioning: packages, the `deck` user, udev rules, the app and its venv on `/var/deck`, the USB link, SSH, services, WiFi off, then `--readonly` for the read-only root |
| `usb-gadget.sh` | The composite USB device: RNDIS or ECM networking plus a keyboard that can only send F13 to F20 |
| `network/10-usb-link.network` | 10.55.0.1 on the deck, a DHCP server that hands out 10.55.0.2 and nothing else |
| `systemd/` | `deck-gadget` (the gadget), `deck` (the firmware), `deck-radio-off` (WiFi and Bluetooth blocked at boot) |
| `udev/99-claude-deck.rules` | Just the devices the panel needs, for the unprivileged `deck` user |
| `deploy.ps1` | Push code from the PC over the USB link and restart the firmware |

## Bring-up, in order

1. **Flash** Radxa's official Debian image for the ZERO 3W, the CLI variant
   (a desktop would hold the display the firmware draws to). Soldered header
   first, see docs/BUILD.md phase 2.

2. **Make the data partition** before first boot, from the PC: shrink or cap
   the root partition and add a third ext4 partition labelled `DECKDATA`
   (1GB is plenty; ROMs go here too). On Linux or WSL with the card attached:
   `sudo parted /dev/sdX mkpart primary ext4 <end-of-root> 100%`, then
   `sudo mkfs.ext4 -L DECKDATA /dev/sdX3`. **Verify** the image doesn't grow
   its root to fill the card on first boot; if it does, create the partition
   after that and shrink root offline. `setup.sh` refuses to run without it
   and never partitions anything itself.

3. **First boot** with the HDMI panel and a USB keyboard on USB-C 2 (the
   host-only port). Connect WiFi, add your SSH public key to the login user's
   `~/.ssh/authorized_keys` (SSH becomes key-only and USB-link-only), clone
   this repo, and run `sudo deploy/setup.sh`. WiFi is blocked from the next
   boot on, so do anything that needs the network first. The WiFi network you
   connected stays saved (as long as it was saved before `--readonly`), so
   Settings > wifi radio can bring it back later, for the RNDIS fallback in
   docs/HARDWARE.md or to pull an update.

4. **Overlays.** `setup.sh` ends with a checklist. For every MISSING line,
   enable the overlay in `sudo rsetup` -> Overlays: I2C4 on pins 27/28, SPI3
   (M1) with a spidev on CS0, I2S3 (M0) for the MAX98357A, and the USB-C 1 OTG
   port in peripheral mode. **Verify** the exact overlay names on the image;
   Radxa names them per SoC and pin mux. Reboot and re-run `setup.sh` until
   every line says ok. `i2cdetect -y 4` should show 20, 21, 40 and 48.

5. **The link.** Plug USB-C 1 into the PC. Windows should find an RNDIS
   network adapter and a keyboard, and get 10.55.0.2 by DHCP; macOS the same
   over ECM. **Verify** macOS picks the ECM configuration on its own. Start
   the daemon on the PC (no `DECK_REQUIRE_HID=0` here: the real deck pairs
   every press). The LINK lamp lights when heartbeats arrive.

6. **Bench test** with Settings > hardware test, then Settings > calibrate
   meters, per docs/BUILD.md phase 3.

7. **Lock it down** once everything works: `sudo deploy/setup.sh --readonly`
   and reboot. The root filesystem is now a RAM overlay; `/var/deck` stays
   writable. To change the OS later: `sudo overlayroot-chroot`.

## Updating the code

From the repo root on the PC, deck plugged in:

```powershell
.\deploy\deploy.ps1          # code only
.\deploy\deploy.ps1 -Deps    # after requirements-deck.txt changes
```

The app and its venv live on `/var/deck`, so updates never need the root
filesystem writable.
