import time

from deck.screen import WAKE_SECONDS, in_quiet_hours, screen_level, wall_clock
from deck.state import State

SETTINGS = {"quiet_hours": True, "quiet_start": 1, "quiet_end": 8, "night_screen": 0.4}
ASLEEP = WAKE_SECONDS + 1


def test_quiet_hours_plain_and_wrapping():
    assert in_quiet_hours(3, 1, 8)
    assert not in_quiet_hours(8, 1, 8)
    assert in_quiet_hours(23, 22, 6) and in_quiet_hours(2, 22, 6)
    assert not in_quiet_hours(12, 22, 6)
    assert not in_quiet_hours(5, 5, 5)


def test_blanks_only_when_calm_quiet_and_untouched():
    assert screen_level(State.IDLE, 3, False, ASLEEP, SETTINGS) == 0.0
    assert screen_level(State.READY, 3, False, ASLEEP, SETTINGS) == 0.0
    assert screen_level(State.IDLE, 12, False, ASLEEP, SETTINGS) == 1.0
    assert screen_level(State.IDLE, 3, False, 10.0, SETTINGS) == 1.0  # recently touched


def test_attention_and_live_work_always_light_the_screen():
    for state in (State.BLOCKED_PERMISSION, State.BLOCKED_INPUT, State.ERROR, State.INTERRUPTED, State.WORKING):
        assert screen_level(state, 3, False, ASLEEP, SETTINGS) == 1.0


def test_night_dims_and_disabled_schedule_never_blanks():
    assert screen_level(State.IDLE, 12, True, ASLEEP, SETTINGS) == 0.4
    off = {**SETTINGS, "quiet_hours": False}
    assert screen_level(State.IDLE, 3, False, ASLEEP, off) == 1.0


def test_wall_clock_prefers_daemon_and_falls_back():
    fallback = time.strptime("2026-01-02 09:30", "%Y-%m-%d %H:%M")
    c = wall_clock({"clock": "23:05", "date": "2026-09-27"}, fallback)
    assert (c.hour, c.minute, c.year, c.month, c.day) == (23, 5, 2026, 9, 27)
    assert c.weekday == 6  # Sunday
    c = wall_clock({"clock": "garbage"}, fallback)
    assert (c.hour, c.minute, c.day) == (9, 30, 2)
