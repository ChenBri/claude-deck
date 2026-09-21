import { mkdtempSync, mkdirSync, writeFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test, beforeEach, afterEach } from "node:test";
import assert from "node:assert/strict";

// DECK_CLAUDE_PROJECTS_DIR is read at call time (see enrich/usage.ts), so
// pointing it at a fresh directory before each test is enough - no
// import-order trickery, and no risk of one test's fixtures leaking into
// fiveHourUsagePct()'s all-projects scan in another test.
import { contextPct, fiveHourUsagePct } from "../src/enrich/usage.ts";

let root: string;

beforeEach(() => {
  root = mkdtempSync(join(tmpdir(), "claude-deck-usage-test-"));
  process.env.DECK_CLAUDE_PROJECTS_DIR = root;
});

afterEach(() => {
  delete process.env.DECK_CLAUDE_PROJECTS_DIR;
  rmSync(root, { recursive: true, force: true });
});

function writeTranscript(slug: string, sessionId: string, lines: object[]): void {
  const dir = join(root, slug);
  mkdirSync(dir, { recursive: true });
  writeFileSync(join(dir, `${sessionId}.jsonl`), lines.map((l) => JSON.stringify(l)).join("\n") + "\n");
}

test("contextPct reads the last usage entry against the model's window", () => {
  writeTranscript("C--fake-project", "session-a", [
    { message: { model: "claude-sonnet-5", usage: { input_tokens: 1000, cache_read_input_tokens: 0 } } },
    { message: { model: "claude-sonnet-5", usage: { input_tokens: 50_000, cache_read_input_tokens: 50_000 } } },
  ]);
  const pct = contextPct("session-a", "C:\\fake\\project");
  assert.equal(pct, 100_000 / 200_000);
});

test("contextPct returns null when the transcript doesn't exist yet", () => {
  assert.equal(contextPct("no-such-session", "/nowhere"), null);
});

test("contextPct ignores entries with no usage field (e.g. a user turn)", () => {
  writeTranscript("C--fake-project-2", "session-b", [
    { message: { model: "claude-sonnet-5", usage: { input_tokens: 20_000 } } },
    { message: { role: "user" } }, // no usage: must not be mistaken for zero usage
  ]);
  const pct = contextPct("session-b", "C:\\fake\\project-2");
  assert.equal(pct, 20_000 / 200_000);
});

test("fiveHourUsagePct discounts cache reads instead of counting them at face value", () => {
  // A long agentic session re-sends its whole cache almost every turn;
  // counting cache_read_input_tokens at 1x would make a single real
  // session read as hundreds of millions of "tokens" (confirmed against
  // this repo's own transcripts), pinning the gauge at 100% immediately.
  const now = new Date().toISOString();
  writeTranscript("C--project-three", "s3", [
    { timestamp: now, message: { usage: { input_tokens: 0, cache_read_input_tokens: 10_000_000 } } },
  ]);
  const pct = fiveHourUsagePct();
  assert.equal(pct, (10_000_000 * 0.1) / 25_000_000);
});

test("fiveHourUsagePct sums recent tokens across every project, ignoring stale ones", () => {
  const now = new Date();
  const sixHoursAgo = new Date(now.getTime() - 6 * 60 * 60 * 1000).toISOString();
  const oneHourAgo = new Date(now.getTime() - 1 * 60 * 60 * 1000).toISOString();

  writeTranscript("C--project-one", "s1", [
    { timestamp: oneHourAgo, message: { usage: { input_tokens: 100_000, output_tokens: 0 } } },
    { timestamp: sixHoursAgo, message: { usage: { input_tokens: 999_000, output_tokens: 0 } } }, // too old, must not count
  ]);
  writeTranscript("C--project-two", "s2", [
    { timestamp: oneHourAgo, message: { usage: { input_tokens: 150_000, output_tokens: 0 } } },
  ]);

  const pct = fiveHourUsagePct();
  // 250,000 recent input tokens (weight 1x) against the default 25M budget
  assert.equal(pct, 250_000 / 25_000_000);
});
