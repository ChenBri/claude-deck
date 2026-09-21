import { test } from "node:test";
import assert from "node:assert/strict";

// Imported from dist, not src: guard.ts/sessions.ts use TypeScript
// constructor parameter properties, which Node's strip-only type
// stripping can't handle directly (it needs real transformation, not
// just type removal) - see package.json's pretest, which builds first.
import { Guard } from "../dist/guard.js";
import { SessionRegistry } from "../dist/sessions.js";
import { DailyStats } from "../dist/stats.js";
import { DenylistSettingsStore } from "../dist/denylist.js";
import type { HostActions } from "../src/actions/types.ts";
import type { AuditLog } from "../src/store.ts";

function makeGuard(actions: Partial<HostActions>) {
  const noopActions: HostActions = {
    approve: async () => {},
    deny: async () => {},
    interrupt: async () => {},
    focusOrLaunchClaude: async () => {},
    newSession: async () => {},
    planMode: async () => {},
    pushToTalk: async () => {},
    effortSelect: async () => {},
    ...actions,
  };
  const noopAudit = { record: () => {}, close: () => {} } as unknown as AuditLog;
  return new Guard(new SessionRegistry(), noopActions, noopAudit, new DailyStats(), new DenylistSettingsStore(), "test-host");
}

test("effort_select dispatches a known level to the host action", async () => {
  const calls: string[] = [];
  const guard = makeGuard({ effortSelect: async (level: string) => void calls.push(level) });
  await guard.handle({ kind: "effort_select", value: "HIGH" });
  assert.deepEqual(calls, ["HIGH"]);
});

test("effort_select ignores an unknown level rather than passing it through", async () => {
  const calls: string[] = [];
  const guard = makeGuard({ effortSelect: async (level: string) => void calls.push(level) });
  await guard.handle({ kind: "effort_select", value: "BOGUS" });
  assert.deepEqual(calls, []);
});

test("effort_select accepts all five real /effort levels", async () => {
  const calls: string[] = [];
  const guard = makeGuard({ effortSelect: async (level: string) => void calls.push(level) });
  for (const level of ["LOW", "MEDIUM", "HIGH", "XHIGH", "MAX"]) {
    await guard.handle({ kind: "effort_select", value: level });
  }
  assert.deepEqual(calls, ["LOW", "MEDIUM", "HIGH", "XHIGH", "MAX"]);
});
