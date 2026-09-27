/** Bootstrap: host detection for the action backend, then wire hook ingest,
 * the deck link (both directions), and the audit log together. */

import os from "node:os";
import { loadHostActions } from "./actions";
import { DenylistSettingsStore } from "./denylist";
import { startHookIngest } from "./http";
import { registerHotkeys } from "./link/hotkeys";
import { HidPairing } from "./link/pairing";
import { sendHeartbeat, sendIdleInfo, startActionListener } from "./link/transport";
import { Guard } from "./guard";
import { SessionRegistry } from "./sessions";
import { DailyStats } from "./stats";
import { AuditLog } from "./store";
import { getGitStatus } from "./enrich/git";
import { getWeather } from "./enrich/weather";
import { scanUsage } from "./enrich/usage";

const IDLE_INFO_INTERVAL_MS = 20_000;
// Must stay well under firmware/deck/link.py's HEARTBEAT_TIMEOUT (5s), or
// the deck flags OFFLINE in the gap between heartbeats even with a live daemon.
const HEARTBEAT_INTERVAL_MS = 2_000;
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
  // Real deck: every press needs its F13-F20 key and its HTTP action to agree
  // (link/pairing.ts). DECK_REQUIRE_HID=0 is only for the desktop simulator,
  // which has no HID gadget to send keys with.
  const requireHid = process.env.DECK_REQUIRE_HID !== "0";
  if (!requireHid) console.warn("DECK_REQUIRE_HID=0: deck actions run without their HID key. Simulator only.");
  const pairing = new HidPairing(
    requireHid,
    (req) => void guard.handle(req).catch((err) => console.error("guard:", err)),
    (req, reason) => guard.reject(req, reason),
  );
  startActionListener((req) => pairing.onAction(req));
  const hotkeys = registerHotkeys((name) => pairing.onKey(name));

  setInterval(() => sessions.prune(SESSION_MAX_AGE_MS), SESSION_PRUNE_INTERVAL_MS);

  sendHeartbeat(); // don't wait a full interval for the link to come up
  setInterval(sendHeartbeat, HEARTBEAT_INTERVAL_MS);

  const userName = process.env.DECK_USER_NAME ?? process.env.USER ?? process.env.USERNAME ?? "";
  setInterval(async () => {
    const now = new Date();
    const usage = scanUsage(now.getTime());
    sendIdleInfo({
      clock: now.toTimeString().slice(0, 5),
      // local date, not toISOString(): that's UTC and reads as yesterday for the first hours after midnight east of Greenwich
      date: `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`,
      name: userName,
      weather: await getWeather(),
      git: await getGitStatus(lastCwd),
      totals: stats.summary(),
      five_hour_pct: usage.fiveHourPct,
      five_hour_series: usage.fiveHourSeries,
      today: { ...stats.counts(), output_tokens: usage.todayOutputTokens, turns: usage.todayTurns },
    });
  }, IDLE_INFO_INTERVAL_MS);

  console.log(`claude-deck daemon running on ${host} (${process.platform}), hook ingest on 127.0.0.1:7327`);

  process.on("SIGINT", () => {
    hotkeys.stop();
    audit.close();
    process.exit(0);
  });
}

main().catch((err) => {
  console.error("daemon failed to start:", err);
  process.exit(1);
});
