export interface HostActions {
  approve(sessionId: string): Promise<void>;
  deny(sessionId: string): Promise<void>;
  interrupt(): Promise<void>;
  focusOrLaunchClaude(): Promise<void>;
  newSession(): Promise<void>;
  planMode(): Promise<void>;
  pushToTalk(): Promise<void>;
  /** level is "LOW" | "MED" | "HIGH" | "MAX", straight off the effort
   * dial. Same status as planMode(): a placeholder hotkey, not a
   * confirmed way to actually change Claude Code's reasoning effort -
   * tune to whatever that turns out to be locally. */
  effortSelect(level: string): Promise<void>;
}
