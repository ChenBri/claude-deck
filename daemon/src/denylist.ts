/**
 * Dangerous-call detection. All four categories from docs/SAFETY.md rule 4.
 * Patterns live here, not the encoder menu, because you cannot type a regex
 * on a knob; the menu only flips whole categories on and off.
 *
 * NOTE: category enable/disable is not yet synced from the Pi's settings
 * menu (firmware/deck/menu.py) to this daemon over the link. Until that
 * wiring exists, every category defaults to enabled here, which is the safe
 * (fail-closed) default.
 */

export type DenylistCategory = "database" | "destructive_fs_git" | "infrastructure" | "secrets";

const PATTERNS: Record<DenylistCategory, RegExp[]> = {
  database: [
    /\b(psql|mysql|mongosh|redis-cli)\b/i,
    /\b\w+:\/\/[^/\s]+:[^/\s]+@/i, // user:pass@host connection strings
    /--host[= ]\S+|--uri[= ]\S+/i,
  ],
  destructive_fs_git: [
    /\brm\s+-[a-z]*r[a-z]*f\b|\brm\s+-[a-z]*f[a-z]*r\b/i,
    /\bgit\s+push\s+(--force|-f)\b/i,
    /\bgit\s+reset\s+--hard\b/i,
    /\bgit\s+branch\s+-D\b/i,
    /\bgit\s+(rebase\s+-i|filter-branch|push\s+--force-with-lease)\b/i,
  ],
  infrastructure: [
    /\bterraform\s+(apply|destroy)\b/i,
    /\bkubectl\b(?!.*--context[= ]?(docker-desktop|minikube|kind|local))/i,
    /\baws\s+\S+\s+(create|delete|put|update|terminate)/i,
    /\beksctl\b/i,
  ],
  secrets: [
    /\.env(\.\w+)?\b/i,
    /\bcredentials(\.json)?\b/i,
    /\bkeychain\b/i,
    /\bid_(rsa|ed25519|ecdsa)\b|private[_-]?key/i,
    /\b(api|access)[_-]?(key|token|secret)\b\s*[:=]/i,
  ],
};

export interface DenylistSettings {
  enabled: Record<DenylistCategory, boolean>;
}

export const defaultDenylistSettings: DenylistSettings = {
  enabled: { database: true, destructive_fs_git: true, infrastructure: true, secrets: true },
};

/** Returns the first matching category, or null if the call is clean. */
export function matchDenylist(text: string, settings: DenylistSettings = defaultDenylistSettings): DenylistCategory | null {
  for (const category of Object.keys(PATTERNS) as DenylistCategory[]) {
    if (!settings.enabled[category]) continue;
    if (PATTERNS[category].some((re) => re.test(text))) return category;
  }
  return null;
}

export function isApprovable(text: string, settings: DenylistSettings = defaultDenylistSettings): boolean {
  return matchDenylist(text, settings) === null;
}
