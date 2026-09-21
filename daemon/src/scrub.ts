/**
 * Truncate and redact before anything leaves the daemon for the Pi.
 * docs/SAFETY.md rule 7: the Pi renders text to a screen and writes state
 * transitions to its card, so nothing sensitive may reach it.
 */

const MAX_LENGTH = 80;

const SECRET_PATTERNS: RegExp[] = [
  /\b\w+:\/\/[^/\s]+:[^/\s]+@\S+/gi, // user:pass@host connection strings
  /\b(sk|pk|ghp|gho|ghu|ghs|xox[abp])-?[A-Za-z0-9_-]{16,}\b/gi, // common API key shapes
  /\bAKIA[0-9A-Z]{16}\b/g, // AWS access key id
  /-----BEGIN [A-Z ]+PRIVATE KEY-----[\s\S]*?-----END [A-Z ]+PRIVATE KEY-----/gi,
  /\b(api|access|secret)[_-]?(key|token)\b\s*[:=]\s*\S+/gi,
];

function redactSecrets(text: string): string {
  let out = text;
  for (const pattern of SECRET_PATTERNS) {
    out = out.replace(pattern, "[redacted]");
  }
  return out;
}

/** /a/very/long/real/path/to/file.ts -> .../to/file.ts */
function shortenPath(text: string): string {
  return text.replace(/(?:[\w.-]+[\\/]){3,}([\w.-]+[\\/][\w.-]+)/g, "...$1");
}

export function scrubText(text: string): string {
  const redacted = shortenPath(redactSecrets(text));
  return redacted.length > MAX_LENGTH ? redacted.slice(0, MAX_LENGTH - 1) + "…" : redacted;
}

/** Recursively scrubs every string value in a hook payload. Depth-limited so a
 * malformed or adversarial payload can never cause unbounded recursion. */
export function scrubPayload(value: unknown, depth = 0): unknown {
  if (depth > 6) return "[too deep]";
  if (typeof value === "string") return scrubText(value);
  if (Array.isArray(value)) return value.slice(0, 20).map((v) => scrubPayload(v, depth + 1));
  if (value && typeof value === "object") {
    const out: Record<string, unknown> = {};
    for (const [key, v] of Object.entries(value as Record<string, unknown>).slice(0, 40)) {
      out[key] = scrubPayload(v, depth + 1);
    }
    return out;
  }
  return value;
}
