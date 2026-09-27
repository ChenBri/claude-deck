#!/bin/bash
# Composite USB gadget on the Radxa's USB-C 1 (OTG) port, via configfs.
# Run at boot by deck-gadget.service, before the firmware starts.
#
#   config 1: RNDIS + HID   Windows binds this one, steered by the MS OS descriptor
#   config 2: ECM + HID     macOS and Linux
#
# Network: a point-to-point link, 10.55.0.1 here and 10.55.0.2 on the host,
# handed out by systemd-networkd (network/10-usb-link.network).
#
# HID: a keyboard whose report descriptor declares only the usages F13 to F20
# (0x68-0x6F). Any other keycode is outside the declared range, so the host
# discards it: docs/SAFETY.md rule 1 enforced by USB itself, on top of
# firmware/deck/hid.py refusing to send one. Report layout matches hid.py:
# 2 unused bytes, then 6 key slots.
#
# Idempotent: exits quietly if the gadget already exists.
# Verify on first boot: the OTG port has to be in peripheral mode for a UDC to
# show up in /sys/class/udc (see deploy/README.md).
set -euo pipefail

GADGET=/sys/kernel/config/usb_gadget/deck

# Locally administered, fixed MACs: the host remembers the adapter across plugs.
DEV_MAC_RNDIS=02:de:ec:00:00:01
HOST_MAC_RNDIS=02:de:ec:00:00:02
DEV_MAC_ECM=02:de:ec:00:00:03
HOST_MAC_ECM=02:de:ec:00:00:04

HID_REPORT_DESC='\x05\x01\x09\x06\xa1\x01\x75\x08\x95\x02\x81\x01\x05\x07\x19\x68\x29\x6f\x15\x68\x25\x6f\x75\x08\x95\x06\x81\x00\xc0'
#  05 01   Usage Page (Generic Desktop)     09 06  Usage (Keyboard)
#  a1 01   Collection (Application)
#  75 08 95 02 81 01                        2 constant bytes (padding)
#  05 07   Usage Page (Keyboard/Keypad)
#  19 68 29 6f                              Usage Min F13 .. Max F20
#  15 68 25 6f                              Logical Min 0x68 .. Max 0x6F
#  75 08 95 06 81 00                        6 key slots, data array
#  c0      End Collection

modprobe libcomposite
mountpoint -q /sys/kernel/config || mount -t configfs none /sys/kernel/config

if [ -e "$GADGET/UDC" ] && [ -n "$(cat "$GADGET/UDC")" ]; then
    exit 0
fi

mkdir -p "$GADGET"
cd "$GADGET"

echo 0x1d6b > idVendor   # Linux Foundation
echo 0x0104 > idProduct  # Multifunction Composite Gadget
echo 0x0100 > bcdDevice
echo 0x0200 > bcdUSB
# Composite with an IAD, which Windows needs to bind RNDIS inside a composite device
echo 0xEF > bDeviceClass
echo 0x02 > bDeviceSubClass
echo 0x01 > bDeviceProtocol

serial=$(tr -d '\0' < /proc/device-tree/serial-number 2>/dev/null || cat /etc/machine-id)
mkdir -p strings/0x409
echo "$serial" > strings/0x409/serialnumber
echo "claude-deck" > strings/0x409/manufacturer
echo "claude-deck" > strings/0x409/product

# MS OS descriptor: tells Windows to load its RNDIS driver without an .inf
echo 1 > os_desc/use
echo 0xcd > os_desc/b_vendor_code
echo MSFT100 > os_desc/qw_sign

mkdir -p functions/rndis.usb0
echo "$DEV_MAC_RNDIS" > functions/rndis.usb0/dev_addr
echo "$HOST_MAC_RNDIS" > functions/rndis.usb0/host_addr
echo RNDIS > functions/rndis.usb0/os_desc/interface.rndis/compatible_id
echo 5162001 > functions/rndis.usb0/os_desc/interface.rndis/sub_compatible_id

mkdir -p functions/ecm.usb0
echo "$DEV_MAC_ECM" > functions/ecm.usb0/dev_addr
echo "$HOST_MAC_ECM" > functions/ecm.usb0/host_addr

mkdir -p functions/hid.usb0
echo 0 > functions/hid.usb0/protocol   # not a boot keyboard: the descriptor is deliberately non-standard
echo 0 > functions/hid.usb0/subclass
echo 8 > functions/hid.usb0/report_length
printf '%b' "$HID_REPORT_DESC" > functions/hid.usb0/report_desc

for c in 1 2; do
    mkdir -p "configs/c.$c/strings/0x409"
    echo 0xC0 > "configs/c.$c/bmAttributes"  # self-powered: power comes from the GPIO header, never this port
    echo 2 > "configs/c.$c/MaxPower"
done
echo "RNDIS + HID" > configs/c.1/strings/0x409/configuration
echo "ECM + HID" > configs/c.2/strings/0x409/configuration

# network function first in each config
ln -s functions/rndis.usb0 configs/c.1/
ln -s functions/hid.usb0 configs/c.1/
ln -s functions/ecm.usb0 configs/c.2/
ln -s functions/hid.usb0 configs/c.2/
ln -s configs/c.1 os_desc/

udc=""
for path in /sys/class/udc/*; do
    [ -e "$path" ] && udc=$(basename "$path") && break
done
if [ -z "$udc" ]; then
    echo "usb-gadget: no USB device controller found; is the OTG port in peripheral mode?" >&2
    exit 1
fi
echo "$udc" > UDC
