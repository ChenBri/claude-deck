/** Today's totals for the idle dashboard. Resets when the local date rolls
 * over; in-memory only, the audit log (store.ts) is the durable record. */

function today(): string {
  return new Date().toDateString();
}

export class DailyStats {
  private day = today();
  private toolCalls = 0;
  private approvals = 0;
  private denials = 0;

  private rollIfNeeded(): void {
    const d = today();
    if (d !== this.day) {
      this.day = d;
      this.toolCalls = 0;
      this.approvals = 0;
      this.denials = 0;
    }
  }

  recordToolCall(): void {
    this.rollIfNeeded();
    this.toolCalls += 1;
  }

  recordApproval(approved: boolean): void {
    this.rollIfNeeded();
    if (approved) this.approvals += 1;
    else this.denials += 1;
  }

  summary(): string {
    this.rollIfNeeded();
    return `${this.toolCalls} tool calls, ${this.approvals} approved, ${this.denials} denied`;
  }
}
