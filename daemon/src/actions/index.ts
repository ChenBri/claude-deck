/** Full action set on Windows and on macOS alike (docs/SAFETY.md rule 5):
 * the denylist is what protects production access, not a per-machine
 * profile, so both hosts get approve, deny, interrupt, mech keys, push to talk. */

export type { HostActions } from "./types";
import { HostActions } from "./types";
import { windowsActions } from "./windows";
import { macosActions } from "./macos";

export function loadHostActions(): HostActions {
  if (process.platform === "win32") return windowsActions;
  if (process.platform === "darwin") return macosActions;
  throw new Error(`unsupported host platform ${process.platform}; claude-deck targets Windows and macOS`);
}
