export interface HostActions {
  approve(sessionId: string): Promise<void>;
  deny(sessionId: string): Promise<void>;
  interrupt(): Promise<void>;
  focusOrLaunchClaude(): Promise<void>;
  newSession(): Promise<void>;
  planMode(): Promise<void>;
  pushToTalk(): Promise<void>;
  /** level is "LOW" | "MEDIUM" | "HIGH" | "XHIGH" | "MAX", straight off
   * the effort dial. Unlike planMode(), this is a real, confirmed
   * mechanism: types Claude Code's own `/effort <level>` slash command
   * mid-session (see code.claude.com/docs/en/slash-commands), not a
   * guessed hotkey. */
  effortSelect(level: string): Promise<void>;
}
