"""What main.py forwards to the daemon and the HID gadget, and when it
must not: the approval path, so it gets real tests."""
import os
import time

os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pytest

from deck.main import App
from deck.menu import Menu
from deck.panel.base import InputEvent
from deck.state import Deck
from tests.test_real_panel import _panel


class Recorder:
    def __init__(self):
        self.actions = []
        self.keys = []

    def send_action(self, kind, **kw):
        self.actions.append(kind)

    def tap(self, name):
        self.keys.append(name)


@pytest.fixture
def app(tmp_path):
    panel = _panel()[0]
    rec = Recorder()
    a = App(panel, Deck(), Menu(tmp_path / "settings.yaml"), use_link=False, hid=rec)
    a.link = rec
    return a, rec


def _pending(app, approvable=True):
    app.deck.registry.handle("s1", "SessionStart", now=time.monotonic())
    app.deck.registry.handle(
        "s1", "Notification", now=time.monotonic(), variant="permission",
        request_id="r1", tool="Bash", target="ls", approvable=approvable,
    )


def test_live_approve_goes_out_as_key_and_action(app):
    a, rec = app
    _pending(a)
    a._on_button(InputEvent("button", "APPROVE"), {})
    assert rec.keys == ["APPROVE"] and rec.actions == ["approve"]


def test_dead_approve_sends_nothing(app):
    a, rec = app
    _pending(a, approvable=False)  # denylisted
    a._on_button(InputEvent("button", "APPROVE"), {})
    assert rec.keys == [] and rec.actions == []


def test_nothing_pending_sends_nothing(app):
    a, rec = app
    a._on_button(InputEvent("button", "DENY"), {})
    assert rec.keys == [] and rec.actions == []


def test_hardware_test_never_forwards_presses(app):
    a, rec = app
    _pending(a)
    a.current_app = "hwtest"
    a._on_button(InputEvent("button", "APPROVE"), {})
    a._on_mech_key(InputEvent("mech_key", "NEW"), {})
    assert rec.keys == [] and rec.actions == []


def test_mech_keys_in_a_game_stay_in_the_game(app):
    a, rec = app
    a.current_app = "tetris"
    inputs = {}
    a._on_mech_key(InputEvent("mech_key", "NEW"), inputs)
    assert inputs["mech_keys"] == {"NEW"}
    assert rec.keys == [] and rec.actions == []
    a.current_app = None
    a._on_mech_key(InputEvent("mech_key", "NEW"), {})
    assert rec.keys == ["NEW"] and rec.actions == ["mech_key"]


def test_panic_sends_its_key_only_on_latch(app):
    a, rec = app
    a._on_panic(InputEvent("panic", "panic", True), {})
    a._on_panic(InputEvent("panic", "panic", False), {})
    assert rec.keys == ["PANIC"]
    assert rec.actions == ["panic", "panic"]
