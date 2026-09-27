import os
import subprocess

os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from deck.main import App
from deck.menu import Menu
from deck.radio import RFKILL, Radio
from deck.state import Deck
from tests.test_real_panel import _panel


class FakeRun:
    def __init__(self, returncode=0):
        self.calls = []
        self.returncode = returncode

    def __call__(self, cmd, **kw):
        self.calls.append(cmd)
        return subprocess.CompletedProcess(cmd, self.returncode)


def test_radio_runs_exactly_the_sudoers_commands():
    run = FakeRun()
    radio = Radio(run)
    assert radio.set_wifi(True) and radio.set_wifi(False)
    assert run.calls == [
        ["sudo", "-n", RFKILL, "unblock", "wifi"],
        ["sudo", "-n", RFKILL, "block", "wifi"],
    ]
    sudoers = open(os.path.join(os.path.dirname(__file__), "..", "..", "deploy", "setup.sh")).read()
    assert f"NOPASSWD: {RFKILL} block wifi, {RFKILL} unblock wifi" in sudoers


def test_radio_failure_is_reported_not_raised():
    def missing(cmd, **kw):
        raise FileNotFoundError(cmd[0])

    assert not Radio(missing).set_wifi(True)
    assert not Radio(FakeRun(returncode=1)).set_wifi(True)


def _app(tmp_path, radio, wifi):
    menu = Menu(tmp_path / "settings.yaml")
    menu.settings["wifi"] = wifi
    return App(_panel()[0], Deck(), menu, use_link=False, radio=radio)


def test_saved_setting_is_applied_at_start_up(tmp_path):
    run = FakeRun()
    app = _app(tmp_path, Radio(run), wifi=True)
    assert run.calls == [["sudo", "-n", RFKILL, "unblock", "wifi"]]
    assert app.wifi_on


def test_refused_rfkill_puts_the_setting_back(tmp_path):
    app = _app(tmp_path, Radio(FakeRun(returncode=1)), wifi=True)
    assert not app.wifi_on
    assert app.menu.settings["wifi"] is False
    assert Menu(tmp_path / "settings.yaml").settings["wifi"] is False


def test_simulator_keeps_the_setting_without_a_radio(tmp_path):
    assert _app(tmp_path, None, wifi=True).wifi_on
