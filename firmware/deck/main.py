"""Event loop: entry point on the deck (--panel real) and for desktop
development (--panel sim). tools/replay.py drives the same Deck/Panel/menu
objects directly, feeding registry events on its own thread instead of
starting a DaemonLink.

    python -m deck.main --panel sim
"""
from __future__ import annotations

import argparse
import time

from deck import calibration
from deck import link as link_mod
from deck.apps import APPS
from deck.audio import chiptune
from deck.audio.cues import event_for_transition
from deck.calibration import CalibrationWizard
from deck.hid import HidKeyboard
from deck.hwtest import HardwareTest
from deck.menu import Menu, _get
from deck.panel.base import GB_CANVAS_HEIGHT, GB_CANVAS_WIDTH, METERS, PIXEL_COUNT, RAIL_HEIGHT, RAIL_WIDTH, Panel
from deck.screen import screen_level, wall_clock
from deck.state import LAMP, Deck, State
from deck.ui import rails
from deck.ui.pixels import pixels_for_state
from deck.ui.render import GAMES, SceneManager, new_canvas
from deck.ui.scenes.base import Context
from deck.ui.scenes.calibrate import draw_calibrate
from deck.ui.scenes.home import draw_home
from deck.ui.scenes.hwtest import draw_hwtest
from deck.ui.scenes.menu import draw_menu

DENYLIST_CATEGORIES = ("database", "destructive_fs_git", "infrastructure", "secrets")

BOOT_SECONDS = 3.0  # trimmed way down from the real ~25s boot for desktop dev
LONG_PRESS_SECONDS = 1.5
PRUNE_INTERVAL_SECONDS = 30.0

# Reached from Settings, and they return there rather than to home.
MAINTENANCE_APPS = ("hwtest", "calibrate")

# Apps may hold the screen in these states. OFFLINE is included so the
# hardware test and calibration work on the bench before the daemon is
# up; a session going live still takes the screen straight back.
APP_STATES = (State.IDLE, State.OFFLINE)


def build_panel(name: str, settings: dict) -> Panel:
    if name == "sim":
        from deck.panel.sim import SimPanel

        return SimPanel()
    if name == "real":
        from deck.panel.real import RealPanel

        return RealPanel(settings)
    raise ValueError(f"unknown panel backend {name!r}")


class App:
    def __init__(
        self, panel: Panel, deck: Deck, menu: Menu, use_link: bool = True, hid: HidKeyboard | None = None
    ) -> None:
        self.panel = panel
        # Real panel only: each press also goes out as its F13-F20 key, which
        # the daemon pairs with the HTTP action below before acting (SAFETY.md).
        self.hid = hid
        self.deck = deck
        self.menu = menu
        self.scene_manager = SceneManager()
        self.canvas = new_canvas()
        self.gb_canvas = new_canvas(GB_CANVAS_WIDTH, GB_CANVAS_HEIGHT)
        self.rails = (new_canvas(RAIL_WIDTH, RAIL_HEIGHT), new_canvas(RAIL_WIDTH, RAIL_HEIGHT))
        self._last_input_at = time.monotonic()
        self._last_volume: float | None = None
        self.idle_info: dict = {}
        # None: plain IDLE dashboard (or a live session's own scene). "home":
        # the app launcher. "settings", one of MAINTENANCE_APPS, or a key
        # from ui.render.GAMES: that app is showing.
        self.current_app: str | None = None
        self.hwtest = HardwareTest()
        self.calibrate = CalibrationWizard()
        self._hwtest_label = ""
        self._last_state: State | None = None
        self._last_subagents: tuple[str | None, int] = (None, 0)
        self.home_index = 0
        self.night_on = False
        self._gb_buttons_held: set[str] = set()
        self._encoder_down_at: float | None = None
        self._boot_started = time.monotonic()
        self._last_prune = time.monotonic()

        self.link = None
        if use_link:
            self.link = link_mod.DaemonLink(
                deck.registry,
                on_link_alive_change=deck.set_link_alive,
                on_idle_info=self._on_idle_info,
            )

        chiptune.init()
        chiptune.set_theme(str(menu.settings.get("sound_theme", chiptune.DEFAULT_THEME)))
        deck.idle_after_seconds = float(menu.settings.get("idle_after_seconds", deck.idle_after_seconds))

    def _on_idle_info(self, info: dict) -> None:
        self.idle_info = info

    def start(self) -> None:
        if self.link is not None:
            self.link.start()
            self._sync_denylist_settings()

    def _sync_denylist_settings(self) -> None:
        """Best-effort push of the deck's current denylist categories to the
        daemon, so a freshly (re)started daemon picks up whatever the
        encoder menu last set rather than falling back to its own defaults."""
        if self.link is None:
            return
        denylist = self.menu.settings.get("denylist", {})
        for category in DENYLIST_CATEGORIES:
            if category in denylist:
                self.link.send_action("denylist_toggle", category=category, value=bool(denylist[category]))

    def stop(self) -> None:
        if self.link is not None:
            self.link.stop()
        self.panel.close()

    # -- input handling -------------------------------------------------------

    def _is_touch(self, ev) -> bool:
        """True for a real hand on the panel. The joystick axis and the volume
        knob report every poll, so only movement counts for those."""
        if ev.kind == "joystick" and ev.name == "axis":
            return tuple(ev.value) != (0, 0)
        if ev.kind == "volume":
            moved = self._last_volume is not None and abs(ev.value - self._last_volume) > 0.02
            self._last_volume = ev.value
            return moved
        return True

    def _handle_events(self, events, frame_inputs: dict) -> None:
        for ev in events:
            if self._is_touch(ev):
                self._last_input_at = time.monotonic()
            if self.current_app == "hwtest" and self.hwtest.observe(ev, time.monotonic()):
                chiptune.play("tick")
            handler = getattr(self, f"_on_{ev.kind}", None)
            if handler is not None:
                handler(ev, frame_inputs)

    def _on_joystick(self, ev, frame_inputs: dict) -> None:
        if ev.name == "axis":
            frame_inputs["joystick"] = ev.value
        elif ev.name == "edge":
            frame_inputs.setdefault("joystick_edge", set()).update(ev.value)
        elif ev.name == "push_edge":
            frame_inputs["joystick_push_edge"] = True

    def _on_mech_key(self, ev, frame_inputs: dict) -> None:
        frame_inputs.setdefault("mech_keys", set()).add(ev.name)
        if self.current_app == "hwtest" or self.current_app in GAMES:
            return  # tested, or a game control (Tetris rotates and drops with these): not for Claude
        if self.hid is not None:
            self.hid.tap(ev.name)
        if self.link is not None:
            # PLAN needs to know which session's permission_mode the daemon
            # last saw, to compute how many Shift+Tab presses reach plan mode
            # (see daemon/src/guard.ts). Harmless for CLD/NEW/MIC, which ignore it.
            session = self.deck.active_session()
            self.link.send_action(
                "mech_key", name=ev.name, session_id=session.session_id if session else None
            )

    def _on_gb_button(self, ev, frame_inputs: dict) -> None:
        # Game Boy app input only, never forwarded to the daemon: ev.value is
        # True while held, False on release, so the Game Boy scene sees the
        # same continuous press/release state a real MCP23017 poll would give.
        if ev.value:
            self._gb_buttons_held.add(ev.name)
        else:
            self._gb_buttons_held.discard(ev.name)

    def _on_toggle(self, ev, frame_inputs: dict) -> None:
        if ev.name == "MUTE":
            chiptune.set_muted(ev.value)
        elif ev.name == "NIGHT":
            self.night_on = bool(ev.value)
        elif ev.name == "AUTO_ACCEPT" and self.link is not None:
            self.link.send_action("toggle", name="AUTO_ACCEPT", value=ev.value)

    def _brightness(self) -> float:
        """Dim factor for the PCA9685-driven indicators (lamps, button LEDs)
        under NIGHT mode. Never applied to set_meter(): those channels are
        the needle position itself, not a backlight, and dimming them would
        falsify the reading."""
        if not self.night_on:
            return 1.0
        return max(0.0, min(1.0, float(self.menu.settings.get("night_brightness", 0.2))))

    def _on_rotary(self, ev, frame_inputs: dict) -> None:
        if ev.name == "effort":
            if self.link is not None:
                self.link.send_action("effort_select", value=ev.value)
            return
        self.deck.set_selector(ev.value)

    def _on_volume(self, ev, frame_inputs: dict) -> None:
        # Purely local: the volume knob only ever affects this deck's own
        # audio output, no reason to round-trip it through the daemon.
        chiptune.set_volume(ev.value)

    def _on_button(self, ev, frame_inputs: dict) -> None:
        # Real hardware: the physical press itself emits F13/F14 over HID, and
        # the daemon's hotkeys.ts is the actual trigger (docs/SAFETY.md rule 1).
        # The simulator has no HID gadget to be faithful to, so it substitutes
        # this HTTP action; guard.ts verifies it against the same request id
        # either way.
        if self.current_app == "hwtest":
            return  # being tested, not pressed in anger: never forwarded
        session = self.deck.active_session()
        if session is None or session.pending is None:
            return
        if ev.name == "APPROVE" and not self.deck.approve_button_live():
            return  # stale, denylisted, or expired: dead button, per docs/SAFETY.md
        if self.hid is not None:
            self.hid.tap(ev.name)
        if self.link is not None:
            self.link.send_action(
                ev.name.lower(), session_id=session.session_id, request_id=session.pending.request_id
            )

    def _on_panic(self, ev, frame_inputs: dict) -> None:
        if ev.value and self.hid is not None:
            self.hid.tap("PANIC")
        if ev.value:
            self.deck.panic()
        else:
            self.deck.panic_release()
        if self.link is not None:
            self.link.send_action("panic", value=ev.value)

    def _on_encoder(self, ev, frame_inputs: dict) -> None:
        now = time.monotonic()
        if ev.name in ("cw", "ccw"):
            if self.current_app == "settings":
                self.menu.rotate(1 if ev.name == "cw" else -1)
            elif self.current_app == "calibrate":
                self.calibrate.rotate(1 if ev.name == "cw" else -1)
            else:
                frame_inputs["encoder_edge"] = ev.name  # e.g. the Game Boy rom picker
                # every detent this frame, not just the last: a fast turn sends several
                step = 1 if ev.name == "cw" else -1
                frame_inputs["encoder_steps"] = frame_inputs.get("encoder_steps", 0) + step
        elif ev.name == "push_down":
            self._encoder_down_at = now
        elif ev.name == "push_up":
            held = now - self._encoder_down_at if self._encoder_down_at is not None else 0.0
            self._encoder_down_at = None
            if held >= LONG_PRESS_SECONDS:
                self._shutdown()
            else:
                self._encoder_short_press(frame_inputs)

    def _encoder_short_press(self, frame_inputs: dict) -> None:
        if self.current_app in GAMES:
            frame_inputs["encoder_push_edge"] = True  # the game itself decides: pause, or retry if over
            return

        if self.current_app == "hwtest":
            return  # HardwareTest.observe already saw it; a double push exits

        if self.current_app == "calibrate":
            self.calibrate.push()
            if self.calibrate.finished:
                self.menu.settings["meter_cal"] = self.calibrate.curves
                self.menu.save()
                self.current_app = "settings"
            return

        if self.current_app == "settings":
            item = self.menu.current_item()
            if item.key == "EXIT":
                self.current_app = "home"
                return
            if item.key == "HWTEST":
                self.hwtest.reset()
                self.current_app = "hwtest"
                return
            if item.key == "CALIBRATE":
                self.calibrate.start(self.menu.settings.get("meter_cal", {}))
                self.current_app = "calibrate"
                return
            self.menu.activate()
            if item.key == "sound_theme":
                chiptune.set_theme(str(_get(self.menu.settings, item.key)))
                chiptune.play("finished")  # preview
            if item.key.startswith("denylist.") and self.link is not None:
                category = item.key.split(".", 1)[1]
                self.link.send_action(
                    "denylist_toggle", category=category, value=_get(self.menu.settings, item.key)
                )
            return

        if self.current_app == "home":
            app_id = APPS[self.home_index].id
            if app_id == "settings":
                self.menu.focus = 0
            self.current_app = app_id
            return

        # current_app is None: idle dashboard (or attract-mode snake), open the launcher
        self.current_app = "home"
        self.home_index = 0

    def _on_joystick_navigation(self, frame_inputs: dict) -> None:
        """Home-screen left/right and the universal "back" button. Kept
        separate from per-app input (which scenes read straight out of
        frame_inputs) because it changes which app is showing at all."""
        if self.current_app == "home":
            edges = frame_inputs.get("joystick_edge", ())
            if "left" in edges:
                self.home_index = (self.home_index - 1) % len(APPS)
            if "right" in edges:
                self.home_index = (self.home_index + 1) % len(APPS)

        if frame_inputs.get("joystick_push_edge") and self.current_app is not None:
            if self.current_app == "hwtest":
                return  # joystick push is one of the inputs under test
            if self.current_app in MAINTENANCE_APPS:
                self.current_app = "settings"  # calibrate: cancel, nothing saved
            else:
                self.current_app = None if self.current_app == "home" else "home"

    def _shutdown(self) -> None:
        # Real hardware: play the goodbye animation, then `sudo shutdown -h now`.
        # Desktop dev: just close the window.
        self.panel_should_quit = True

    # -- main loop --------------------------------------------------------------

    def run(self) -> None:
        last_now = time.monotonic()
        while not getattr(self.panel, "closed", False) and not getattr(self, "panel_should_quit", False):
            now = time.monotonic()
            dt = now - last_now
            last_now = now

            frame_inputs: dict = {"gb_buttons": frozenset(self._gb_buttons_held)}
            self._handle_events(self.panel.poll_inputs(), frame_inputs)
            self._on_joystick_navigation(frame_inputs)
            self.deck.tick(now)
            if now - self._last_prune >= PRUNE_INTERVAL_SECONDS:
                self._last_prune = now
                self.deck.registry.prune(now=now)

            booting = (now - self._boot_started) < BOOT_SECONDS
            if self.current_app == "hwtest" and self.hwtest.exit_requested:
                self.current_app = "settings"
            if self.current_app is not None and self.deck.current_state(now) not in APP_STATES:
                self.current_app = None  # a live session takes the screen back over
            if not booting:
                self._play_cues(now)

            if self.current_app == "settings":
                draw_menu(self.canvas, self.menu)
                canvas = self.canvas
            elif self.current_app == "home":
                draw_home(self.canvas, self.home_index)
                canvas = self.canvas
            elif self.current_app == "hwtest":
                draw_hwtest(self.canvas, self.hwtest, now, self._hwtest_label)
                canvas = self.canvas
            elif self.current_app == "calibrate":
                draw_calibrate(self.canvas, self.calibrate)
                canvas = self.canvas
            else:
                canvas = self.gb_canvas if self.current_app == "gameboy" else self.canvas
                session = self.deck.active_session()
                ctx = Context(
                    now=now,
                    dt=dt,
                    deck=self.deck,
                    session=session,
                    tool_name=session.last_tool if session else "",
                    tool_target=session.last_target if session else "",
                    tool_rate=session.tool_call_rate(now) if session else 0.0,
                    idle_info=self.idle_info,
                    inputs=frame_inputs,
                    settings=self.menu.settings,
                )
                game = self.current_app if self.current_app in GAMES else None
                self.scene_manager.draw(canvas, ctx, booting=booting, game=game)

            self._update_indicators(now)
            state = self.deck.current_state(now)
            clock = wall_clock(self.idle_info)
            if booting:
                for rail in self.rails:
                    rail.fill(rails.RAIL_BG)
            else:
                self._draw_rails(now, state, clock)
            level = screen_level(state, clock.hour, self.night_on, now - self._last_input_at, self.menu.settings)
            self.panel.present(canvas, self.rails, level)

    def _draw_rails(self, now: float, state: State, clock) -> None:
        left, right = self.rails
        rails.draw_left(left, clock, self.idle_info.get("weather"))
        session = self.deck.active_session()
        rails.draw_right(
            right,
            state,
            now,
            len(self.deck.registry.sessions),
            session.context_pct if session else 0.0,
            float(self.idle_info.get("five_hour_pct", 0.0)),
        )

    def _play_cues(self, now: float) -> None:
        state = self.deck.current_state(now)
        event = event_for_transition(self._last_state, state)
        self._last_state = state

        session = self.deck.active_session()
        subagents = (session.session_id, session.subagent_count) if session else (None, 0)
        if event is None and subagents[0] == self._last_subagents[0] and subagents[1] > self._last_subagents[1]:
            event = "subagent_spawn"
        self._last_subagents = subagents

        if event is not None:
            chiptune.play(event)

    def _set_meter(self, name: str, level: float) -> None:
        curve = self.menu.settings.get("meter_cal", {}).get(name)
        self.panel.set_meter(name, calibration.apply(level, curve))

    def _update_hwtest_indicators(self, now: float) -> None:
        # Raw duty on the meters, no calibration: bring-up comes before it.
        out = self.hwtest.outputs(now, PIXEL_COUNT)
        self._hwtest_label = out["label"]
        for name, level in out["lamps"].items():
            self.panel.set_lamp(name, level)
        for name, level in out["leds"].items():
            self.panel.set_button_led(name, level)
        for name, level in out["meters"].items():
            self.panel.set_meter(name, level)
        self.panel.set_pixels(out["pixels"])

    def _update_indicators(self, now: float) -> None:
        if self.current_app == "hwtest":
            self._update_hwtest_indicators(now)
            return
        state = self.deck.current_state(now)
        lamp_name = LAMP.get(state)
        brightness = self._brightness()
        for name in ("READY", "WORKING", "BLOCKED", "DONE", "LINK"):
            if name == "LINK":
                self.panel.set_lamp(name, brightness if self.deck.link_alive else 0.0)
            else:
                self.panel.set_lamp(name, brightness if lamp_name == name else 0.0)

        self.panel.set_backlight(brightness)
        self.panel.set_button_led("APPROVE", brightness if self.deck.approve_button_live(now) else 0.0)
        self.panel.set_button_led("DENY", brightness if state == State.BLOCKED_PERMISSION else 0.0)

        if self.current_app == "calibrate":
            for name in METERS:
                self.panel.set_meter(name, self.calibrate.drive() if name == self.calibrate.meter else 0.0)
        else:
            session = self.deck.active_session()
            self._set_meter("CONTEXT", session.context_pct if session else 0.0)
            self._set_meter("FIVE_HOUR", float(self.idle_info.get("five_hour_pct", 0.0)))

        self.panel.set_pixels(pixels_for_state(state, now, brightness, PIXEL_COUNT))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--panel", choices=["sim", "real"], default="sim")
    parser.add_argument("--no-link", action="store_true", help="skip starting the daemon link")
    args = parser.parse_args()

    menu = Menu()
    panel = build_panel(args.panel, menu.settings)
    hid = HidKeyboard() if args.panel == "real" else None
    deck = Deck(selector="ALL", idle_after_seconds=float(menu.settings.get("idle_after_seconds", 300)))
    app = App(panel, deck, menu, use_link=not args.no_link, hid=hid)
    app.start()
    try:
        app.run()
    finally:
        app.stop()


if __name__ == "__main__":
    main()
