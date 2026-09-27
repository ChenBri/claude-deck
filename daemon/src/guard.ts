/** Approval verification rules: docs/SAFETY.md rule 2. A press carries a
 * request id, never a keystroke intent; this is the only place that turns
 * a verified id into a real action on the host. */

import { HostActions } from "./actions/types";
import { DenylistSettingsStore, isDenylistCategory } from "./denylist";
import { SessionRegistry } from "./sessions";
import { DailyStats } from "./stats";
import { AuditEntry, AuditLog } from "./store";

export interface ActionRequest {
  kind: string;
  session_id?: string;
  request_id?: string;
  name?: string;
  category?: string;
  value?: unknown;
}

// Shift+Tab presses needed to reach plan mode from a given permission_mode.
// Per code.claude.com/docs/en/permission-modes, the CLI cycle is
// default -> acceptEdits -> plan -> back to default, and from auto the
// first press always lands on default first. Modes outside the default
// cycle (dontAsk, bypassPermissions) have no fixed distance to plan, so
// they're deliberately absent: an unknown or uncyclable mode means "don't
// guess a keystroke," the same rule that governs the approve button.
const PLAN_MODE_STEPS: Record<string, number> = {
  auto: 3,
  default: 2,
  acceptEdits: 1,
  plan: 0,
};

export class Guard {
  constructor(
    private sessions: SessionRegistry,
    private actions: HostActions,
    private audit: AuditLog,
    private stats: DailyStats,
    private denylistStore: DenylistSettingsStore,
    private host: string,
  ) {}

  async handle(req: ActionRequest): Promise<void> {
    switch (req.kind) {
      case "approve":
        return this.handleApproval(req, true);
      case "deny":
        return this.handleApproval(req, false);
      case "panic":
        await this.actions.interrupt();
        this.audit.record(this.entry("panic", "", null, "approved", null));
        return;
      case "mech_key":
        return this.handleMechKey(req.name ?? "", req.session_id ?? "");
      case "toggle":
        if (req.name === "AUTO_ACCEPT" && req.session_id) {
          this.sessions.setAutoAccept(req.session_id, Boolean(req.value));
        }
        return;
      case "denylist_toggle":
        return this.handleDenylistToggle(req);
      case "effort_select":
        return this.handleEffortSelect(req);
      default:
        return;
    }
  }

  private async handleApproval(req: ActionRequest, approve: boolean): Promise<void> {
    const sessionId = req.session_id ?? "";
    const requestId = req.request_id ?? "";
    const session = this.sessions.get(sessionId);
    const kind = approve ? "approve" : "deny";

    if (!session?.pending || session.pending.requestId !== requestId) {
      // rule 4: any mismatch discards the press. Can't approve what you
      // haven't seen, because the deck can only act on the thing it's
      // currently displaying.
      this.audit.record(this.entry(kind, sessionId, requestId, "rejected", "no matching pending request"));
      return;
    }
    if (approve && !this.sessions.isPendingLive(sessionId, requestId)) {
      this.audit.record(this.entry("approve", sessionId, requestId, "rejected", "expired or denylisted"));
      return;
    }

    const { tool, target } = session.pending;
    await (approve ? this.actions.approve(sessionId) : this.actions.deny(sessionId));
    this.sessions.clearPending(sessionId);
    this.stats.recordApproval(approve);
    this.audit.record(this.entry(kind, sessionId, requestId, approve ? "approved" : "denied", null, tool, target));
  }

  /** Audit-log an action that never reached handle(), e.g. a press whose
   * HID key and HTTP action didn't pair up (link/pairing.ts). */
  reject(req: ActionRequest, reason: string): void {
    this.audit.record(this.entry(req.kind, req.session_id ?? "", req.request_id ?? null, "rejected", reason));
  }

  private handleDenylistToggle(req: ActionRequest): void {
    const category = req.category ?? "";
    if (!isDenylistCategory(category)) {
      this.audit.record(this.entry("denylist_toggle", "", null, "rejected", `unknown category ${category}`));
      return;
    }
    this.denylistStore.setCategory(category, Boolean(req.value));
    this.audit.record(
      this.entry("denylist_toggle", "", null, "approved", `${category}=${Boolean(req.value)}`),
    );
  }

  private async handleEffortSelect(req: ActionRequest): Promise<void> {
    const level = String(req.value ?? "");
    if (!["LOW", "MEDIUM", "HIGH", "XHIGH", "MAX"].includes(level)) {
      this.audit.record(this.entry("effort_select", "", null, "rejected", `unknown level ${level}`));
      return;
    }
    await this.actions.effortSelect(level);
    this.audit.record(this.entry("effort_select", "", null, "approved", level));
  }

  private async handleMechKey(name: string, sessionId: string): Promise<void> {
    switch (name) {
      case "CLD":
        return this.actions.focusOrLaunchClaude();
      case "NEW":
        return this.actions.newSession();
      case "PLAN":
        return this.handlePlanMode(sessionId);
      case "MIC":
        return this.actions.pushToTalk();
      default:
        return;
    }
  }

  private async handlePlanMode(sessionId: string): Promise<void> {
    const mode = this.sessions.get(sessionId)?.permissionMode ?? null;
    const presses = mode === null ? null : PLAN_MODE_STEPS[mode] ?? null;
    if (presses === null) {
      // rule 4's spirit applied to mode-cycling: no confirmed current mode
      // means no safe press count, so this is a no-op, not a guess.
      this.audit.record(this.entry("plan_mode", sessionId, null, "rejected", `no cyclable mode (last seen: ${mode ?? "none"})`));
      return;
    }
    if (presses > 0) await this.actions.planMode(presses);
    this.audit.record(this.entry("plan_mode", sessionId, null, "approved", `${presses} Shift+Tab from ${mode}`));
  }

  private entry(
    kind: string,
    sessionId: string,
    requestId: string | null,
    outcome: AuditEntry["outcome"],
    reason: string | null,
    tool: string | null = null,
    target: string | null = null,
  ): AuditEntry {
    return { ts: Date.now(), sessionId, requestId, kind, tool, target, host: this.host, outcome, reason };
  }
}
