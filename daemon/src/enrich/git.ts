/** Git status of the last repo, for the idle dashboard. "Last repo" is
 * whichever directory the most recent hook fired from. */

import { execFile } from "node:child_process";
import { promisify } from "node:util";

const run = promisify(execFile);

export async function getGitStatus(cwd: string | null): Promise<string | null> {
  if (!cwd) return null;
  try {
    const { stdout } = await run("git", ["-C", cwd, "status", "--short", "--branch"], { timeout: 2000 });
    const lines = stdout.split("\n").filter(Boolean);
    if (lines.length === 0) return null;
    const branchLine = lines[0].replace(/^## /, "");
    const dirty = lines.length - 1;
    return dirty > 0 ? `${branchLine}, ${dirty} changed` : `${branchLine}, clean`;
  } catch {
    return null; // not a git repo, git not on PATH, etc: the dashboard just omits it
  }
}
