/** F13-F20 global hotkeys (docs/SAFETY.md rule 1): the physical half of
 * every deck press. A small per-OS helper process registers the keys
 * system-wide and prints a line per press; this module runs it, parses its
 * output and restarts it if it dies. Keys only prove a press happened -
 * link/pairing.ts matches each one with the HTTP action that names what
 * it's for before anything runs.
 *
 * Windows: helpers/win-hotkeys.ps1 (RegisterHotKey). Tested.
 * macOS: helpers/mac-hotkeys.swift (Carbon RegisterEventHotKey). Untested.
 */

import { spawn, type ChildProcess } from "node:child_process";
import { existsSync } from "node:fs";
import { join } from "node:path";
import { createInterface } from "node:readline";

export type HotkeyName = "APPROVE" | "DENY" | "PANIC" | "CLD" | "NEW" | "PLAN" | "MIC";

// Must match firmware/deck/hid.py HOTKEYS (a firmware test checks this).
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

const BY_KEY = new Map(Object.entries(HOTKEY_MAP).map(([name, key]) => [key, name as HotkeyName]));
const RESTART_DELAY_MS = 2000;

// dist/link/hotkeys.js -> daemon/helpers
const HELPERS_DIR = join(__dirname, "..", "..", "helpers");

/** A helper output line -> the hotkey it reports, or null for anything else. */
export function parseHelperLine(line: string): HotkeyName | null {
  const match = /^KEY (F\d+)$/.exec(line.trim());
  return match ? BY_KEY.get(match[1]) ?? null : null;
}

function helperCommand(): [string, string[]] | null {
  if (process.platform === "win32") {
    return [
      "powershell.exe",
      ["-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", join(HELPERS_DIR, "win-hotkeys.ps1")],
    ];
  }
  if (process.platform === "darwin") {
    const built = join(HELPERS_DIR, "mac-hotkeys");
    return existsSync(built) ? [built, []] : ["swift", [join(HELPERS_DIR, "mac-hotkeys.swift")]];
  }
  return null;
}

export interface HotkeyListener {
  stop(): void;
}

export function registerHotkeys(onHotkey: (name: HotkeyName) => void): HotkeyListener {
  const command = helperCommand();
  if (command === null) {
    console.warn(`hotkeys: no helper for ${process.platform}; deck presses can't be paired and won't act.`);
    return { stop: () => {} };
  }

  let child: ChildProcess | null = null;
  let stopped = false;

  const start = () => {
    const [cmd, args] = command;
    child = spawn(cmd, args, { stdio: ["ignore", "pipe", "pipe"], windowsHide: true });
    createInterface({ input: child.stdout! }).on("line", (line) => {
      const name = parseHelperLine(line);
      if (name !== null) onHotkey(name);
      else if (line.startsWith("FAILED")) console.error(`hotkeys: ${line} (another app may already own it)`);
    });
    child.stderr!.on("data", (d) => console.error(`hotkeys helper: ${String(d).trim()}`));
    child.on("exit", (code) => {
      if (stopped) return;
      console.error(`hotkeys: helper exited (${code}), restarting in ${RESTART_DELAY_MS}ms`);
      setTimeout(start, RESTART_DELAY_MS).unref();
    });
    child.on("error", (err) => console.error("hotkeys: helper failed to start:", err.message));
  };
  start();

  return {
    stop: () => {
      stopped = true;
      child?.kill();
    },
  };
}
