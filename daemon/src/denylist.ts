/**
 * Dangerous-call detection. All four categories from docs/SAFETY.md rule 4.
 * Patterns live here, not the encoder menu, because you cannot type a regex
 * on a knob; the menu only flips whole categories on and off (synced in via
 * DenylistSettingsStore, see link/transport.ts's "denylist_toggle" action).
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

const CATEGORIES = Object.keys(defaultDenylistSettings.enabled) as DenylistCategory[];

export function isDenylistCategory(value: string): value is DenylistCategory {
  return (CATEGORIES as string[]).includes(value);
}

/** Live, mutable denylist settings, synced from the Pi's encoder menu
 * (firmware/deck/menu.py) over link/transport.ts's action endpoint. Starts
 * fail-closed (every category enabled) until the Pi says otherwise. */
export class DenylistSettingsStore {
  private settings: DenylistSettings = { enabled: { ...defaultDenylistSettings.enabled } };

  get(): DenylistSettings {
    return this.settings;
  }

  setCategory(category: DenylistCategory, enabled: boolean): void {
    this.settings = { enabled: { ...this.settings.enabled, [category]: enabled } };
  }
}

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
