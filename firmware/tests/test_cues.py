from deck.audio.cues import event_for_transition
from deck.state import State


def test_no_sound_on_first_frame_or_same_state():
    assert event_for_transition(None, State.BLOCKED_PERMISSION) is None
    assert event_for_transition(State.WORKING, State.WORKING) is None


def test_attention_states_chime():
    assert event_for_transition(State.WORKING, State.BLOCKED_PERMISSION) == "blocked"
    assert event_for_transition(State.WORKING, State.DONE) == "finished"
    assert event_for_transition(State.WORKING, State.ERROR) == "error"


def test_blocked_variants_do_not_chime_twice():
    assert event_for_transition(State.BLOCKED_PERMISSION, State.BLOCKED_INPUT) is None


def test_task_start_only_from_rest():
    assert event_for_transition(State.READY, State.WORKING) == "task_start"
    assert event_for_transition(State.IDLE, State.WORKING) == "task_start"
    assert event_for_transition(State.BLOCKED_PERMISSION, State.WORKING) is None
    assert event_for_transition(State.SUBAGENTS, State.WORKING) is None
