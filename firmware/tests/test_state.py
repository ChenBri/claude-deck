from deck.state import (
    APPROVAL_EXPIRY_SECONDS,
    Deck,
    DONE_CLEAR_SECONDS,
    SessionRegistry,
    SessionState,
    State,
)


def test_session_start_is_ready():
    s = SessionState("a")
    s.handle("SessionStart", now=0)
    assert s.state is State.READY


def test_prompt_submit_enters_working():
    s = SessionState("a")
    s.handle("SessionStart", now=0)
    s.handle("UserPromptSubmit", now=1)
    assert s.state is State.WORKING


def test_pretooluse_task_enters_subagents_and_stacks():
    s = SessionState("a")
    s.handle("SessionStart", now=0)
    s.handle("PreToolUse", now=1, tool="Task")
    assert s.state is State.SUBAGENTS
    assert s.subagent_count == 1
    s.handle("PreToolUse", now=2, tool="Task")
    assert s.subagent_count == 2
    # a non-Task tool call while subagents are live must not kick us to WORKING
    s.handle("PreToolUse", now=3, tool="Read")
    assert s.state is State.SUBAGENTS


def test_subagents_drain_back_to_working():
    s = SessionState("a")
    s.handle("SessionStart", now=0)
    s.handle("PreToolUse", now=1, tool="Task")
    s.handle("PreToolUse", now=2, tool="Task")
    s.handle("PostToolUse", now=3, tool="Task")
    assert s.state is State.SUBAGENTS
    assert s.subagent_count == 1
    s.handle("PostToolUse", now=4, tool="Task")
    assert s.state is State.WORKING
    assert s.subagent_count == 0


def test_subagent_stop_event_drains_too():
    s = SessionState("a")
    s.handle("SessionStart", now=0)
    s.handle("PreToolUse", now=1, tool="Task")
    s.handle("SubagentStop", now=2)
    assert s.state is State.WORKING
    assert s.subagent_count == 0


def test_posttooluse_failure_enters_error():
    s = SessionState("a")
    s.handle("SessionStart", now=0)
    s.handle("PreToolUse", now=1, tool="Bash")
    s.handle("PostToolUse", now=2, failed=True)
    assert s.state is State.ERROR


def test_notification_permission_creates_pending_and_blocks():
    s = SessionState("a")
    s.handle("SessionStart", now=0)
    s.handle(
        "Notification",
        now=1,
        variant="permission",
        request_id="req-1",
        tool="Bash",
        target="npm test",
        approvable=True,
    )
    assert s.state is State.BLOCKED_PERMISSION
    assert s.pending.request_id == "req-1"
    assert s.approve_button_live(now=1.0) is True


def test_notification_idle_blocks_without_pending():
    s = SessionState("a")
    s.handle("SessionStart", now=0)
    s.handle("Notification", now=1, variant="idle")
    assert s.state is State.BLOCKED_INPUT
    assert s.pending is None
    assert s.approve_button_live(now=1.0) is False


def test_approval_expires_after_90_seconds():
    s = SessionState("a")
    s.handle("SessionStart", now=0)
    s.handle(
        "Notification",
        now=0,
        variant="permission",
        request_id="req-1",
        approvable=True,
    )
    assert s.approve_button_live(now=APPROVAL_EXPIRY_SECONDS - 1) is True
    assert s.approve_button_live(now=APPROVAL_EXPIRY_SECONDS + 1) is False


def test_denylisted_pending_is_never_live():
    s = SessionState("a")
    s.handle("SessionStart", now=0)
    s.handle(
        "Notification",
        now=0,
        variant="permission",
        request_id="req-1",
        approvable=False,
    )
    assert s.approve_button_live(now=0) is False


def test_stop_after_work_enters_done():
    s = SessionState("a")
    s.handle("SessionStart", now=0)
    s.handle("UserPromptSubmit", now=1)
    s.handle("Stop", now=2)
    assert s.state is State.DONE
    assert s.did_work is False


def test_stop_without_work_enters_ready():
    s = SessionState("a")
    s.handle("SessionStart", now=0)
    s.handle("Stop", now=1)
    assert s.state is State.READY


def test_done_auto_clears_to_ready():
    s = SessionState("a")
    s.handle("SessionStart", now=0)
    s.handle("UserPromptSubmit", now=1)
    s.handle("Stop", now=2)
    assert s.state is State.DONE
    s.tick(now=2 + DONE_CLEAR_SECONDS - 1)
    assert s.state is State.DONE
    s.tick(now=2 + DONE_CLEAR_SECONDS + 1)
    assert s.state is State.READY


def test_precompact_enters_compacting():
    s = SessionState("a")
    s.handle("SessionStart", now=0)
    s.handle("PreToolUse", now=1, tool="Bash")
    s.handle("PreCompact", now=2)
    assert s.state is State.COMPACTING


def test_session_end_error_flag():
    s = SessionState("a")
    s.handle("SessionStart", now=0)
    s.handle("SessionEnd", now=1, error=True)
    assert s.state is State.ERROR


def test_unknown_event_raises():
    s = SessionState("a")
    try:
        s.handle("NotAnEvent", now=0)
    except Exception as exc:
        assert "NotAnEvent" in str(exc)
    else:
        raise AssertionError("expected UnknownEventError")


def test_registry_aggregate_all_picks_highest_priority():
    reg = SessionRegistry()
    reg.handle("a", "SessionStart", now=0)
    reg.handle("a", "UserPromptSubmit", now=1)  # WORKING
    reg.handle("b", "SessionStart", now=0)
    reg.handle(
        "b", "Notification", now=1, variant="permission", request_id="r", approvable=True
    )  # BLOCKED_PERMISSION
    winner = reg.aggregate("ALL")
    assert winner.session_id == "b"


def test_registry_aggregate_single_selector():
    reg = SessionRegistry()
    reg.handle("a", "SessionStart", now=0)
    reg.handle("b", "SessionStart", now=0)
    reg.handle("b", "UserPromptSubmit", now=1)
    assert reg.aggregate("a").state is State.READY
    assert reg.aggregate("b").state is State.WORKING
    assert reg.aggregate("missing") is None


def test_deck_idle_with_no_sessions():
    deck = Deck(selector="ALL")
    assert deck.current_state(now=0) is State.IDLE


def test_deck_idle_after_timeout():
    deck = Deck(selector="a", idle_after_seconds=10)
    deck.registry.handle("a", "SessionStart", now=0)
    assert deck.current_state(now=5) is State.READY
    assert deck.current_state(now=11) is State.IDLE


def test_deck_offline_beats_everything_except_panic():
    deck = Deck(selector="a")
    deck.registry.handle("a", "SessionStart", now=0)
    deck.set_link_alive(False)
    assert deck.current_state(now=0) is State.OFFLINE
    deck.panic()
    assert deck.current_state(now=0) is State.INTERRUPTED


def test_deck_panic_latches_until_release():
    deck = Deck(selector="a")
    deck.registry.handle("a", "SessionStart", now=0)
    deck.panic()
    assert deck.current_state(now=0) is State.INTERRUPTED
    deck.registry.handle("a", "UserPromptSubmit", now=1)
    assert deck.current_state(now=1) is State.INTERRUPTED
    deck.panic_release()
    assert deck.current_state(now=1) is State.WORKING


def test_deck_approve_button_live_tracks_selector():
    deck = Deck(selector="a")
    deck.registry.handle("a", "SessionStart", now=0)
    deck.registry.handle(
        "a", "Notification", now=0, variant="permission", request_id="r", approvable=True
    )
    assert deck.approve_button_live(now=1) is True
    deck.set_selector("b")
    assert deck.approve_button_live(now=1) is False
    deck.panic()
    deck.set_selector("a")
    assert deck.approve_button_live(now=1) is False
