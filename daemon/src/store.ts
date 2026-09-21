/** SQLite audit log of every deck-originated action. docs/SAFETY.md rule 8:
 * if the box ever approves something surprising, there is a record of
 * exactly what and when. */

import { DatabaseSync } from "node:sqlite";
import path from "node:path";

export interface AuditEntry {
  ts: number;
  sessionId: string;
  requestId: string | null;
  kind: string;
  tool: string | null;
  target: string | null;
  host: string;
  outcome: "approved" | "denied" | "rejected";
  reason: string | null;
}

export class AuditLog {
  private db: DatabaseSync;

  constructor(dbPath = path.join(process.cwd(), "audit.sqlite")) {
    this.db = new DatabaseSync(dbPath);
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS audit (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts INTEGER NOT NULL,
        session_id TEXT NOT NULL,
        request_id TEXT,
        kind TEXT NOT NULL,
        tool TEXT,
        target TEXT,
        host TEXT NOT NULL,
        outcome TEXT NOT NULL,
        reason TEXT
      )
    `);
  }

  record(entry: AuditEntry): void {
    const stmt = this.db.prepare(`
      INSERT INTO audit (ts, session_id, request_id, kind, tool, target, host, outcome, reason)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    `);
    stmt.run(
      entry.ts,
      entry.sessionId,
      entry.requestId,
      entry.kind,
      entry.tool,
      entry.target,
      entry.host,
      entry.outcome,
      entry.reason,
    );
  }

  close(): void {
    this.db.close();
  }
}
