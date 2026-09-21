export interface HostActions {
  approve(sessionId: string): Promise<void>;
  deny(sessionId: string): Promise<void>;
  interrupt(): Promise<void>;
  focusOrLaunchClaude(): Promise<void>;
  newSession(): Promise<void>;
  planMode(): Promise<void>;
  pushToTalk(): Promise<void>;
}
