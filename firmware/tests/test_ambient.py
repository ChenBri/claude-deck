from deck.state import SessionState, State
from deck.ui.cards import available
from deck.ui.scenes.ambient import Rotation, ambient_due, build_cycle


def _session(last_event_at):
    s = SessionState("s")
    s.last_event_at = last_event_at
    return s


def test_idle_is_ambient_at_once_ready_and_done_after_quiet():
    assert ambient_due(State.IDLE, None, now=0.0, after_seconds=60)
    assert not ambient_due(State.READY, _session(100.0), now=130.0, after_seconds=60)
    assert ambient_due(State.READY, _session(100.0), now=160.0, after_seconds=60)
    assert ambient_due(State.DONE, _session(100.0), now=160.0, after_seconds=60)


def test_states_that_want_you_never_go_ambient():
    for state in (State.WORKING, State.SUBAGENTS, State.BLOCKED_PERMISSION, State.BLOCKED_INPUT,
                  State.ERROR, State.COMPACTING, State.OFFLINE, State.INTERRUPTED):
        assert not ambient_due(state, _session(0.0), now=10_000.0, after_seconds=60)


def test_cycle_puts_a_mascot_after_every_two_cards_and_always_has_one():
    assert build_cycle({"clock"}) == ["clock", "mascot"]
    assert build_cycle({"clock", "weather", "usage"}) == ["clock", "weather", "mascot", "usage", "mascot"]


def test_rotation_advances_by_duration_and_skips():
    r = Rotation()
    avail = {"clock", "weather"}
    assert r.update(0.0, avail, 20, 60)[0] == "clock"
    assert r.update(19.0, avail, 20, 60)[0] == "clock"
    assert r.update(20.0, avail, 20, 60)[0] == "weather"
    assert r.update(40.0, avail, 20, 60)[0] == "mascot"
    assert r.update(99.0, avail, 20, 60)[0] == "mascot"
    assert r.update(100.0, avail, 20, 60)[0] == "clock"
    assert r.update(101.0, avail, 20, 60, skip=-1)[0] == "mascot"


def test_rotation_moves_on_when_a_cards_data_disappears():
    r = Rotation()
    r.update(0.0, {"clock", "weather"}, 20, 60)
    r.update(20.0, {"clock", "weather"}, 20, 60)
    assert r.item == "weather"
    assert r.update(21.0, {"clock"}, 20, 60)[0] != "weather"


def test_cards_only_offered_with_data():
    assert available({}) == {"clock"}
    info = {"weather": "20C clear", "today": {}, "git": "master, clean", "five_hour_series": [0, 0.01]}
    assert available(info) == {"clock", "weather", "usage", "git", "five_hour"}
    assert "five_hour" not in available({"five_hour_series": [0, 0]})
