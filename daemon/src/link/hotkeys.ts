/** F13-F20 global hotkey registration (docs/SAFETY.md rule 1): the real
 * trigger for APPROVE/DENY/PANIC/mech-keys once the Pi's USB HID gadget
 * exists. No hardware has arrived yet (docs/BUILD.md phase 0), and Node has
 * no built-in global hotkey API, so this is a stub for whichever native
 * listener gets chosen (e.g. a keyboard-hook addon) once there's a real HID
 * device to test it against.
 *
 * Until then, the simulator's button presses reach guard.ts through
 * link/transport.ts's /action endpoint instead (see firmware/deck/main.py's
 * _on_button comment) - functionally equivalent, just not through a real
 * OS-level hotkey.
 */

export type HotkeyName = "APPROVE" | "DENY" | "PANIC" | "CLD" | "NEW" | "PLAN" | "MIC";

// F13 .. F20, in the order docs/HARDWARE.md's pin map implies: the three
// real-GPIO buttons first, then the MCP23017 mech keys.
export const HOTKEY_MAP: Record<HotkeyName, string> = {
  APPROVE: "F13",
  DENY: "F14",
  PANIC: "F15",
  CLD: "F16",
  NEW: "F17",
  PLAN: "F18",
  MIC: "F19",
  // F20 spare
};

export function registerHotkeys(_onHotkey: (name: HotkeyName) => void): void {
  console.warn(
    "hotkeys.ts: no HID hardware yet, global F13-F20 hotkeys are not registered. " +
      "Button presses arrive via the simulator's /action HTTP path instead.",
  );
}
