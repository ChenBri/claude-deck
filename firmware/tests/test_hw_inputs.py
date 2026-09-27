from deck.panel.hw.gpio import DEBOUNCE_SECONDS, EdgeDecoder
from deck.panel.hw.inputs import (
    EFFORT_BITS,
    GB_BITS,
    JOY_PUSH_BIT,
    MECH_KEY_BITS,
    SELECTOR_BITS,
    TOGGLE_BITS,
    AnalogInputs,
    ExpanderInputs,
    axis,
)

IDLE = {"APPROVE": 1, "DENY": 1, "PANIC": 1, "ENC_PUSH": 1, "ENC_A": 1, "ENC_B": 1}


def _kinds(events):
    return [(e.kind, e.name, e.value) for e in events]


# -- GPIO edges ---------------------------------------------------------------

def test_button_press_reports_once_through_bounce():
    d = EdgeDecoder()
    d.seed(IDLE)
    events = d.feed("APPROVE", 0, 1.000)
    events += d.feed("APPROVE", 1, 1.002)  # bounce
    events += d.feed("APPROVE", 0, 1.004)
    events += d.settle(1.05)
    assert _kinds(events) == [("button", "APPROVE", None)]


def test_short_tap_is_released_by_settle():
    d = EdgeDecoder()
    d.seed(IDLE)
    d.feed("ENC_PUSH", 0, 1.000)
    assert _kinds(d.feed("ENC_PUSH", 1, 1.005)) == []  # inside the debounce window
    assert _kinds(d.settle(1.005 + DEBOUNCE_SECONDS)) == [("encoder", "push_up", None)]


def test_mushroom_latched_at_boot_reports_immediately():
    d = EdgeDecoder()
    assert _kinds(d.seed({**IDLE, "PANIC": 0})) == [("panic", "panic", True)]
    assert _kinds(EdgeDecoder().seed(IDLE)) == []


def test_mushroom_reports_latch_and_release():
    d = EdgeDecoder()
    d.seed(IDLE)
    assert _kinds(d.feed("PANIC", 0, 1.0)) == [("panic", "panic", True)]
    assert _kinds(d.feed("PANIC", 1, 5.0)) == [("panic", "panic", False)]


def _turn(d, sequence):
    events = []
    for a, b in sequence:
        events += d.feed("ENC_A", a, 0.0)
        events += d.feed("ENC_B", b, 0.0)
    return events


def test_encoder_one_detent_each_way_and_invert():
    cw = [(0, 1), (0, 0), (1, 0), (1, 1)]
    ccw = [(1, 0), (0, 0), (0, 1), (1, 1)]
    d = EdgeDecoder()
    d.seed(IDLE)
    assert _kinds(_turn(d, cw)) == [("encoder", "cw", None)]
    assert _kinds(_turn(d, ccw)) == [("encoder", "ccw", None)]
    inv = EdgeDecoder(invert_encoder=True)
    inv.seed(IDLE)
    assert _kinds(_turn(inv, cw)) == [("encoder", "ccw", None)]


def test_encoder_wobble_back_to_rest_is_not_a_step():
    d = EdgeDecoder()
    d.seed(IDLE)
    assert _kinds(_turn(d, [(0, 1), (1, 1)])) == []


# -- expanders ------------------------------------------------------------------

def _mask(bits):
    m = 0
    for b in bits:
        m |= 1 << b
    return m


def _stable(ex, m1, m2):
    ex.update(m1, m2)
    return ex.update(m1, m2)


def test_first_stable_read_syncs_positions_but_not_held_keys():
    ex = ExpanderInputs()
    m1 = _mask([SELECTOR_BITS[2], TOGGLE_BITS["NIGHT"], MECH_KEY_BITS["NEW"]])
    m2 = _mask([EFFORT_BITS[4]])
    assert ex.update(m1, m2) == []  # needs two frames
    events = _kinds(ex.update(m1, m2))
    assert ("rotary", "selector", "3") in events
    assert ("rotary", "effort", "MAX") in events
    assert ("toggle", "NIGHT", True) in events and ("toggle", "MUTE", False) in events
    assert not any(k == "mech_key" for k, _, _ in events)


def test_presses_and_changes_after_sync():
    ex = ExpanderInputs()
    _stable(ex, _mask([SELECTOR_BITS[5]]), 0)
    events = _kinds(_stable(ex, _mask([SELECTOR_BITS[5], MECH_KEY_BITS["PLAN"]]),
                            _mask([JOY_PUSH_BIT, GB_BITS["A"]])))
    assert ("mech_key", "PLAN", None) in events
    assert ("joystick", "push_edge", True) in events
    assert ("gb_button", "A", True) in events
    events = _kinds(_stable(ex, _mask([SELECTOR_BITS[5]]), 0))
    assert ("gb_button", "A", False) in events
    assert not any(k == "mech_key" for k, _, _ in events)  # release is not a press


def test_rotary_between_positions_keeps_the_last_one():
    ex = ExpanderInputs()
    _stable(ex, _mask([SELECTOR_BITS[0]]), 0)
    assert _kinds(_stable(ex, 0, 0)) == []  # break-before-make gap
    assert _kinds(_stable(ex, _mask([SELECTOR_BITS[0], SELECTOR_BITS[1]]), 0)) == []  # two closed: ignore
    assert ("rotary", "selector", "2") in _kinds(_stable(ex, _mask([SELECTOR_BITS[1]]), 0))


def test_one_frame_glitch_is_ignored():
    ex = ExpanderInputs()
    _stable(ex, 0, 0)
    assert ex.update(_mask([MECH_KEY_BITS["CLD"]]), 0) == []
    assert ex.update(0, 0) == []


# -- analog ---------------------------------------------------------------------

def test_axis_deadzone_is_exactly_zero_and_full_throw_is_one():
    assert axis(0.52, 0.5, 0.12) == 0.0
    assert axis(1.0, 0.5, 0.12) == 1.0
    assert axis(0.0, 0.5, 0.12) == -1.0


def test_joystick_edges_fire_once_until_recentred():
    a = AnalogInputs()
    first = _kinds(a.update(1.0, 0.5, None))
    assert ("joystick", "edge", {"right"}) in first
    held = _kinds(a.update(1.0, 0.5, None))
    assert not any(n == "edge" for _, n, _ in held)
    a.update(0.5, 0.5, None)
    assert ("joystick", "edge", {"right"}) in _kinds(a.update(1.0, 0.5, None))


def test_joystick_invert_and_volume_smoothing():
    a = AnalogInputs({"invert_y": True})
    axis_ev = [e for e in a.update(0.5, 0.0, 0.0) if e.name == "axis"][0]
    assert axis_ev.value == (0.0, 1.0)
    vol = [e for e in a.update(0.5, 0.5, 1.0) if e.kind == "volume"][0]
    assert 0.0 < vol.value < 1.0
