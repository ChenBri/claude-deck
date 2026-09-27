import pytest

from deck.hid import HOTKEYS, HidKeyboard
from deck.panel.base import InputEvent
from deck.panel.hw import pca9685
from deck.panel.hw.inputs import SELECTOR_BITS
from deck.panel.real import METER_CHANNELS, RealPanel
from tests.fakes import FakeGpio, FakeI2C, FakeSPI


def _panel():
    bus, spi, gpio = FakeI2C(), FakeSPI(), FakeGpio()
    # all switches open: pins read high
    for addr in (0x20, 0x21):
        bus.regs.setdefault(addr, {}).update({0x12: 0xFF, 0x13: 0xFF})
    return RealPanel({}, bus=bus, spi=spi, gpio=gpio, display=False), bus, spi, gpio


def _channel(bus, ch):
    return [bus.regs[0x40][pca9685.LED0_ON_L + 4 * ch + i] for i in range(4)]


def test_meters_are_inverted_for_the_pull_up():
    panel, bus, _, _ = _panel()
    panel.set_meter("CONTEXT", 0.0)
    panel.set_meter("FIVE_HOUR", 1.0)
    panel.present(None)
    assert _channel(bus, METER_CHANNELS["CONTEXT"]) == pca9685.channel_registers(1.0)  # sink fully: needle down
    assert _channel(bus, METER_CHANNELS["FIVE_HOUR"]) == pca9685.channel_registers(0.0)


def test_lamps_sink_directly_and_pixels_reach_the_strip():
    panel, bus, spi, _ = _panel()
    panel.set_lamp("BLOCKED", 1.0)
    panel.set_pixels([(10, 20, 30)] * 30)
    panel.present(None)
    assert _channel(bus, 2) == pca9685.channel_registers(1.0)
    assert len(spi.frames) == 1


def test_close_parks_meters_at_zero_not_pegged():
    panel, bus, _, gpio = _panel()
    panel.close()
    for ch in METER_CHANNELS.values():
        assert _channel(bus, ch) == pca9685.channel_registers(1.0)
    assert gpio.closed


def test_poll_merges_gpio_expander_and_analog_events():
    panel, bus, _, gpio = _panel()
    gpio.pending = [InputEvent("button", "APPROVE")]
    bus.regs[0x20][0x12] = 0xFF & ~(1 << SELECTOR_BITS[5])  # ALL closed
    first = panel.poll_inputs()
    assert ("button", "APPROVE") in [(e.kind, e.name) for e in first]
    second = panel.poll_inputs()  # expander needs two matching frames
    assert any(e.kind == "rotary" and e.value == "ALL" for e in second)
    assert any(e.kind == "joystick" and e.name == "axis" for e in second)


def test_hid_only_ever_writes_f13_to_f20_and_releases():
    reports = []
    kb = HidKeyboard(writer=reports.append)
    kb.tap("APPROVE")
    assert reports == [bytes([0, 0, 0x68, 0, 0, 0, 0, 0]), bytes(8)]
    assert all(0x68 <= code <= 0x6F for code in HOTKEYS.values())
    with pytest.raises(KeyError):
        kb.tap("ENTER")


def test_hid_map_matches_the_daemon():
    from pathlib import Path
    import re

    source = (Path(__file__).parents[2] / "daemon" / "src" / "link" / "hotkeys.ts").read_text()
    daemon = dict(re.findall(r"(\w+): \"F(\d+)\"", source))
    for name, code in HOTKEYS.items():
        assert int(daemon[name]) == 13 + (code - 0x68), name
