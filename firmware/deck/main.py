"""Event loop: entry point on the Pi (--panel real) and for desktop
development (--panel sim). tools/replay.py drives the same Deck/Panel/menu
objects directly, feeding registry events on its own thread instead of
starting a DaemonLink.

    python -m deck.main --panel sim
"""
from __future__ import annotations

import argparse
import time

from deck import link as link_mod
from deck.apps import APPS
from deck.audio import chiptune
from deck.menu import Menu, _get
from deck.panel.base import PIXEL_COUNT, Panel
from deck.state import LAMP, Deck, State
from deck.ui.pixels import pixels_for_state
from deck.ui.render import GAMES, SceneManager, new_canvas
from deck.ui.scenes.base import Context
from deck.ui.scenes.home import draw_home
from deck.ui.scenes.menu import draw_menu

DENYLIST_CATEGORIES = ("database", "destructive_fs_git", "infrastructure", "secrets")

BOOT_SECONDS = 3.0  # trimmed way down from the real ~25s Pi boot for desktop dev
LONG_PRESS_SECONDS = 1.5
PRUNE_INTERVAL_SECONDS = 30.0


def build_panel(name: str) -> Panel:
    if name == "sim":
        from deck.panel.sim import SimPanel

        return SimPanel()
    if name == "real":
        from deck.panel.real import RealPanel

        return RealPanel()
    raise ValueError(f"unknown panel backend {name!r}")


class App:
    def __init__(self, panel: Panel, deck: Deck, menu: Menu, use_link: bool = True) -> None:
        self.panel = panel
        self.deck = deck
        self.menu = menu
        self.scene_manager = SceneManager()
        self.canvas = new_canvas()
        self.idle_info: dict = {}
        # None: plain IDLE dashboard (or a live session's own scene). "home":
        # the app launcher. "settings", or a key from ui.render.GAMES: that
        # app is showing.
        self.current_app: str | None = None
        self.home_index = 0
        self.night_on = False
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
        deck.idle_after_seconds = float(menu.settings.get("idle_after_seconds", deck.idle_after_seconds))

    def _on_idle_info(self, info: dict) -> None:
        self.idle_info = info

    def start(self) -> None:
        if self.link is not None:
            self.link.start()
            self._sync_denylist_settings()

    def _sync_denylist_settings(self) -> None:
        """Best-effort push of the Pi's current denylist categories to the
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

    def _handle_events(self, events, frame_inputs: dict) -> None:
        for ev in events:
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
        if self.link is not None:
            self.link.send_action("mech_key", name=ev.name)

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
        self.deck.set_selector(ev.value)

    def _on_button(self, ev, frame_inputs: dict) -> None:
        # Real hardware: the physical press itself emits F13/F14 over HID, and
        # the daemon's hotkeys.ts is the actual trigger (docs/SAFETY.md rule 1).
        # The simulator has no HID gadget to be faithful to, so it substitutes
        # this HTTP action; guard.ts verifies it against the same request id
        # either way.
        session = self.deck.active_session()
        if session is None or session.pending is None:
            return
        if ev.name == "APPROVE" and not self.deck.approve_button_live():
            return  # stale, denylisted, or expired: dead button, per docs/SAFETY.md
        if self.link is not None:
            self.link.send_action(
                ev.name.lower(), session_id=session.session_id, request_id=session.pending.request_id
            )

    def _on_panic(self, ev, frame_inputs: dict) -> None:
        if ev.value:
            self.deck.panic()
        else:
            self.deck.panic_release()
        if self.link is not None:
            self.link.send_action("panic", value=ev.value)

    def _on_encoder(self, ev, frame_inputs: dict) -> None:
        now = time.monotonic()
        if ev.name == "cw":
            self.menu.rotate(1)
        elif ev.name == "ccw":
            self.menu.rotate(-1)
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

        if self.current_app == "settings":
            item = self.menu.current_item()
            if item.key == "EXIT":
                self.current_app = "home"
                return
            self.menu.activate()
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

            frame_inputs: dict = {}
            self._handle_events(self.panel.poll_inputs(), frame_inputs)
            self._on_joystick_navigation(frame_inputs)
            self.deck.tick(now)
            if now - self._last_prune >= PRUNE_INTERVAL_SECONDS:
                self._last_prune = now
                self.deck.registry.prune(now=now)

            booting = (now - self._boot_started) < BOOT_SECONDS
            if self.current_app is not None and self.deck.current_state(now) is not State.IDLE:
                self.current_app = None  # a live session takes the screen back over

            if self.current_app == "settings":
                draw_menu(self.canvas, self.menu)
            elif self.current_app == "home":
                draw_home(self.canvas, self.home_index)
            else:
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
                )
                game = self.current_app if self.current_app in GAMES else None
                self.scene_manager.draw(self.canvas, ctx, booting=booting, game=game)

            self._update_indicators(now)
            self.panel.present(self.canvas)

    def _update_indicators(self, now: float) -> None:
        state = self.deck.current_state(now)
        lamp_name = LAMP.get(state)
        brightness = self._brightness()
        for name in ("READY", "WORKING", "BLOCKED", "DONE", "LINK"):
            if name == "LINK":
                self.panel.set_lamp(name, brightness if self.deck.link_alive else 0.0)
            else:
                self.panel.set_lamp(name, brightness if lamp_name == name else 0.0)

        self.panel.set_button_led("APPROVE", brightness if self.deck.approve_button_live(now) else 0.0)
        self.panel.set_button_led("DENY", brightness if state == State.BLOCKED_PERMISSION else 0.0)

        self.panel.set_pixels(pixels_for_state(state, now, brightness, PIXEL_COUNT))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--panel", choices=["sim", "real"], default="sim")
    parser.add_argument("--no-link", action="store_true", help="skip starting the daemon link")
    args = parser.parse_args()

    panel = build_panel(args.panel)
    menu = Menu()
    deck = Deck(selector="ALL", idle_after_seconds=float(menu.settings.get("idle_after_seconds", 300)))
    app = App(panel, deck, menu, use_link=not args.no_link)
    app.start()
    try:
        app.run()
    finally:
        app.stop()


if __name__ == "__main__":
    main()
