"""Which chiptune event (if any) a deck state change should play. Pure
logic so it can be tested without a mixer; main.py calls chiptune.play()
with the result."""
from __future__ import annotations

from deck.state import State

_ENTER_SOUNDS = {
    State.BLOCKED_PERMISSION: "blocked",
    State.BLOCKED_INPUT: "blocked",
    State.DONE: "finished",
    State.ERROR: "error",
}

# WORKING only chimes when work starts from rest, not when it resumes after
# an approval or a subagent finishing, or it would chime on every tool call.
_TASK_START_FROM = {State.READY, State.IDLE, State.DONE}


def event_for_transition(prev: State | None, new: State) -> str | None:
    if prev is None or prev == new:
        return None
    if new in _ENTER_SOUNDS:
        # BLOCKED_PERMISSION <-> BLOCKED_INPUT is still the same "waiting on you"
        if _ENTER_SOUNDS.get(prev) == _ENTER_SOUNDS[new]:
            return None
        return _ENTER_SOUNDS[new]
    if new == State.WORKING and prev in _TASK_START_FROM:
        return "task_start"
    return None
