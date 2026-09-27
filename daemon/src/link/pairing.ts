/** Pairs each HID key from the deck with the HTTP action that names what
 * it's for (docs/SAFETY.md rules 1 and 2). The key proves a physical press
 * on the real device; the action carries the session and request id. An
 * action that makes the daemon type into a window (approve, deny, the mech
 * keys) runs only when both arrive within PAIR_WINDOW_MS of each other, in
 * either order. One key consumes one action.
 *
 * PANIC is the exception: it runs on whichever half arrives first and the
 * other half is swallowed as its duplicate. It's the stop button, so it must
 * never fail for want of a pairing, and a spoofed panic can only interrupt.
 *
 * Everything else (toggles, the effort dial, denylist toggles, the panic
 * release) has no key and passes straight through, as before.
 *
 * requireHid = false (DECK_REQUIRE_HID=0) is for the desktop simulator,
 * which has no HID gadget: actions pass through unpaired. */

import type { ActionRequest } from "../guard";
import type { HotkeyName } from "./hotkeys";

export const PAIR_WINDOW_MS = 1000;

export type Execute = (req: ActionRequest) => void;
export type Reject = (req: ActionRequest, reason: string) => void;

/** The key an action must be paired with, or null if it needs none. */
export function keyFor(req: ActionRequest): HotkeyName | null {
  switch (req.kind) {
    case "approve":
      return "APPROVE";
    case "deny":
      return "DENY";
    case "panic":
      return req.value === false ? null : "PANIC";
    case "mech_key":
      return ["CLD", "NEW", "PLAN", "MIC"].includes(req.name ?? "") ? (req.name as HotkeyName) : null;
    default:
      return null;
  }
}

interface Waiting {
  req: ActionRequest;
  timer: ReturnType<typeof setTimeout>;
}

export class HidPairing {
  private waitingActions = new Map<HotkeyName, Waiting[]>();
  private waitingKeys = new Map<HotkeyName, ReturnType<typeof setTimeout>[]>();
  private lastPanicAt = -Infinity;

  constructor(
    private requireHid: boolean,
    private execute: Execute,
    private reject: Reject,
    private now: () => number = Date.now,
  ) {}

  onAction(req: ActionRequest): void {
    const key = keyFor(req);
    if (key === null) {
      this.execute(req);
      return;
    }
    if (key === "PANIC") {
      this.panic(req);
      return;
    }
    if (!this.requireHid) {
      this.execute(req);
      return;
    }
    const keys = this.waitingKeys.get(key);
    if (keys && keys.length > 0) {
      clearTimeout(keys.shift()!);
      this.execute(req);
      return;
    }
    const timer = setTimeout(() => this.expireAction(key, req), PAIR_WINDOW_MS);
    timer.unref?.();
    this.push(this.waitingActions, key, { req, timer });
  }

  onKey(key: HotkeyName): void {
    if (key === "PANIC") {
      this.panic({ kind: "panic", value: true });
      return;
    }
    if (!this.requireHid) return; // the simulator path doesn't use keys at all
    const actions = this.waitingActions.get(key);
    if (actions && actions.length > 0) {
      const { req, timer } = actions.shift()!;
      clearTimeout(timer);
      this.execute(req);
      return;
    }
    const timer = setTimeout(() => this.expireKey(key), PAIR_WINDOW_MS);
    timer.unref?.();
    this.push(this.waitingKeys, key, timer);
  }

  private panic(req: ActionRequest): void {
    const t = this.now();
    if (t - this.lastPanicAt < PAIR_WINDOW_MS) return; // the other half of the same press
    this.lastPanicAt = t;
    this.execute(req);
  }

  private expireAction(key: HotkeyName, req: ActionRequest): void {
    const list = this.waitingActions.get(key) ?? [];
    const i = list.findIndex((w) => w.req === req);
    if (i < 0) return;
    list.splice(i, 1);
    this.reject(req, `no ${key} key from the deck within ${PAIR_WINDOW_MS}ms`);
  }

  private expireKey(key: HotkeyName): void {
    const list = this.waitingKeys.get(key) ?? [];
    list.shift();
    // A key with no action: nothing to run and nothing to name in the audit
    // log, but worth knowing about if it happens often.
    this.reject({ kind: key.toLowerCase() }, `${key} key with no matching action within ${PAIR_WINDOW_MS}ms`);
  }

  private push<T>(map: Map<HotkeyName, T[]>, key: HotkeyName, item: T): void {
    const list = map.get(key) ?? [];
    list.push(item);
    map.set(key, list);
  }
}
