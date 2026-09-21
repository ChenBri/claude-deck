# ROMs

Empty on purpose. Drop your own `.gb` / `.gbc` dumps here, made from
cartridges you own. Nothing in this folder except this file and
`.gitignore` is ever committed: this repo is public, and Game Boy game
data is copyrighted regardless of whether you own the cartridge it came
from.

The Game Boy app (`deck/ui/scenes/gameboy.py`) scans this folder on
launch and lists whatever it finds. Point it elsewhere with the
`DECK_ROMS_DIR` environment variable if you'd rather keep ROMs outside
the repo entirely.

Save states land in `${DECK_VAR}/gb_saves/` (already covered by the
existing `firmware/var/` gitignore rule), one per ROM, loaded
automatically the next time you pick that game.

On real hardware, the plan is to also expose this folder as a USB mass
storage drive so you can drag files onto it from the PC the deck is
plugged into, no SD card swap needed. See DECISIONS.md and
docs/HARDWARE.md for the design and its current status.
