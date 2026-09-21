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
from deck.audio import chiptune
from deck.menu import GAME_ACTIONS, Menu
from deck.panel.base import Panel
from deck.state import LAMP, Deck, State
from deck.ui.render import SceneManager, new_canvas
from deck.ui.scenes.base import Context
from deck.ui.scenes.menu import draw_menu

BOOT_SECONDS = 3.0  # trimmed way down from the real ~25s Pi boot for desktop dev
LONG_PRESS_SECONDS = 1.5


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
        self.active_game: str | None = None
        self._encoder_down_at: float | None = None
        self._boot_started = time.monotonic()

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

    def _on_mech_key(self, ev, frame_inputs: dict) -> None:
        frame_inputs.setdefault("mech_keys", set()).add(ev.name)
        if self.link is not None:
            self.link.send_action("mech_key", name=ev.name)

    def _on_toggle(self, ev, frame_inputs: dict) -> None:
        if ev.name == "MUTE":
            chiptune.set_muted(ev.value)
        elif ev.name == "AUTO_ACCEPT" and self.link is not None:
            self.link.send_action("toggle", name="AUTO_ACCEPT", value=ev.value)
        # NIGHT is read straight off the panel's toggle state when dimming lamps/pixels.

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
        if self.active_game is not None:
            frame_inputs["encoder_push_edge"] = True
            return
        if self.menu.open:
            item = self.menu.current_item()
            if item.key in GAME_ACTIONS:
                self.active_game = GAME_ACTIONS[item.key]
                self.menu.open = False
                return
        self.menu.activate()

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
            self.deck.tick(now)

            booting = (now - self._boot_started) < BOOT_SECONDS
            if self.active_game and self.deck.current_state(now) is not State.IDLE:
                self.active_game = None  # a live session takes over the screen again

            if self.menu.open:
                draw_menu(self.canvas, self.menu)
            else:
                session = self.deck.active_session()
                ctx = Context(
                    now=now,
                    dt=dt,
                    deck=self.deck,
                    session=session,
                    tool_name=session.last_tool if session else "",
                    tool_target=session.last_target if session else "",
                    idle_info=self.idle_info,
                    inputs=frame_inputs,
                )
                self.scene_manager.draw(self.canvas, ctx, booting=booting, game=self.active_game)

            self._update_indicators(now)
            self.panel.present(self.canvas)

    def _update_indicators(self, now: float) -> None:
        state = self.deck.current_state(now)
        lamp_name = LAMP.get(state)
        for name in ("READY", "WORKING", "BLOCKED", "DONE", "LINK"):
            if name == "LINK":
                self.panel.set_lamp(name, 1.0 if self.deck.link_alive else 0.0)
            else:
                self.panel.set_lamp(name, 1.0 if lamp_name == name else 0.0)

        self.panel.set_button_led("APPROVE", self.deck.approve_button_live(now))
        self.panel.set_button_led("DENY", state == State.BLOCKED_PERMISSION)


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
