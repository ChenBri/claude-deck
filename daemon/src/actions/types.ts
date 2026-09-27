export interface HostActions {
  approve(sessionId: string): Promise<void>;
  deny(sessionId: string): Promise<void>;
  interrupt(): Promise<void>;
  focusOrLaunchClaude(): Promise<void>;
  newSession(): Promise<void>;
  /** presses is how many times to send Shift+Tab, the CLI's real permission-
   * mode cycle key (see code.claude.com/docs/en/permission-modes). guard.ts
   * computes it from the session's last-seen permission_mode, since the
   * cycle (default -> acceptEdits -> plan -> back to default, 3 presses
   * from auto) is relative to current state, not a fixed hotkey. 0 means
   * already in plan mode: don't send anything. */
  planMode(presses: number): Promise<void>;
  pushToTalk(): Promise<void>;
  /** level is "LOW" | "MEDIUM" | "HIGH" | "XHIGH" | "MAX", straight off
   * the effort dial. A real, confirmed mechanism: types Claude Code's own
   * `/effort <level>` slash command mid-session (see
   * code.claude.com/docs/en/slash-commands). */
  effortSelect(level: string): Promise<void>;
}
