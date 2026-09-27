#!/bin/bash
# One-time provisioning of a Radxa ZERO 3W running Radxa's Debian CLI image.
# Run from a checkout of this repo on the deck, as root:
#
#   sudo deploy/setup.sh              everything, root stays writable
#   sudo deploy/setup.sh --readonly   then this, once it all works: read-only root
#
# Safe to re-run. It never partitions anything: /var/deck has to be an
# existing ext4 partition labelled DECKDATA (deploy/README.md step 2), and
# the script stops if it isn't there.
set -euo pipefail

REPO=$(cd "$(dirname "$0")/.." && pwd)
VAR=/var/deck
APP=$VAR/app
VENV=$VAR/venv
DECK_USER=deck
HW_GROUP=deckhw

say() { printf '\n== %s\n' "$*"; }
die() { printf 'setup: %s\n' "$*" >&2; exit 1; }

[ "$(id -u)" -eq 0 ] || die "run as root (sudo)"
[ "$(uname -m)" = aarch64 ] || die "this is for the deck (aarch64), not $(uname -m)"

if [ "${1:-}" = "--readonly" ]; then
    say "read-only root (overlayroot, tmpfs upper layer)"
    apt-get install -y overlayroot
    # recurse=0: only / gets the overlay; /var/deck stays a real, writable mount.
    sed -i 's/^overlayroot=.*/overlayroot="tmpfs:swap=0,recurse=0"/' /etc/overlayroot.conf
    grep -q '^overlayroot=' /etc/overlayroot.conf || echo 'overlayroot="tmpfs:swap=0,recurse=0"' >> /etc/overlayroot.conf
    echo "Reboot to apply. To change the root filesystem later: sudo overlayroot-chroot"
    exit 0
fi

say "data partition"
if ! grep -q 'LABEL=DECKDATA' /etc/fstab; then
    blkid -L DECKDATA > /dev/null || die "no partition labelled DECKDATA; create it first (deploy/README.md step 2)"
    mkdir -p "$VAR"
    # sync: settings and scores are written on change, and the card must survive a pulled plug
    echo "LABEL=DECKDATA $VAR ext4 defaults,noatime,sync 0 2" >> /etc/fstab
fi
mountpoint -q "$VAR" || mount "$VAR"

say "packages"
apt-get update
apt-get install -y --no-install-recommends \
    python3 python3-venv python3-dev build-essential \
    libsdl2-2.0-0 libsdl2-mixer-2.0-0 libsdl2-ttf-2.0-0 libsdl2-image-2.0-0 \
    fonts-dejavu-core i2c-tools gpiod alsa-utils rfkill rsync

say "user and hardware group"
getent group "$HW_GROUP" > /dev/null || groupadd --system "$HW_GROUP"
if ! id "$DECK_USER" > /dev/null 2>&1; then
    useradd --system --home-dir "$VAR" --no-create-home --shell /usr/sbin/nologin "$DECK_USER"
fi
usermod -aG "$HW_GROUP,video,render,audio,input" "$DECK_USER"
install -m 0644 "$REPO/deploy/udev/99-claude-deck.rules" /etc/udev/rules.d/
udevadm control --reload
udevadm trigger

# The encoder's long press powers the deck off; this is the one thing root does for it.
echo "$DECK_USER ALL=(root) NOPASSWD: /usr/bin/systemctl poweroff" > /etc/sudoers.d/claude-deck
chmod 0440 /etc/sudoers.d/claude-deck
visudo -cf /etc/sudoers.d/claude-deck

say "app and venv on $VAR"
mkdir -p "$APP"
rsync -a --delete --exclude '__pycache__' --exclude 'firmware/var' \
    "$REPO/firmware" "$REPO/deploy" "$APP/"
chmod +x "$APP/deploy/usb-gadget.sh"
[ -d "$VENV" ] || python3 -m venv "$VENV"
"$VENV/bin/pip" install --upgrade pip
"$VENV/bin/pip" install -r "$APP/firmware/requirements-deck.txt"
mkdir -p "$VAR/roms"
chown -R "$DECK_USER:$DECK_USER" "$VAR"

say "USB link"
install -m 0644 "$REPO/deploy/network/10-usb-link.network" /etc/systemd/network/
systemctl enable systemd-networkd

# SSH only on the USB link, keys only. Needs an authorized key for your
# login user before this runs, or the next SSH session is the last one.
mkdir -p /etc/ssh/sshd_config.d
cat > /etc/ssh/sshd_config.d/claude-deck.conf <<'EOF'
ListenAddress 10.55.0.1
PasswordAuthentication no
KbdInteractiveAuthentication no
PermitRootLogin no
EOF
# sshd starts before the gadget has an address; let it bind anyway.
echo 'net.ipv4.ip_nonlocal_bind = 1' > /etc/sysctl.d/90-claude-deck.conf

say "services"
# deck-radio-off: no route out (CLAUDE.md non-negotiable 4). WiFi goes off at
# the next boot and stays off, so finish anything that needs the network first.
for unit in deck-gadget.service deck.service deck-radio-off.service; do
    install -m 0644 "$REPO/deploy/systemd/$unit" /etc/systemd/system/
done
systemctl daemon-reload
systemctl enable deck-gadget.service deck.service deck-radio-off.service

# Logs to RAM: the root card should see no writes in normal running.
mkdir -p /etc/systemd/journald.conf.d
printf '[Journal]\nStorage=volatile\n' > /etc/systemd/journald.conf.d/claude-deck.conf

say "checks (anything MISSING needs an overlay: deploy/README.md step 4)"
check() { if [ -e "$1" ]; then echo "ok       $1 ($2)"; else echo "MISSING  $1 ($2)"; fi; }
check /dev/i2c-4 "I2C4: PCA9685, MCP23017 x2, ADS1115"
check /dev/spidev3.0 "SPI3: WS2812B strip"
check /dev/gpiochip3 "GPIO bank 3: buttons, mushroom, encoder"
if ls /sys/class/udc/* > /dev/null 2>&1; then echo "ok       USB device controller"; else echo "MISSING  USB device controller (OTG port not in peripheral mode)"; fi
aplay -l 2> /dev/null | grep -i -q 'max98357\|i2s' && echo "ok       I2S audio card" || echo "MISSING  I2S audio card (MAX98357A overlay)"
[ -e /dev/i2c-4 ] && i2cdetect -y 4 || true

say "done"
echo "Reboot. Then plug USB-C 1 into the PC: it should get 10.55.0.2, and the deck answers on 10.55.0.1."
echo "When everything works: sudo deploy/setup.sh --readonly"
