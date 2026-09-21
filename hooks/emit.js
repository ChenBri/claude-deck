#!/usr/bin/env node
// Trivial one-liner hook shim: reads the hook's JSON off stdin, tags it with
// the hook name given as argv[2], and fires it at the daemon (or, in phase 0,
// tools/record.py listening on the same address). Never waits for a reply,
// so it adds no measurable latency to the session.
"use strict";

const http = require("http");

const hook = process.argv[2] || "unknown";
const chunks = [];

process.stdin.on("data", (chunk) => chunks.push(chunk));
process.stdin.on("end", () => {
  let payload = {};
  try {
    payload = JSON.parse(Buffer.concat(chunks).toString("utf8") || "{}");
  } catch {
    // malformed hook input must never crash the session; send it empty
  }

  const body = JSON.stringify({ hook, payload, ts: Date.now() });
  const req = http.request(
    { host: "127.0.0.1", port: 7327, path: "/hook", method: "POST", timeout: 300, headers: { "Content-Type": "application/json" } },
    (res) => res.resume(),
  );
  req.on("error", () => {});
  req.on("timeout", () => req.destroy());
  req.end(body);
  process.exit(0);
});
