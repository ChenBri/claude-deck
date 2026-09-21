/** macOS action backend: AppleScript + Accessibility, per docs/ARCHITECTURE.md.
 * Needs Accessibility permission granted once to the process running the
 * daemon (System Settings > Privacy & Security > Accessibility).
 *
 * TERMINAL_APP_HINT names the application to activate before sending keys;
 * set it to whatever actually runs your Claude Code session (Terminal,
 * iTerm2, the VS Code integrated terminal's host app, ...).
 */
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { HostActions } from "./types";

const run = promisify(execFile);
const TERMINAL_APP_HINT = process.env.DECK_TERMINAL_APP_HINT ?? "Terminal";
const DICTATION_SHORTCUT = process.env.DECK_DICTATION_SHORTCUT ?? "using {command down, function down}"; // Fn+Cmd is one common binding

async function osascript(script: string): Promise<void> {
  await run("osascript", ["-e", script]);
}

function activateApp(): string {
  return `tell application "${TERMINAL_APP_HINT}" to activate`;
}

async function keystroke(key: string, modifiers = ""): Promise<void> {
  const usingClause = modifiers ? ` using {${modifiers}}` : "";
  await osascript(`
    ${activateApp()}
    delay 0.08
    tell application "System Events" to keystroke "${key}"${usingClause}
  `);
}

export const macosActions: HostActions = {
  async approve() {
    await keystroke("y");
    await osascript(`tell application "System Events" to key code 36`); // Enter
  },

  async deny() {
    await keystroke("n");
    await osascript(`tell application "System Events" to key code 36`);
  },

  async interrupt() {
    await keystroke("c", "control down");
  },

  async focusOrLaunchClaude() {
    await osascript(activateApp());
  },

  async newSession() {
    await keystroke("t", "command down"); // new tab, then `claude` still has to be typed/aliased
  },

  async planMode() {
    await keystroke("p", "option down");
  },

  async effortSelect(level) {
    // Option+1..4, same "placeholder, tune it locally" status as planMode()
    // above - there's no confirmed way yet to change Claude Code's
    // reasoning effort from an external keystroke.
    const digitByLevel: Record<string, string> = { LOW: "1", MED: "2", HIGH: "3", MAX: "4" };
    const digit = digitByLevel[level];
    if (digit) await keystroke(digit, "option down");
  },

  async pushToTalk() {
    await osascript(`
      ${activateApp()}
      delay 0.08
      tell application "System Events" to key code 4 ${DICTATION_SHORTCUT}
    `); // key code 4 is "h"
  },
};
