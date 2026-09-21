# Hooks

`emit.js` is the one-liner every hook runs: it reads the hook's JSON off
stdin, tags it with the hook name, and POSTs it to `127.0.0.1:7327/hook`
without waiting for a reply. It never blocks your session.

That endpoint is served by either:

- `tools/record.py`, during phase 0, to capture a JSONL corpus for
  `tools/replay.py`, or
- the daemon's hook-ingest server, once it's running (`daemon/src/http.ts`).

Either one, `emit.js` doesn't know or care which.

## Setup

1. Merge `settings.snippet.json` into `~/.claude/settings.json` (or a
   project's `.claude/settings.json`), replacing every
   `/absolute/path/to/claude-deck/hooks/emit.js` with this repo's real path.
2. Start whichever is listening: `python firmware/tools/record.py`, or the
   daemon.
3. Use Claude Code normally. Each hook fires `emit.js` in the background.
