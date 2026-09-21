/** Server-side mirror of what's currently pending per session: the daemon
 * originates every classified event, so it already knows "what the deck
 * currently has on screen" without needing the Pi to echo it back. */

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
}

export class SessionRegistry {
  private sessions = new Map<string, SessionRecord>();

  private getOrCreate(sessionId: string): SessionRecord {
    let session = this.sessions.get(sessionId);
    if (!session) {
      session = { sessionId, pending: null, lastSeen: Date.now(), autoAccept: false };
      this.sessions.set(sessionId, session);
    }
    return session;
  }

  applyClassified(evt: ClassifiedEvent): SessionRecord {
    const session = this.getOrCreate(evt.sessionId);
    session.lastSeen = Date.now();

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
