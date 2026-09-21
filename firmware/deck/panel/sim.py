"""SimPanel: the whole front panel in a pygame window on the desktop. Draws
lamps, needles, halo/underglow, buttons, toggles, rotary switch, encoder,
mech keys and joystick, and turns mouse clicks / key presses into the same
InputEvents the real GPIO/I2C reads would produce.

The screen area runs the exact same render.compose_output() as RealPanel.
"""
from __future__ import annotations

import math

import pygame

from deck.panel.base import (
    BUTTON_LEDS,
    LAMPS,
    MECH_KEYS,
    METERS,
    PIXEL_COUNT,
    Panel,
    InputEvent,
)
from deck.ui import gfx
from deck.ui.render import OUTPUT_HEIGHT, OUTPUT_WIDTH, compose_output

WINDOW_W, WINDOW_H = 700, 560

LAMP_COLORS = {
    "READY": (70, 210, 100),
    "WORKING": (240, 170, 40),
    "BLOCKED": (220, 60, 50),
    "DONE": (100, 160, 235),
    "LINK": (80, 220, 220),
}

BEZEL_POS = (60, 30)

_ARROW_TO_AXIS = {
    pygame.K_LEFT: (-1, 0),
    pygame.K_RIGHT: (1, 0),
    pygame.K_UP: (0, -1),
    pygame.K_DOWN: (0, 1),
}
_ARROW_TO_EDGE = {
    pygame.K_LEFT: "left",
    pygame.K_RIGHT: "right",
    pygame.K_UP: "up",
    pygame.K_DOWN: "down",
}
_MECH_KEY_BINDINGS = {
    pygame.K_F1: "CLD",
    pygame.K_F2: "NEW",
    pygame.K_F3: "PLAN",
    pygame.K_F4: "MIC",
}
_TOGGLE_BINDINGS = {
    pygame.K_F5: "MUTE",
    pygame.K_F6: "NIGHT",
    pygame.K_F7: "AUTO_ACCEPT",
}
_ROTARY_BINDINGS = {
    pygame.K_1: "1", pygame.K_2: "2", pygame.K_3: "3",
    pygame.K_4: "4", pygame.K_5: "5", pygame.K_0: "ALL",
}


class SimPanel(Panel):
    def __init__(self) -> None:
        pygame.display.init()
        pygame.font.init()
        self._window = pygame.display.set_mode((WINDOW_W, WINDOW_H))
        pygame.display.set_caption("claude-deck simulator")
        self._clock = pygame.time.Clock()

        self._lamps = {name: 0.0 for name in LAMPS}
        self._meters = {name: 0.0 for name in METERS}
        self._pixels = [(0, 0, 0)] * PIXEL_COUNT
        self._button_leds = {name: False for name in BUTTON_LEDS}
        self._toggles = {"MUTE": False, "NIGHT": False, "AUTO_ACCEPT": False}
        self._selector = "ALL"  # matches Deck's own default so the drawn rotary isn't a lie at boot
        self._panic_latched = False
        self._closed = False
        self._encoder_mouse_down = False

        self._hitboxes = self._build_hitboxes()

    @property
    def closed(self) -> bool:
        return self._closed

    # -- layout -----------------------------------------------------------

    def _build_hitboxes(self):
        boxes = {}
        bx, by = BEZEL_POS
        lamp_y = by + OUTPUT_HEIGHT + 24
        for i, name in enumerate(LAMPS):
            boxes[("lamp", name)] = pygame.Rect(bx + i * 52, lamp_y, 20, 20)

        meter_x = bx + OUTPUT_WIDTH + 60
        for i, name in enumerate(METERS):
            boxes[("meter", name)] = pygame.Rect(meter_x + i * 100, by + 10, 80, 80)

        button_y = lamp_y + 56
        boxes[("button", "APPROVE")] = pygame.Rect(bx + 20, button_y, 34, 34)
        boxes[("button", "DENY")] = pygame.Rect(bx + 90, button_y, 34, 34)
        boxes[("panic", "panic")] = pygame.Rect(bx + 170, button_y - 5, 44, 44)

        toggle_y = button_y + 60
        for i, name in enumerate(("MUTE", "NIGHT", "AUTO_ACCEPT")):
            boxes[("toggle", name)] = pygame.Rect(bx + i * 70, toggle_y, 50, 20)

        rotary_y = toggle_y + 46
        for i, pos in enumerate(("1", "2", "3", "4", "5", "ALL")):
            boxes[("rotary", pos)] = pygame.Rect(bx + i * 44, rotary_y, 26, 26)

        side_x = meter_x
        boxes[("encoder", "encoder")] = pygame.Rect(side_x, button_y, 44, 44)
        for i, name in enumerate(MECH_KEYS):
            boxes[("mech_key", name)] = pygame.Rect(side_x + 60 + i * 40, button_y + 5, 30, 30)
        boxes[("joystick", "joystick")] = pygame.Rect(side_x, toggle_y, 70, 70)
        return boxes

    # -- Panel interface ----------------------------------------------------

    def set_lamp(self, name: str, level: float) -> None:
        self._lamps[name] = max(0.0, min(1.0, level))

    def set_meter(self, name: str, level: float) -> None:
        self._meters[name] = max(0.0, min(1.0, level))

    def set_pixels(self, colors) -> None:
        self._pixels = list(colors)

    def set_button_led(self, name: str, on: bool) -> None:
        self._button_leds[name] = on

    def present(self, canvas: pygame.Surface) -> None:
        self._window.fill((26, 22, 20))
        self._draw_bezel_and_screen(canvas)
        self._draw_lamps()
        self._draw_meters()
        self._draw_pixels()
        self._draw_buttons()
        self._draw_panic()
        self._draw_toggles()
        self._draw_rotary()
        self._draw_encoder()
        self._draw_mech_keys()
        self._draw_joystick()
        pygame.display.flip()
        self._clock.tick(30)

    def poll_inputs(self) -> list[InputEvent]:
        events: list[InputEvent] = []
        mouse_downs = []
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self._closed = True
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                mouse_downs.append(e.pos)
            elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
                if self._encoder_mouse_down:
                    self._encoder_mouse_down = False
                    events.append(InputEvent("encoder", "push_up"))
            elif e.type == pygame.KEYDOWN:
                events.extend(self._handle_keydown(e.key))
            elif e.type == pygame.KEYUP and e.key == pygame.K_RETURN:
                events.append(InputEvent("encoder", "push_up"))

        for pos in mouse_downs:
            events.extend(self._handle_click(pos))

        keys = pygame.key.get_pressed()
        ax = (1 if keys[pygame.K_RIGHT] else -1 if keys[pygame.K_LEFT] else 0)
        ay = (1 if keys[pygame.K_DOWN] else -1 if keys[pygame.K_UP] else 0)
        events.append(InputEvent("joystick", "axis", (ax, ay)))
        return events

    def close(self) -> None:
        pygame.display.quit()

    # -- input helpers ------------------------------------------------------

    def _handle_keydown(self, key) -> list[InputEvent]:
        out = []
        if key in _ARROW_TO_EDGE:
            out.append(InputEvent("joystick", "edge", {_ARROW_TO_EDGE[key]}))
        elif key == pygame.K_SPACE:
            out.append(InputEvent("joystick", "push_edge", True))
        elif key in _MECH_KEY_BINDINGS:
            out.append(InputEvent("mech_key", _MECH_KEY_BINDINGS[key]))
        elif key in _TOGGLE_BINDINGS:
            name = _TOGGLE_BINDINGS[key]
            self._toggles[name] = not self._toggles[name]
            out.append(InputEvent("toggle", name, self._toggles[name]))
        elif key in _ROTARY_BINDINGS:
            self._selector = _ROTARY_BINDINGS[key]
            out.append(InputEvent("rotary", "selector", self._selector))
        elif key == pygame.K_a:
            out.append(InputEvent("button", "APPROVE"))
        elif key == pygame.K_d:
            out.append(InputEvent("button", "DENY"))
        elif key == pygame.K_x:
            self._panic_latched = not self._panic_latched
            out.append(InputEvent("panic", "panic", self._panic_latched))
        elif key == pygame.K_LEFTBRACKET:
            out.append(InputEvent("encoder", "ccw"))
        elif key == pygame.K_RIGHTBRACKET:
            out.append(InputEvent("encoder", "cw"))
        elif key == pygame.K_RETURN:
            out.append(InputEvent("encoder", "push_down"))
        return out

    def _handle_click(self, pos) -> list[InputEvent]:
        for (kind, name), rect in self._hitboxes.items():
            if not rect.collidepoint(pos):
                continue
            if kind == "button":
                return [InputEvent("button", name)]
            if kind == "panic":
                self._panic_latched = not self._panic_latched
                return [InputEvent("panic", "panic", self._panic_latched)]
            if kind == "toggle":
                self._toggles[name] = not self._toggles[name]
                return [InputEvent("toggle", name, self._toggles[name])]
            if kind == "rotary":
                self._selector = name
                return [InputEvent("rotary", "selector", name)]
            if kind == "encoder":
                self._encoder_mouse_down = True
                return [InputEvent("encoder", "push_down")]
            if kind == "mech_key":
                return [InputEvent("mech_key", name)]
        return []

    # -- drawing --------------------------------------------------------------

    def _draw_bezel_and_screen(self, canvas: pygame.Surface) -> None:
        bx, by = BEZEL_POS
        bezel = pygame.Rect(bx - 6, by - 6, OUTPUT_WIDTH + 12, OUTPUT_HEIGHT + 12)
        pygame.draw.rect(self._window, (10, 8, 8), bezel, border_radius=8)
        output = compose_output(canvas)
        self._window.blit(output, BEZEL_POS)

    def _draw_lamps(self) -> None:
        for name, rect in ((n, r) for (k, n), r in self._hitboxes.items() if k == "lamp"):
            level = self._lamps[name]
            base = LAMP_COLORS[name]
            color = tuple(int(c * (0.15 + 0.85 * level)) for c in base)
            pygame.draw.circle(self._window, color, rect.center, 10)
            pygame.draw.circle(self._window, (0, 0, 0), rect.center, 10, 1)
            gfx.draw_text(self._window, name, (rect.x - 6, rect.bottom + 2), size=8, color=(180, 180, 180))

    def _draw_meters(self) -> None:
        for name, rect in ((n, r) for (k, n), r in self._hitboxes.items() if k == "meter"):
            center = rect.center
            radius = rect.width // 2
            pygame.draw.circle(self._window, (30, 30, 32), center, radius)
            pygame.draw.circle(self._window, (90, 90, 96), center, radius, 1)
            angle = math.radians(210 - 240 * self._meters[name])
            end = (center[0] + radius * 0.85 * math.cos(angle), center[1] - radius * 0.85 * math.sin(angle))
            pygame.draw.line(self._window, (240, 170, 40), center, end, 2)
            gfx.draw_text(self._window, name, (rect.x, rect.bottom + 2), size=8, color=(180, 180, 180))

    def _draw_pixels(self) -> None:
        bx, by = BEZEL_POS
        halo_count = PIXEL_COUNT * 2 // 3
        underglow_count = PIXEL_COUNT - halo_count
        cx, cy = bx + OUTPUT_WIDTH // 2, by + OUTPUT_HEIGHT // 2
        rx, ry = OUTPUT_WIDTH // 2 + 14, OUTPUT_HEIGHT // 2 + 14
        for i in range(halo_count):
            angle = 2 * math.pi * i / halo_count
            pos = (cx + rx * math.cos(angle), cy + ry * math.sin(angle))
            pygame.draw.circle(self._window, self._pixels[i], pos, 3)
        underglow_y = by + OUTPUT_HEIGHT + 10
        for i in range(underglow_count):
            x = bx + i * (OUTPUT_WIDTH // max(underglow_count - 1, 1))
            pygame.draw.circle(self._window, self._pixels[halo_count + i], (x, underglow_y), 3)

    def _draw_buttons(self) -> None:
        for name in BUTTON_LEDS:
            rect = self._hitboxes[("button", name)]
            lit = self._button_leds[name]
            ring = (70, 210, 100) if name == "APPROVE" else (220, 60, 50)
            fill = ring if lit else (50, 50, 52)
            pygame.draw.circle(self._window, fill, rect.center, rect.width // 2)
            pygame.draw.circle(self._window, ring, rect.center, rect.width // 2, 2)
            gfx.draw_text(self._window, name, (rect.x - 4, rect.bottom + 2), size=8, color=(180, 180, 180))

    def _draw_panic(self) -> None:
        rect = self._hitboxes[("panic", "panic")]
        color = (120, 20, 16) if self._panic_latched else (200, 40, 32)
        pygame.draw.circle(self._window, color, rect.center, rect.width // 2)
        pygame.draw.circle(self._window, (20, 8, 8), rect.center, rect.width // 2, 2)
        gfx.draw_text(self._window, "PANIC", (rect.x - 6, rect.bottom + 2), size=8, color=(180, 180, 180))

    def _draw_toggles(self) -> None:
        for name in ("MUTE", "NIGHT", "AUTO_ACCEPT"):
            rect = self._hitboxes[("toggle", name)]
            on = self._toggles[name]
            pygame.draw.rect(self._window, (50, 50, 52), rect, border_radius=10)
            knob_x = rect.right - 10 if on else rect.left + 10
            pygame.draw.circle(self._window, (70, 210, 100) if on else (120, 120, 124), (knob_x, rect.centery), 8)
            gfx.draw_text(self._window, name, (rect.x, rect.bottom + 2), size=7, color=(180, 180, 180))

    def _draw_rotary(self) -> None:
        for pos in ("1", "2", "3", "4", "5", "ALL"):
            rect = self._hitboxes[("rotary", pos)]
            active = self._selector == pos
            color = (240, 170, 40) if active else (50, 50, 52)
            pygame.draw.circle(self._window, color, rect.center, rect.width // 2)
            pygame.draw.circle(self._window, (90, 90, 96), rect.center, rect.width // 2, 1)
            gfx.draw_text(self._window, pos, (rect.x + 2, rect.y + 6), size=8, color=(20, 20, 20) if active else (180, 180, 180))

    def _draw_encoder(self) -> None:
        rect = self._hitboxes[("encoder", "encoder")]
        pygame.draw.circle(self._window, (60, 60, 64), rect.center, rect.width // 2)
        pygame.draw.circle(self._window, (140, 140, 144), rect.center, rect.width // 2, 2)
        gfx.draw_text(self._window, "ENC", (rect.x + 8, rect.bottom + 2), size=8, color=(180, 180, 180))

    def _draw_mech_keys(self) -> None:
        for name in MECH_KEYS:
            rect = self._hitboxes[("mech_key", name)]
            pygame.draw.rect(self._window, (60, 60, 64), rect, border_radius=4)
            pygame.draw.rect(self._window, (140, 140, 144), rect, 1, border_radius=4)
            gfx.draw_text(self._window, name, (rect.x - 2, rect.bottom + 2), size=7, color=(180, 180, 180))

    def _draw_joystick(self) -> None:
        rect = self._hitboxes[("joystick", "joystick")]
        pygame.draw.rect(self._window, (40, 40, 44), rect, border_radius=6)
        keys = pygame.key.get_pressed()
        ax = (1 if keys[pygame.K_RIGHT] else -1 if keys[pygame.K_LEFT] else 0)
        ay = (1 if keys[pygame.K_DOWN] else -1 if keys[pygame.K_UP] else 0)
        knob = (rect.centerx + ax * 18, rect.centery + ay * 18)
        pygame.draw.circle(self._window, (224, 122, 42), knob, 10)
        gfx.draw_text(self._window, "JOY", (rect.x + 4, rect.bottom + 2), size=8, color=(180, 180, 180))
