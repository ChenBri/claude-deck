/** Windows action backend: window focus and key send, via PowerShell (COM
 * WScript.Shell for AppActivate, SendKeys for keystrokes). No native addon,
 * so this is what "Win32 window focus and key send" means without a build
 * step: it's a thin shell, easy to see exactly what it does.
 *
 * TERMINAL_TITLE_HINT is a best-effort partial window-title match for
 * "whichever terminal has your Claude Code session." Set it to whatever
 * your terminal actually shows in its title bar (Windows Terminal, cmd,
 * the VS Code integrated terminal, ...).
 */
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { HostActions } from "./types";

const run = promisify(execFile);
const TERMINAL_TITLE_HINT = process.env.DECK_TERMINAL_TITLE_HINT ?? "claude";

async function powershell(script: string): Promise<void> {
  await run("powershell.exe", ["-NoProfile", "-NonInteractive", "-Command", script]);
}

function focusScript(): string {
  return `$sh = New-Object -ComObject WScript.Shell; [void]$sh.AppActivate('${TERMINAL_TITLE_HINT}'); Start-Sleep -Milliseconds 80;`;
}

async function sendKeys(keys: string): Promise<void> {
  await powershell(`${focusScript()} $sh.SendKeys('${keys}')`);
}

export const windowsActions: HostActions = {
  async approve() {
    await sendKeys("y~"); // ~ is Enter in SendKeys syntax
  },

  async deny() {
    await sendKeys("n~");
  },

  async interrupt() {
    await sendKeys("^c");
  },

  async focusOrLaunchClaude() {
    await powershell(focusScript());
  },

  async newSession() {
    // Best-effort: opens a new terminal tab, then starts Claude Code in it.
    // Tune to whatever launcher shortcut your terminal actually binds.
    await sendKeys("^+t");
  },

  async planMode() {
    await sendKeys("%p"); // Alt+P, wired to whatever launches plan mode locally
  },

  async effortSelect(level) {
    // Real Claude Code slash command (confirmed against the docs, not a
    // placeholder like planMode() above): /effort low|medium|high|xhigh|max,
    // typed mid-session. LOW/MEDIUM/HIGH/XHIGH/MAX map straight onto it.
    const argByLevel: Record<string, string> = {
      LOW: "low", MEDIUM: "medium", HIGH: "high", XHIGH: "xhigh", MAX: "max",
    };
    const arg = argByLevel[level];
    if (arg) await sendKeys(`/effort ${arg}~`);
  },

  async pushToTalk() {
    // Win+H (Windows dictation). SendKeys can't hit the Windows key, so this
    // goes through a tiny keybd_event P/Invoke instead.
    await powershell(`
      Add-Type -Namespace Deck -Name Keys -MemberDefinition '
        [DllImport("user32.dll")] public static extern void keybd_event(byte b, byte s, uint f, UIntPtr e);
      ';
      $VK_LWIN = 0x5B; $VK_H = 0x48; $KEYEVENTF_KEYUP = 0x2;
      [Deck.Keys]::keybd_event($VK_LWIN, 0, 0, [UIntPtr]::Zero);
      [Deck.Keys]::keybd_event($VK_H, 0, 0, [UIntPtr]::Zero);
      [Deck.Keys]::keybd_event($VK_H, 0, $KEYEVENTF_KEYUP, [UIntPtr]::Zero);
      [Deck.Keys]::keybd_event($VK_LWIN, 0, $KEYEVENTF_KEYUP, [UIntPtr]::Zero);
    `);
  },
};
