import { test, mock, beforeEach, afterEach } from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";

// From dist for the same reason as guard.test.ts: parameter properties.
import { HidPairing, PAIR_WINDOW_MS, keyFor } from "../dist/link/pairing.js";
import { parseHelperLine, registerHotkeys } from "../dist/link/hotkeys.js";

type Req = { kind: string; name?: string; value?: unknown; request_id?: string };

let ran: Req[];
let rejected: string[];
let clock: number;

function pairing(requireHid = true) {
  return new HidPairing(
    requireHid,
    (req: Req) => void ran.push(req),
    (_req: Req, reason: string) => void rejected.push(reason),
    () => clock,
  );
}

beforeEach(() => {
  ran = [];
  rejected = [];
  clock = 0;
  mock.timers.enable({ apis: ["setTimeout"] });
});

afterEach(() => {
  mock.timers.reset();
});

test("approve runs only once its key arrives, in either order", () => {
  const p = pairing();
  p.onAction({ kind: "approve", request_id: "r1" });
  assert.deepEqual(ran, []);
  p.onKey("APPROVE");
  assert.deepEqual(ran.map((r) => r.request_id), ["r1"]);

  p.onKey("APPROVE");
  assert.equal(ran.length, 1);
  p.onAction({ kind: "approve", request_id: "r2" });
  assert.deepEqual(ran.map((r) => r.request_id), ["r1", "r2"]);
});

test("an approve with no key is dropped and audited after the window", () => {
  const p = pairing();
  p.onAction({ kind: "approve", request_id: "r1" });
  mock.timers.tick(PAIR_WINDOW_MS);
  p.onKey("APPROVE"); // too late: must not resurrect the expired action
  assert.deepEqual(ran, []);
  assert.equal(rejected.length, 1);
  assert.match(rejected[0], /no APPROVE key/);
});

test("a key only pairs with its own action", () => {
  const p = pairing();
  p.onAction({ kind: "approve", request_id: "r1" });
  p.onKey("DENY");
  assert.deepEqual(ran, []);
  p.onAction({ kind: "deny", request_id: "r2" });
  assert.deepEqual(ran.map((r) => r.kind), ["deny"]);
});

test("one key consumes one action", () => {
  const p = pairing();
  p.onAction({ kind: "mech_key", name: "NEW" });
  p.onAction({ kind: "mech_key", name: "NEW" });
  p.onKey("NEW");
  assert.equal(ran.length, 1);
});

test("panic runs on either half alone and the other half is a duplicate", () => {
  const p = pairing();
  p.onKey("PANIC");
  assert.equal(ran.length, 1);
  clock += 100;
  p.onAction({ kind: "panic", value: true });
  assert.equal(ran.length, 1);
  clock += PAIR_WINDOW_MS;
  p.onAction({ kind: "panic", value: true });
  assert.equal(ran.length, 2);
});

test("panic release and keyless actions pass straight through", () => {
  const p = pairing();
  p.onAction({ kind: "panic", value: false });
  p.onAction({ kind: "effort_select", value: "HIGH" });
  p.onAction({ kind: "toggle", name: "AUTO_ACCEPT", value: true });
  assert.deepEqual(ran.map((r) => r.kind), ["panic", "effort_select", "toggle"]);
});

test("DECK_REQUIRE_HID=0 runs actions unpaired and ignores keys", () => {
  const p = pairing(false);
  p.onAction({ kind: "approve", request_id: "r1" });
  p.onKey("APPROVE");
  assert.deepEqual(ran.map((r) => r.request_id), ["r1"]);
});

test("keyFor covers exactly the actions that type into a window", () => {
  assert.equal(keyFor({ kind: "approve" }), "APPROVE");
  assert.equal(keyFor({ kind: "mech_key", name: "PLAN" }), "PLAN");
  assert.equal(keyFor({ kind: "mech_key", name: "BOGUS" }), null);
  assert.equal(keyFor({ kind: "denylist_toggle" }), null);
});

test("helper lines parse to hotkeys and nothing else", () => {
  assert.equal(parseHelperLine("KEY F13"), "APPROVE");
  assert.equal(parseHelperLine("KEY F19\r"), "MIC");
  assert.equal(parseHelperLine("KEY F20"), null); // spare
  assert.equal(parseHelperLine("READY F13"), null);
  assert.equal(parseHelperLine("KEY F1"), null);
});

test("windows helper: a real F13 press reaches the callback", { skip: process.platform !== "win32" }, async () => {
  mock.timers.reset(); // real time for a real process
  const seen: string[] = [];
  const listener = registerHotkeys((name: string) => void seen.push(name));
  try {
    await new Promise((r) => setTimeout(r, 2500)); // PowerShell + Add-Type start-up
    const press = `
      Add-Type -Name K -Namespace T -MemberDefinition '[DllImport("user32.dll")] public static extern void keybd_event(byte b, byte s, uint f, System.UIntPtr e);'
      [T.K]::keybd_event(0x7C, 0, 0, [System.UIntPtr]::Zero)
      [T.K]::keybd_event(0x7C, 0, 2, [System.UIntPtr]::Zero)`;
    spawnSync("powershell.exe", ["-NoProfile", "-NonInteractive", "-Command", press]);
    for (let i = 0; i < 20 && seen.length === 0; i++) await new Promise((r) => setTimeout(r, 100));
    assert.deepEqual(seen, ["APPROVE"]);
  } finally {
    listener.stop();
  }
});
