/** Server-side mirror of what's currently pending per session: the daemon
 * originates every classified event, so it already knows "what the deck
 * currently has on screen" without needing the deck to echo it back. */

import { ClassifiedEvent } from "./classify";

const APPROVAL_EXPIRY_MS = 90_000;

export interface PendingRequest {
  requestId: string;
  tool: string;
  target: string;
  approvable: boolean;
  denylistCategory: string | null;
  createdAt: number;
}

export interface SessionRecord {
  sessionId: string;
  pending: PendingRequest | null;
  lastSeen: number;
  autoAccept: boolean;
  // Last permission_mode seen on any hook event for this session, e.g.
  // "default" | "acceptEdits" | "plan" | "auto". Null until the first hook
  // event that carries it arrives. Drives guard.ts's plan-mode Shift+Tab count.
  permissionMode: string | null;
}

export class SessionRegistry {
  private sessions = new Map<string, SessionRecord>();

  private getOrCreate(sessionId: string): SessionRecord {
    let session = this.sessions.get(sessionId);
    if (!session) {
      session = { sessionId, pending: null, lastSeen: Date.now(), autoAccept: false, permissionMode: null };
      this.sessions.set(sessionId, session);
    }
    return session;
  }

  applyClassified(evt: ClassifiedEvent): SessionRecord {
    const session = this.getOrCreate(evt.sessionId);
    session.lastSeen = Date.now();

    if (typeof evt.meta.permission_mode === "string") {
      session.permissionMode = evt.meta.permission_mode;
    }

    if (evt.event === "Notification" && evt.meta.variant === "permission") {
      session.pending = {
        requestId: String(evt.meta.request_id),
        tool: String(evt.meta.tool ?? ""),
        target: String(evt.meta.target ?? ""),
        approvable: Boolean(evt.meta.approvable),
        denylistCategory: (evt.meta.denylist_category as string | null) ?? null,
        createdAt: Date.now(),
      };
    } else if (evt.event === "Stop" || evt.event === "SessionStart") {
      session.pending = null;
    }
    return session;
  }

  get(sessionId: string): SessionRecord | undefined {
    return this.sessions.get(sessionId);
  }

  setAutoAccept(sessionId: string, value: boolean): void {
    this.getOrCreate(sessionId).autoAccept = value;
  }

  isPendingLive(sessionId: string, requestId: string, now = Date.now()): boolean {
    const session = this.sessions.get(sessionId);
    if (!session?.pending) return false;
    return (
      session.pending.requestId === requestId &&
      session.pending.approvable &&
      now - session.pending.createdAt < APPROVAL_EXPIRY_MS
    );
  }

  hasPending(sessionId: string, requestId: string): boolean {
    return this.sessions.get(sessionId)?.pending?.requestId === requestId;
  }

  clearPending(sessionId: string): void {
    const session = this.sessions.get(sessionId);
    if (session) session.pending = null;
  }

  prune(maxAgeMs: number, now = Date.now()): void {
    for (const [id, session] of this.sessions) {
      if (now - session.lastSeen > maxAgeMs) this.sessions.delete(id);
    }
  }
}
