/** Two panel meters, per DECISIONS.md #19/#57: Context Window (exact, read
 * straight off the current session's own transcript) and 5-hour usage (an
 * estimate, since Anthropic doesn't expose actual remaining quota anywhere
 * a local process can read). Both come from Claude Code's own local session
 * logs under ~/.claude/projects, the same files a tool like ccusage parses. */

import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";

const FIVE_HOUR_MS = 5 * 60 * 60 * 1000;

// A function, not a frozen constant: read at call time so tests (and an env
// var set after this module first loads) both see DECK_CLAUDE_PROJECTS_DIR.
function projectsDir(): string {
  return process.env.DECK_CLAUDE_PROJECTS_DIR ?? join(homedir(), ".claude", "projects");
}

// Best-effort table: Anthropic hasn't published a machine-readable way to
// ask a model its own context window, so this is filled in from what's
// documented today and falls back to the Sonnet/Opus-class default.
const CONTEXT_WINDOW_BY_MODEL: Record<string, number> = {
  "claude-opus-5": 200_000,
  "claude-sonnet-5": 200_000,
};
const DEFAULT_CONTEXT_WINDOW = 200_000;

// No documented number exists for what a 5-hour window actually allows on
// any given plan, so this is a starting guess, not a fact. Calibrated once
// against something real: this repo's own multi-hour build session landed
// around 26.5M weighted units, so a single heavy session lands near the top
// of the gauge rather than invisible at the bottom. Still needs tuning per
// plan (Pro vs. a Max tier) by watching a few real windows - see README.md.
const FIVE_HOUR_TOKEN_BUDGET = Number(process.env.DECK_FIVE_HOUR_TOKEN_BUDGET ?? 25_000_000);

interface TranscriptUsage {
  input_tokens?: number;
  output_tokens?: number;
  cache_read_input_tokens?: number;
  cache_creation_input_tokens?: number;
}

interface TranscriptEntry {
  timestamp?: string;
  message?: { model?: string; usage?: TranscriptUsage };
}

// Raw, not weighted: this is literally what occupies the context window at
// the moment a turn is generated, so it's what contextPct() needs. Output
// tokens are deliberately excluded - they're the response being generated,
// not something already sitting in the window that was sent as input.
function contextTokens(usage: TranscriptUsage): number {
  return (
    (usage.input_tokens ?? 0) +
    (usage.cache_read_input_tokens ?? 0) +
    (usage.cache_creation_input_tokens ?? 0)
  );
}

// Weighted, not a raw token count: a long agentic session re-sends its whole
// cache on nearly every turn, so naively summing cache_read_input_tokens at
// face value inflates a multi-hour session into hundreds of millions of
// "tokens" (confirmed against this repo's own multi-hour session), making
// the gauge useless (pins at 100% almost immediately). Weights approximate
// Anthropic's own relative pricing (cache reads are roughly a tenth the cost
// of a fresh input token, output roughly five times), tracking real usage
// pressure far better than a raw count - still an estimate, not the real
// formula behind the 5-hour limit, which isn't published.
function usagePressure(usage: TranscriptUsage): number {
  return (
    (usage.input_tokens ?? 0) +
    5 * (usage.output_tokens ?? 0) +
    1.25 * (usage.cache_creation_input_tokens ?? 0) +
    0.1 * (usage.cache_read_input_tokens ?? 0)
  );
}

function readEntries(path: string): TranscriptEntry[] {
  const lines = readFileSync(path, "utf8").split("\n");
  const entries: TranscriptEntry[] = [];
  for (const line of lines) {
    if (!line) continue;
    try {
      entries.push(JSON.parse(line));
    } catch {
      // a line written mid-append when we read it: skip, not fatal
    }
  }
  return entries;
}

// Mirrors Claude Code's own project-directory naming (confirmed against a
// real transcript path: every non-alphanumeric character becomes a dash).
function slugForCwd(cwd: string): string {
  return cwd.replace(/[^a-zA-Z0-9]/g, "-");
}

/** Exact, not an estimate: how much of the model's context window the most
 * recent turn in this session's own transcript actually used. */
export function contextPct(sessionId: string, cwd: string): number | null {
  try {
    const transcriptPath = join(projectsDir(), slugForCwd(cwd), `${sessionId}.jsonl`);
    if (!existsSync(transcriptPath)) return null;
    const entries = readEntries(transcriptPath);
    for (let i = entries.length - 1; i >= 0; i--) {
      const usage = entries[i].message?.usage;
      if (!usage) continue;
      const windowSize = CONTEXT_WINDOW_BY_MODEL[entries[i].message?.model ?? ""] ?? DEFAULT_CONTEXT_WINDOW;
      return Math.min(1, contextTokens(usage) / windowSize);
    }
    return null;
  } catch {
    return null; // transcript mid-write, permissions, whatever: the meter just holds its last value
  }
}

/** An estimate, not a fact (see the module docstring): total tokens across
 * every project's transcripts in the trailing 5 hours, against a budget
 * that's a guess until you've calibrated it against your own plan. */
export function fiveHourUsagePct(): number {
  try {
    const cutoff = Date.now() - FIVE_HOUR_MS;
    const dir = projectsDir();
    let total = 0;
    for (const projectDir of readdirSync(dir)) {
      const fullDir = join(dir, projectDir);
      if (!statSync(fullDir).isDirectory()) continue;
      for (const file of readdirSync(fullDir)) {
        if (!file.endsWith(".jsonl")) continue;
        for (const entry of readEntries(join(fullDir, file))) {
          if (!entry.timestamp || !entry.message?.usage) continue;
          if (new Date(entry.timestamp).getTime() < cutoff) continue;
          total += usagePressure(entry.message.usage);
        }
      }
    }
    return Math.min(1, total / FIVE_HOUR_TOKEN_BUDGET);
  } catch {
    return 0;
  }
}
