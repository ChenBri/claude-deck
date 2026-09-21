/** Local HTTP endpoint the hook scripts POST to (docs/ARCHITECTURE.md).
 * Hooks stay trivial one-liners; all the real work (scrub, classify,
 * aggregate) happens here, off the hot path of the session. */

import http, { IncomingMessage, ServerResponse } from "node:http";
import { classify } from "./classify";
import { DenylistSettingsStore } from "./denylist";
import { contextPct } from "./enrich/usage";
import { scrubPayload } from "./scrub";
import { SessionRegistry } from "./sessions";
import { DailyStats } from "./stats";
import { sendEvent } from "./link/transport";

const HOST = "127.0.0.1";
const PORT = Number(process.env.DECK_HOOK_PORT ?? 7327);

interface RawHookPost {
  hook?: string;
  payload?: Record<string, unknown>;
  ts?: number;
}

function readBody(req: IncomingMessage): Promise<string> {
  return new Promise((resolve) => {
    const chunks: Buffer[] = [];
    req.on("data", (c) => chunks.push(c));
    req.on("end", () => resolve(Buffer.concat(chunks).toString("utf8")));
  });
}

export interface HookIngestDeps {
  sessions: SessionRegistry;
  stats: DailyStats;
  denylistStore: DenylistSettingsStore;
  onCwdSeen: (cwd: string) => void;
}

export function startHookIngest(deps: HookIngestDeps): http.Server {
  const server = http.createServer(async (req: IncomingMessage, res: ServerResponse) => {
    if (req.method !== "POST" || req.url !== "/hook") {
      res.writeHead(404).end();
      return;
    }
    const body = await readBody(req);
    res.writeHead(204).end(); // hooks never wait for a reply

    let parsed: RawHookPost;
    try {
      parsed = JSON.parse(body || "{}");
    } catch {
      return;
    }
    const hookName = parsed.hook;
    const rawPayload = parsed.payload ?? {};
    if (!hookName) return;

    const cwd = rawPayload.cwd;
    if (typeof cwd === "string") deps.onCwdSeen(cwd);

    const scrubbed = scrubPayload(rawPayload) as Record<string, unknown>;
    const classified = classify(hookName, scrubbed, deps.denylistStore.get());
    if (!classified) return;

    // Not part of classify()'s job (that's a pure mapping, no I/O): reads
    // the session's own transcript for the CONTEXT meter, see enrich/usage.ts.
    if (typeof cwd === "string") {
      const pct = contextPct(classified.sessionId, cwd);
      if (pct !== null) classified.meta.context_pct = pct;
    }

    deps.sessions.applyClassified(classified);
    if (classified.event === "PreToolUse") deps.stats.recordToolCall();
    sendEvent(classified);
  });

  server.listen(PORT, HOST);
  return server;
}
