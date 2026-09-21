"""State machine: priority, latching, timeouts. Pure logic, no I/O."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum

DONE_CLEAR_SECONDS = 180.0
DEFAULT_IDLE_AFTER_SECONDS = 300.0
APPROVAL_EXPIRY_SECONDS = 90.0
SLOT_COUNT = 5  # rotary switch positions 1-5; position 6 is ALL, not a slot
DEFAULT_SLOT_FREE_AFTER_SECONDS = 1800.0  # how long a finished session holds its slot
TOOL_RATE_WINDOW_SECONDS = 10.0  # trailing window for the WORKING scene's animation speed


class State(Enum):
    READY = "READY"
    WORKING = "WORKING"
    SUBAGENTS = "SUBAGENTS"
    BLOCKED_PERMISSION = "BLOCKED_PERMISSION"
    BLOCKED_INPUT = "BLOCKED_INPUT"
    COMPACTING = "COMPACTING"
    DONE = "DONE"
    ERROR = "ERROR"
    IDLE = "IDLE"
    OFFLINE = "OFFLINE"
    INTERRUPTED = "INTERRUPTED"


# Lamp shared by more than one state; None means no lamp (IDLE/OFFLINE/INTERRUPTED
# have their own presentation, not one of the five lamps).
LAMP = {
    State.READY: "READY",
    State.WORKING: "WORKING",
    State.SUBAGENTS: "WORKING",
    State.BLOCKED_PERMISSION: "BLOCKED",
    State.BLOCKED_INPUT: "BLOCKED",
    State.COMPACTING: "WORKING",
    State.DONE: "DONE",
    State.ERROR: "BLOCKED",
    State.IDLE: None,
    State.OFFLINE: None,
    State.INTERRUPTED: None,
}

# Aggregation priority when the rotary selector is on ALL. Panic/offline are
# handled outside this list, above everything, by Deck.current_state.
PRIORITY = [
    State.BLOCKED_PERMISSION,
    State.BLOCKED_INPUT,
    State.ERROR,
    State.WORKING,
    State.SUBAGENTS,
    State.COMPACTING,
    State.DONE,
    State.READY,
    State.IDLE,
]


class UnknownEventError(ValueError):
    pass


@dataclass
class PendingApproval:
    request_id: str
    tool: str
    target: str
    approvable: bool
    created_at: float

    def is_live(self, now: float) -> bool:
        return self.approvable and (now - self.created_at) < APPROVAL_EXPIRY_SECONDS


@dataclass
class SessionState:
    """Per-session state machine. One instance per live Claude Code session."""

    session_id: str
    state: State = State.READY
    subagent_count: int = 0
    pending: PendingApproval | None = None
    did_work: bool = False
    last_tool: str = ""
    last_target: str = ""
    context_pct: float = 0.0  # of the model's context window; see daemon/src/enrich/usage.ts
    entered_at: float = field(default_factory=time.monotonic)
    last_event_at: float = field(default_factory=time.monotonic)
    _recent_tool_calls: list[float] = field(default_factory=list)

    def _enter(self, state: State, now: float) -> None:
        self.state = state
        self.entered_at = now

    def handle(self, event: str, now: float | None = None, **meta) -> None:
        now = time.monotonic() if now is None else now
        self.last_event_at = now
        if "context_pct" in meta:
            self.context_pct = float(meta["context_pct"])

        if event == "SessionStart":
            self.did_work = False
            self.subagent_count = 0
            self.pending = None
            self._enter(State.READY, now)

        elif event == "UserPromptSubmit":
            self.did_work = True
            if self.state != State.SUBAGENTS:
                self._enter(State.WORKING, now)

        elif event == "PreToolUse":
            self.did_work = True
            self.last_tool = meta.get("tool", "")
            self.last_target = meta.get("target", "")
            self._recent_tool_calls.append(now)
            if meta.get("tool") == "Task":
                self.subagent_count += 1
                self._enter(State.SUBAGENTS, now)
            elif self.state != State.SUBAGENTS:
                self._enter(State.WORKING, now)

        elif event == "PostToolUse":
            if meta.get("failed"):
                self._enter(State.ERROR, now)
                return
            if meta.get("tool") == "Task":
                self.subagent_count = max(0, self.subagent_count - 1)
                if self.subagent_count == 0 and self.state == State.SUBAGENTS:
                    self._enter(State.WORKING, now)

        elif event == "Notification":
            variant = meta.get("variant")
            if variant == "permission":
                self.pending = PendingApproval(
                    request_id=meta["request_id"],
                    tool=meta.get("tool", ""),
                    target=meta.get("target", ""),
                    approvable=meta.get("approvable", True),
                    created_at=now,
                )
                self._enter(State.BLOCKED_PERMISSION, now)
            elif variant == "idle":
                self._enter(State.BLOCKED_INPUT, now)
            else:
                raise UnknownEventError(f"unknown Notification variant {variant!r}")

        elif event == "PreCompact":
            self._enter(State.COMPACTING, now)

        elif event == "Stop":
            self.pending = None
            self._enter(State.DONE if self.did_work else State.READY, now)
            self.did_work = False

        elif event == "SubagentStop":
            self.subagent_count = max(0, self.subagent_count - 1)
            if self.subagent_count == 0 and self.state == State.SUBAGENTS:
                self._enter(State.WORKING, now)

        elif event == "SessionEnd":
            self._enter(State.ERROR if meta.get("error") else State.READY, now)

        else:
            raise UnknownEventError(f"unknown event {event!r}")

    def tick(self, now: float | None = None) -> None:
        """Advance time-based transitions: DONE auto-clear."""
        now = time.monotonic() if now is None else now
        if self.state == State.DONE and now - self.entered_at >= DONE_CLEAR_SECONDS:
            self._enter(State.READY, now)

    def approve_button_live(self, now: float | None = None) -> bool:
        now = time.monotonic() if now is None else now
        return (
            self.state == State.BLOCKED_PERMISSION
            and self.pending is not None
            and self.pending.is_live(now)
        )

    def tool_call_rate(self, now: float | None = None, window_seconds: float = TOOL_RATE_WINDOW_SECONDS) -> float:
        """Tool calls per second over the trailing window; drives how fast
        the WORKING scene's glyphs fly and the mascot types."""
        now = time.monotonic() if now is None else now
        cutoff = now - window_seconds
        self._recent_tool_calls = [t for t in self._recent_tool_calls if t >= cutoff]
        if not self._recent_tool_calls:
            return 0.0
        return len(self._recent_tool_calls) / window_seconds


class SessionRegistry:
    """Tracks every live session, keyed by session id.

    Also assigns each session a rotary-switch slot (1-5), first-available,
    on first sight. A slot is fixed for as long as its session is tracked, so
    switching to position 3 always shows the same session until that session
    is dropped and frees the slot for a new one - it never gets silently
    reassigned because some unrelated session elsewhere ended.
    """

    def __init__(self) -> None:
        self.sessions: dict[str, SessionState] = {}
        self._slot_of: dict[str, int] = {}
        self._session_in_slot: dict[int, str] = {}

    def _assign_slot(self, session_id: str) -> None:
        taken = set(self._session_in_slot)
        for n in range(1, SLOT_COUNT + 1):
            if n not in taken:
                self._slot_of[session_id] = n
                self._session_in_slot[n] = session_id
                return
        # all 5 slots full: this session is only reachable via ALL

    def get(self, session_id: str) -> SessionState | None:
        return self.sessions.get(session_id)

    def get_or_create(self, session_id: str) -> SessionState:
        session = self.sessions.get(session_id)
        if session is None:
            session = SessionState(session_id)
            self.sessions[session_id] = session
            self._assign_slot(session_id)
        return session

    def handle(self, session_id: str, event: str, now: float | None = None, **meta) -> SessionState:
        session = self.get_or_create(session_id)
        session.handle(event, now=now, **meta)
        return session

    def drop(self, session_id: str) -> None:
        self.sessions.pop(session_id, None)
        slot = self._slot_of.pop(session_id, None)
        if slot is not None:
            self._session_in_slot.pop(slot, None)

    def prune(self, max_age_seconds: float = DEFAULT_SLOT_FREE_AFTER_SECONDS, now: float | None = None) -> None:
        """Frees slots held by sessions nobody's touched in a while."""
        now = time.monotonic() if now is None else now
        stale = [sid for sid, s in self.sessions.items() if now - s.last_event_at > max_age_seconds]
        for session_id in stale:
            self.drop(session_id)

    def tick(self, now: float | None = None) -> None:
        now = time.monotonic() if now is None else now
        for session in self.sessions.values():
            session.tick(now)

    def slot(self, n: int) -> SessionState | None:
        session_id = self._session_in_slot.get(n)
        return self.sessions.get(session_id) if session_id is not None else None

    def aggregate(self, selector: str) -> SessionState | None:
        """selector is "1".."5" (a rotary slot), "ALL", or a literal session id."""
        if selector == "ALL":
            if not self.sessions:
                return None

            def rank(session: SessionState) -> int:
                try:
                    return PRIORITY.index(session.state)
                except ValueError:
                    return len(PRIORITY)

            return min(self.sessions.values(), key=rank)
        if selector in ("1", "2", "3", "4", "5"):
            return self.slot(int(selector))
        return self.sessions.get(selector)


@dataclass
class Deck:
    """Top-level device state: sessions plus the physical overrides (panic, link)."""

    registry: SessionRegistry = field(default_factory=SessionRegistry)
    selector: str = "ALL"
    panic_latched: bool = False
    link_alive: bool = True
    idle_after_seconds: float = DEFAULT_IDLE_AFTER_SECONDS

    def panic(self) -> None:
        self.panic_latched = True

    def panic_release(self) -> None:
        self.panic_latched = False

    def set_link_alive(self, alive: bool) -> None:
        self.link_alive = alive

    def set_selector(self, selector: str) -> None:
        self.selector = selector

    def active_session(self) -> SessionState | None:
        return self.registry.aggregate(self.selector)

    def current_state(self, now: float | None = None) -> State:
        now = time.monotonic() if now is None else now
        if self.panic_latched:
            return State.INTERRUPTED
        if not self.link_alive:
            return State.OFFLINE
        session = self.active_session()
        if session is None or (now - session.last_event_at) >= self.idle_after_seconds:
            return State.IDLE
        return session.state

    def approve_button_live(self, now: float | None = None) -> bool:
        if self.panic_latched or not self.link_alive:
            return False
        session = self.active_session()
        return bool(session and session.approve_button_live(now))

    def tick(self, now: float | None = None) -> None:
        self.registry.tick(now)
