/** Bootstrap: host detection for the action backend, then wire hook ingest,
 * the Pi link (both directions), and the audit log together. */

import os from "node:os";
import { loadHostActions } from "./actions";
import { DenylistSettingsStore } from "./denylist";
import { startHookIngest } from "./http";
import { registerHotkeys } from "./link/hotkeys";
import { sendIdleInfo, startActionListener } from "./link/transport";
import { Guard } from "./guard";
import { SessionRegistry } from "./sessions";
import { DailyStats } from "./stats";
import { AuditLog } from "./store";
import { getGitStatus } from "./enrich/git";
import { getWeather } from "./enrich/weather";

const IDLE_INFO_INTERVAL_MS = 20_000;
const SESSION_PRUNE_INTERVAL_MS = 60_000;
const SESSION_MAX_AGE_MS = 6 * 60 * 60 * 1000;

async function main(): Promise<void> {
  const host = os.hostname();
  const actions = loadHostActions();
  const sessions = new SessionRegistry();
  const stats = new DailyStats();
  const audit = new AuditLog();
  const denylistStore = new DenylistSettingsStore();
  const guard = new Guard(sessions, actions, audit, stats, denylistStore, host);

  let lastCwd: string | null = null;

  startHookIngest({
    sessions,
    stats,
    denylistStore,
    onCwdSeen: (cwd) => {
      lastCwd = cwd;
    },
  });
  startActionListener(guard);
  registerHotkeys((name) => {
    // Placeholder wiring for when a real HID device exists; see link/hotkeys.ts.
    void guard.handle({ kind: name.toLowerCase() });
  });

  setInterval(() => sessions.prune(SESSION_MAX_AGE_MS), SESSION_PRUNE_INTERVAL_MS);

  const userName = process.env.DECK_USER_NAME ?? process.env.USER ?? process.env.USERNAME ?? "";
  setInterval(async () => {
    const now = new Date();
    sendIdleInfo({
      clock: now.toTimeString().slice(0, 5),
      date: now.toISOString().slice(0, 10),
      name: userName,
      weather: await getWeather(),
      git: await getGitStatus(lastCwd),
      totals: stats.summary(),
    });
  }, IDLE_INFO_INTERVAL_MS);

  console.log(`claude-deck daemon running on ${host} (${process.platform}), hook ingest on 127.0.0.1:7327`);

  process.on("SIGINT", () => {
    audit.close();
    process.exit(0);
  });
}

main().catch((err) => {
  console.error("daemon failed to start:", err);
  process.exit(1);
});
