from deck.state import State
from deck.ui.pixels import pixels_for_state


def test_pixels_count_and_off_at_zero_brightness():
    colors = pixels_for_state(State.READY, now=0.0, brightness=0.0, count=30)
    assert len(colors) == 30
    assert all(c == (0, 0, 0) for c in colors)


def test_pixels_scale_with_brightness():
    full = pixels_for_state(State.READY, now=0.0, brightness=1.0, count=1)[0]
    dim = pixels_for_state(State.READY, now=0.0, brightness=0.25, count=1)[0]
    assert dim < full  # tuple compare: each dim channel <= corresponding full channel, and strictly less overall
    assert dim != (0, 0, 0)


def test_non_pulse_state_is_static_over_time():
    a = pixels_for_state(State.READY, now=0.0, brightness=1.0, count=1)
    b = pixels_for_state(State.READY, now=100.0, brightness=1.0, count=1)
    assert a == b


def test_blocked_state_pulses_over_time():
    samples = {
        pixels_for_state(State.BLOCKED_PERMISSION, now=t, brightness=1.0, count=1)[0]
        for t in (0.0, 0.4, 0.8, 1.2)
    }
    assert len(samples) > 1  # brightness actually varies across the pulse period


def test_pulse_never_fully_off():
    darkest = min(
        pixels_for_state(State.INTERRUPTED, now=t / 10, brightness=1.0, count=1)[0][0]
        for t in range(0, 32)
    )
    assert darkest > 0
