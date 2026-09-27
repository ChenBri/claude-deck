from deck.hwtest import HardwareTest
from deck.panel.base import InputEvent, LAMPS


def test_single_push_does_not_exit_double_push_does():
    test = HardwareTest()
    assert test.observe(InputEvent("encoder", "push_down"), now=1.0)
    assert not test.exit_requested
    test.observe(InputEvent("encoder", "push_down"), now=2.0)
    assert not test.exit_requested
    test.observe(InputEvent("encoder", "push_down"), now=2.3)
    assert test.exit_requested


def test_records_positional_inputs_without_clicking():
    test = HardwareTest()
    assert not test.observe(InputEvent("toggle", "MUTE", True), now=0.0)
    assert not test.observe(InputEvent("rotary", "effort", "HIGH"), now=0.0)
    assert not test.observe(InputEvent("rotary", "selector", "3"), now=0.0)
    assert not test.observe(InputEvent("volume", "level", 0.5), now=0.0)
    assert test.toggles["MUTE"] is True
    assert test.effort == "HIGH" and test.selector == "3" and test.volume == 0.5


def test_momentary_presses_flash_then_fade():
    test = HardwareTest()
    assert test.observe(InputEvent("button", "APPROVE"), now=10.0)
    assert test.flashing("APPROVE", 10.1)
    assert not test.flashing("APPROVE", 11.0)


def test_encoder_counts_both_ways():
    test = HardwareTest()
    for name in ("cw", "cw", "cw", "ccw"):
        test.observe(InputEvent("encoder", name), now=0.0)
    assert test.encoder_count == 2


def test_outputs_exercise_one_thing_at_a_time_starting_with_first_lamp():
    test = HardwareTest()
    out = test.outputs(now=100.0, pixel_count=30)
    assert out["lamps"][LAMPS[0]] == 1.0
    assert sum(out["lamps"].values()) == 1.0
    assert all(v == 0.0 for v in out["meters"].values())
    assert len(out["pixels"]) == 30


def test_pixel_chase_lights_exactly_one_pixel():
    test = HardwareTest()
    test.outputs(now=0.0, pixel_count=30)
    # lamps + leds + meters = 5*0.6 + 2*0.6 + 2*2.0 = 8.2s, chase runs after
    out = test.outputs(now=9.0, pixel_count=30)
    lit = [p for p in out["pixels"] if p != (0, 0, 0)]
    assert len(lit) == 1
