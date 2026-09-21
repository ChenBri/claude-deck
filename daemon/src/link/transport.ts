/** HTTP to the Pi over the USB link (docs/HARDWARE.md: 10.55.0.1 the Pi,
 * 10.55.0.2 the host). Two directions: push classified events and idle-info
 * out to the Pi, and receive button/toggle actions back from it.
 *
 * All four addresses are overridable so the daemon and firmware/deck/link.py
 * can both run on one dev machine before any hardware exists - see
 * README.md's "running the full stack locally" section. */

import http, { IncomingMessage, ServerResponse } from "node:http";
import { ClassifiedEvent } from "../classify";
import { ActionRequest, Guard } from "../guard";

const PI_HOST = process.env.DECK_PI_HOST ?? "10.55.0.1";
const PI_PORT = Number(process.env.DECK_PI_PORT ?? 7328);
const LISTEN_HOST = process.env.DECK_DAEMON_LISTEN_HOST ?? "10.55.0.2";
const LISTEN_PORT = Number(process.env.DECK_DAEMON_LISTEN_PORT ?? 7329);
const SEND_TIMEOUT_MS = 1000;

function postJson(host: string, port: number, path: string, body: unknown): void {
  const data = Buffer.from(JSON.stringify(body));
  const req = http.request(
    { host, port, path, method: "POST", timeout: SEND_TIMEOUT_MS, headers: { "Content-Type": "application/json" } },
    (res) => res.resume(),
  );
  req.on("error", () => {}); // the Pi being unreachable must never crash the daemon
  req.on("timeout", () => req.destroy());
  req.end(data);
}

export function sendEvent(evt: ClassifiedEvent): void {
  postJson(PI_HOST, PI_PORT, "/event", { session_id: evt.sessionId, event: evt.event, meta: evt.meta });
}

export function sendIdleInfo(info: Record<string, unknown>): void {
  postJson(PI_HOST, PI_PORT, "/idle_info", info);
}

/** A bare keepalive, sent on its own schedule (see index.ts) independent of
 * hook events or the idle-info refresh - those are irregular/slow and must
 * not double as the link's liveness signal, or the Pi flags OFFLINE in the
 * gaps between them even though the daemon never went anywhere. */
export function sendHeartbeat(): void {
  postJson(PI_HOST, PI_PORT, "/heartbeat", {});
}

function readBody(req: IncomingMessage): Promise<string> {
  return new Promise((resolve) => {
    const chunks: Buffer[] = [];
    req.on("data", (c) => chunks.push(c));
    req.on("end", () => resolve(Buffer.concat(chunks).toString("utf8")));
  });
}

export function startActionListener(guard: Guard): http.Server {
  const server = http.createServer(async (req: IncomingMessage, res: ServerResponse) => {
    if (req.method !== "POST" || req.url !== "/action") {
      res.writeHead(404).end();
      return;
    }
    const body = await readBody(req);
    res.writeHead(204).end();
    try {
      const action = JSON.parse(body || "{}") as ActionRequest;
      await guard.handle(action);
    } catch (err) {
      console.error("action listener: bad request", err);
    }
  });

  server.on("error", (err: NodeJS.ErrnoException) => {
    console.warn(
      `link/transport: could not bind ${LISTEN_HOST}:${LISTEN_PORT} (${err.code}). ` +
        "Expected until the USB gadget link is configured; button actions from the Pi won't arrive.",
    );
  });
  server.on("listening", () => {
    console.log(
      `link/transport: action listener up on ${LISTEN_HOST}:${LISTEN_PORT}, ` +
        `sending events to the Pi at ${PI_HOST}:${PI_PORT}`,
    );
  });
  server.listen(LISTEN_PORT, LISTEN_HOST);
  return server;
}
