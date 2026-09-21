/** Maps a raw Claude Code hook payload onto a normalized (sessionId, event,
 * meta) the Pi's state machine (firmware/deck/state.py) understands, and
 * runs the denylist over pending permission requests. */

import { DenylistSettings, defaultDenylistSettings, isApprovable, matchDenylist } from "./denylist";
import { scrubText } from "./scrub";

export interface ClassifiedEvent {
  sessionId: string;
  event: string;
  meta: Record<string, unknown>;
}

interface ToolInput {
  command?: string;
  file_path?: string;
  path?: string;
  [key: string]: unknown;
}

function targetFrom(toolInput: ToolInput | undefined): string {
  if (!toolInput) return "";
  const raw = toolInput.command ?? toolInput.file_path ?? toolInput.path ?? "";
  return scrubText(String(raw));
}

const PASSTHROUGH_HOOKS = new Set([
  "SessionStart",
  "UserPromptSubmit",
  "PreCompact",
  "Stop",
  "SubagentStop",
]);

export function classify(
  hookName: string,
  payload: Record<string, unknown>,
  denylistSettings: DenylistSettings = defaultDenylistSettings,
): ClassifiedEvent | null {
  const sessionId = String(payload.session_id ?? "default");

  if (PASSTHROUGH_HOOKS.has(hookName)) {
    return { sessionId, event: hookName, meta: {} };
  }

  if (hookName === "PreToolUse") {
    const tool = String(payload.tool_name ?? "");
    const target = targetFrom(payload.tool_input as ToolInput);
    return { sessionId, event: hookName, meta: { tool, target } };
  }

  if (hookName === "PostToolUse") {
    const tool = String(payload.tool_name ?? "");
    const response = payload.tool_response as Record<string, unknown> | undefined;
    const failed = Boolean(response && "error" in response && response.error);
    return { sessionId, event: hookName, meta: { tool, failed } };
  }

  if (hookName === "Notification") {
    const message = scrubText(String(payload.message ?? ""));
    const tool = String(payload.tool_name ?? "");
    const isPermission = Boolean(tool) || /permission/i.test(message);
    if (!isPermission) {
      return { sessionId, event: hookName, meta: { variant: "idle" } };
    }
    const target = targetFrom(payload.tool_input as ToolInput) || message;
    const category = matchDenylist(`${tool} ${target}`, denylistSettings);
    return {
      sessionId,
      event: hookName,
      meta: {
        variant: "permission",
        request_id: String(payload.tool_use_id ?? `${sessionId}-${payload.session_id ?? Date.now()}`),
        tool,
        target,
        approvable: isApprovable(`${tool} ${target}`, denylistSettings),
        denylist_category: category,
      },
    };
  }

  if (hookName === "SessionEnd") {
    return { sessionId, event: hookName, meta: { error: payload.reason === "error" } };
  }

  return null; // unknown hook: ignore rather than guess
}
