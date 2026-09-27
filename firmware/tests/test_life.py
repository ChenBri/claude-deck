from deck.ui.scenes.life import vignette_for_hour
from deck.ui.sprites import _face_overrides


def test_schedule_covers_the_clock_and_wraps_past_midnight():
    assert vignette_for_hour(6) == "coffee"
    assert vignette_for_hour(10) == "coffee"
    assert vignette_for_hour(11) == "wander"
    assert vignette_for_hour(15) == "reading"
    assert vignette_for_hour(19) == "window"
    assert vignette_for_hour(23) == "sleep"
    assert vignette_for_hour(0) == "sleep"
    assert vignette_for_hour(5) == "sleep"


def test_closed_eyes_hide_every_pupil():
    closed = _face_overrides(closed=True)
    assert "K" not in closed.values()
    assert all(closed[(x, 8)] == "B" for x in range(5, 11))


def test_look_moves_both_pupils_together():
    left = {k for k, v in _face_overrides("left").items() if v == "K"}
    assert left == {(5, 7), (5, 8), (8, 7), (8, 8)}
    down = {k for k, v in _face_overrides("down").items() if v == "K"}
    assert down == {(6, 8), (9, 8)}
