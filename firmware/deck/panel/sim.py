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

WINDOW_W, WINDOW_H = 900, 600   # was 700x560; the preview bezel and side controls both grew with the bigger panel
SIM_ZOOM = 1.6  # desktop-only magnification; real hardware has no equivalent, it's a fixed panel

# The real panel is 1366x768 (DECISIONS.md #20) - too big to lay out at
# 1:1 in a desktop dev window. PREVIEW_WIDTH/HEIGHT is what the rest of
# this file's layout math uses instead; compose_output()'s true
# OUTPUT_WIDTH x OUTPUT_HEIGHT result gets scaled down to this size only
# at the final blit, in _draw_bezel_and_screen.
PREVIEW_SCALE = 0.35
PREVIEW_WIDTH = round(OUTPUT_WIDTH * PREVIEW_SCALE)
PREVIEW_HEIGHT = round(OUTPUT_HEIGHT * PREVIEW_SCALE)

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
_GB_BUTTON_BINDINGS = {
    pygame.K_z: "A",
    pygame.K_c: "B",
    pygame.K_BACKSPACE: "START",
    pygame.K_RSHIFT: "SELECT",
}
_EFFORT_BINDINGS = {
    pygame.K_F8: "LOW",
    pygame.K_F9: "MED",
    pygame.K_F10: "HIGH",
    pygame.K_F11: "MAX",
}
VOLUME_STEP = 0.02  # per poll (~30fps), held -/= ramps the knob over ~1.7s end to end


class SimPanel(Panel):
    def __init__(self) -> None:
        pygame.display.init()
        pygame.font.init()
        # Everything draws onto this native-resolution surface; present()
        # zooms the whole thing into the actual OS window so desktop text
        # is readable without changing any real-hardware-shared layout math.
        self._native = pygame.Surface((WINDOW_W, WINDOW_H))
        self._display = pygame.display.set_mode(
            (round(WINDOW_W * SIM_ZOOM), round(WINDOW_H * SIM_ZOOM))
        )
        pygame.display.set_caption("claude-deck simulator")
        self._clock = pygame.time.Clock()

        self._lamps = {name: 0.0 for name in LAMPS}
        self._meters = {name: 0.0 for name in METERS}
        self._pixels = [(0, 0, 0)] * PIXEL_COUNT
        self._button_leds = {name: 0.0 for name in BUTTON_LEDS}
        self._toggles = {"MUTE": False, "NIGHT": False, "AUTO_ACCEPT": False}
        self._selector = "ALL"  # matches Deck's own default so the drawn rotary isn't a lie at boot
        self._effort = "MED"
        self._volume = 1.0
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
        lamp_y = by + PREVIEW_HEIGHT + 24
        for i, name in enumerate(LAMPS):
            boxes[("lamp", name)] = pygame.Rect(bx + i * 52, lamp_y, 20, 20)

        meter_x = bx + PREVIEW_WIDTH + 60
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
        # Same diamond A/B offset a real Game Boy uses, not a row: B low-left,
        # A high-right. START/SELECT are a smaller pair off to the side, real
        # switches too (see DECISIONS.md #55) but a lot less prominent.
        gb_x, gb_y = side_x + 90, toggle_y + 5
        boxes[("gb_button", "A")] = pygame.Rect(gb_x + 40, gb_y, 30, 30)
        boxes[("gb_button", "B")] = pygame.Rect(gb_x, gb_y + 48, 30, 30)
        boxes[("gb_button", "SELECT")] = pygame.Rect(gb_x + 90, gb_y + 56, 18, 18)
        boxes[("gb_button", "START")] = pygame.Rect(gb_x + 135, gb_y + 56, 18, 18)

        effort_y = gb_y + 80
        for i, name in enumerate(("LOW", "MED", "HIGH", "MAX")):
            boxes[("effort", name)] = pygame.Rect(side_x + i * 36, effort_y, 26, 26)
        boxes[("volume", "volume")] = pygame.Rect(side_x + 170, effort_y - 5, 36, 36)
        return boxes

    # -- Panel interface ----------------------------------------------------

    def set_lamp(self, name: str, level: float) -> None:
        self._lamps[name] = max(0.0, min(1.0, level))

    def set_meter(self, name: str, level: float) -> None:
        self._meters[name] = max(0.0, min(1.0, level))

    def set_pixels(self, colors) -> None:
        self._pixels = list(colors)

    def set_button_led(self, name: str, level: float) -> None:
        self._button_leds[name] = max(0.0, min(1.0, level))

    def present(self, canvas: pygame.Surface) -> None:
        self._native.fill((26, 22, 20))
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
        self._draw_gb_buttons()
        self._draw_effort()
        self._draw_volume()
        zoomed = pygame.transform.scale(self._native, self._display.get_size())
        self._display.blit(zoomed, (0, 0))
        pygame.display.flip()
        self._clock.tick(30)

    def poll_inputs(self) -> list[InputEvent]:
        events: list[InputEvent] = []
        mouse_downs = []
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self._closed = True
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                # e.pos is in real (zoomed) window pixels; hitboxes are in
                # native coordinates, so unzoom before hit-testing.
                mouse_downs.append((e.pos[0] / SIM_ZOOM, e.pos[1] / SIM_ZOOM))
            elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
                if self._encoder_mouse_down:
                    self._encoder_mouse_down = False
                    events.append(InputEvent("encoder", "push_up"))
            elif e.type == pygame.KEYDOWN:
                events.extend(self._handle_keydown(e.key))
            elif e.type == pygame.KEYUP and e.key == pygame.K_RETURN:
                events.append(InputEvent("encoder", "push_up"))
            elif e.type == pygame.KEYUP and e.key in _GB_BUTTON_BINDINGS:
                events.append(InputEvent("gb_button", _GB_BUTTON_BINDINGS[e.key], False))

        for pos in mouse_downs:
            events.extend(self._handle_click(pos))

        keys = pygame.key.get_pressed()
        ax = (1 if keys[pygame.K_RIGHT] else -1 if keys[pygame.K_LEFT] else 0)
        ay = (1 if keys[pygame.K_DOWN] else -1 if keys[pygame.K_UP] else 0)
        events.append(InputEvent("joystick", "axis", (ax, ay)))

        # Volume knob: a real potentiometer reads continuously on hardware,
        # so this emits every poll too, not just on change - held -/= ramps
        # it, matching how a finger turning a real knob would.
        if keys[pygame.K_MINUS]:
            self._volume = max(0.0, self._volume - VOLUME_STEP)
        elif keys[pygame.K_EQUALS]:
            self._volume = min(1.0, self._volume + VOLUME_STEP)
        events.append(InputEvent("volume", "level", self._volume))
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
        elif key in _GB_BUTTON_BINDINGS:
            out.append(InputEvent("gb_button", _GB_BUTTON_BINDINGS[key], True))
        elif key in _TOGGLE_BINDINGS:
            name = _TOGGLE_BINDINGS[key]
            self._toggles[name] = not self._toggles[name]
            out.append(InputEvent("toggle", name, self._toggles[name]))
        elif key in _ROTARY_BINDINGS:
            self._selector = _ROTARY_BINDINGS[key]
            out.append(InputEvent("rotary", "selector", self._selector))
        elif key in _EFFORT_BINDINGS:
            self._effort = _EFFORT_BINDINGS[key]
            out.append(InputEvent("rotary", "effort", self._effort))
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
            if kind == "effort":
                self._effort = name
                return [InputEvent("rotary", "effort", name)]
            if kind == "encoder":
                self._encoder_mouse_down = True
                return [InputEvent("encoder", "push_down")]
            if kind == "mech_key":
                return [InputEvent("mech_key", name)]
        return []

    # -- drawing --------------------------------------------------------------

    def _draw_bezel_and_screen(self, canvas: pygame.Surface) -> None:
        bx, by = BEZEL_POS
        bezel = pygame.Rect(bx - 6, by - 6, PREVIEW_WIDTH + 12, PREVIEW_HEIGHT + 12)
        pygame.draw.rect(self._native, (10, 8, 8), bezel, border_radius=8)
        output = compose_output(canvas)
        preview = pygame.transform.smoothscale(output, (PREVIEW_WIDTH, PREVIEW_HEIGHT))
        self._native.blit(preview, BEZEL_POS)

    def _draw_lamps(self) -> None:
        for name, rect in ((n, r) for (k, n), r in self._hitboxes.items() if k == "lamp"):
            level = self._lamps[name]
            base = LAMP_COLORS[name]
            color = tuple(int(c * (0.15 + 0.85 * level)) for c in base)
            pygame.draw.circle(self._native, color, rect.center, 10)
            pygame.draw.circle(self._native, (0, 0, 0), rect.center, 10, 1)
            gfx.draw_text(self._native, name, (rect.x - 6, rect.bottom + 2), size=11, color=(180, 180, 180))

    def _draw_meters(self) -> None:
        for name, rect in ((n, r) for (k, n), r in self._hitboxes.items() if k == "meter"):
            center = rect.center
            radius = rect.width // 2
            pygame.draw.circle(self._native, (30, 30, 32), center, radius)
            pygame.draw.circle(self._native, (90, 90, 96), center, radius, 1)
            angle = math.radians(210 - 240 * self._meters[name])
            end = (center[0] + radius * 0.85 * math.cos(angle), center[1] - radius * 0.85 * math.sin(angle))
            pygame.draw.line(self._native, (240, 170, 40), center, end, 2)
            gfx.draw_text(self._native, name, (rect.x, rect.bottom + 2), size=11, color=(180, 180, 180))

    def _draw_pixels(self) -> None:
        bx, by = BEZEL_POS
        halo_count = PIXEL_COUNT * 2 // 3
        underglow_count = PIXEL_COUNT - halo_count
        cx, cy = bx + PREVIEW_WIDTH // 2, by + PREVIEW_HEIGHT // 2
        rx, ry = PREVIEW_WIDTH // 2 + 14, PREVIEW_HEIGHT // 2 + 14
        for i in range(halo_count):
            angle = 2 * math.pi * i / halo_count
            pos = (cx + rx * math.cos(angle), cy + ry * math.sin(angle))
            pygame.draw.circle(self._native, self._pixels[i], pos, 3)
        underglow_y = by + PREVIEW_HEIGHT + 10
        for i in range(underglow_count):
            x = bx + i * (PREVIEW_WIDTH // max(underglow_count - 1, 1))
            pygame.draw.circle(self._native, self._pixels[halo_count + i], (x, underglow_y), 3)

    def _draw_buttons(self) -> None:
        for name in BUTTON_LEDS:
            rect = self._hitboxes[("button", name)]
            level = self._button_leds[name]
            ring = (70, 210, 100) if name == "APPROVE" else (220, 60, 50)
            off = (50, 50, 52)
            fill = tuple(int(o + (r - o) * level) for o, r in zip(off, ring))
            pygame.draw.circle(self._native, fill, rect.center, rect.width // 2)
            pygame.draw.circle(self._native, ring, rect.center, rect.width // 2, 2)
            gfx.draw_text(self._native, name, (rect.x - 4, rect.bottom + 2), size=11, color=(180, 180, 180))

    def _draw_panic(self) -> None:
        rect = self._hitboxes[("panic", "panic")]
        color = (120, 20, 16) if self._panic_latched else (200, 40, 32)
        pygame.draw.circle(self._native, color, rect.center, rect.width // 2)
        pygame.draw.circle(self._native, (20, 8, 8), rect.center, rect.width // 2, 2)
        gfx.draw_text(self._native, "PANIC", (rect.x - 6, rect.bottom + 2), size=11, color=(180, 180, 180))

    def _draw_toggles(self) -> None:
        for name in ("MUTE", "NIGHT", "AUTO_ACCEPT"):
            rect = self._hitboxes[("toggle", name)]
            on = self._toggles[name]
            pygame.draw.rect(self._native, (50, 50, 52), rect, border_radius=10)
            knob_x = rect.right - 10 if on else rect.left + 10
            pygame.draw.circle(self._native, (70, 210, 100) if on else (120, 120, 124), (knob_x, rect.centery), 8)
            gfx.draw_text(self._native, name, (rect.x, rect.bottom + 2), size=10, color=(180, 180, 180))

    def _draw_rotary(self) -> None:
        for pos in ("1", "2", "3", "4", "5", "ALL"):
            rect = self._hitboxes[("rotary", pos)]
            active = self._selector == pos
            color = (240, 170, 40) if active else (50, 50, 52)
            pygame.draw.circle(self._native, color, rect.center, rect.width // 2)
            pygame.draw.circle(self._native, (90, 90, 96), rect.center, rect.width // 2, 1)
            gfx.draw_text(self._native, pos, (rect.x + 2, rect.y + 6), size=11, color=(20, 20, 20) if active else (180, 180, 180))

    def _draw_encoder(self) -> None:
        rect = self._hitboxes[("encoder", "encoder")]
        pygame.draw.circle(self._native, (60, 60, 64), rect.center, rect.width // 2)
        pygame.draw.circle(self._native, (140, 140, 144), rect.center, rect.width // 2, 2)
        gfx.draw_text(self._native, "ENC", (rect.x + 8, rect.bottom + 2), size=11, color=(180, 180, 180))

    def _draw_mech_keys(self) -> None:
        for name in MECH_KEYS:
            rect = self._hitboxes[("mech_key", name)]
            pygame.draw.rect(self._native, (60, 60, 64), rect, border_radius=4)
            pygame.draw.rect(self._native, (140, 140, 144), rect, 1, border_radius=4)
            gfx.draw_text(self._native, name, (rect.x - 2, rect.bottom + 2), size=10, color=(180, 180, 180))

    def _draw_joystick(self) -> None:
        rect = self._hitboxes[("joystick", "joystick")]
        pygame.draw.rect(self._native, (40, 40, 44), rect, border_radius=6)
        keys = pygame.key.get_pressed()
        ax = (1 if keys[pygame.K_RIGHT] else -1 if keys[pygame.K_LEFT] else 0)
        ay = (1 if keys[pygame.K_DOWN] else -1 if keys[pygame.K_UP] else 0)
        knob = (rect.centerx + ax * 18, rect.centery + ay * 18)
        pygame.draw.circle(self._native, (224, 122, 42), knob, 10)
        gfx.draw_text(self._native, "JOY", (rect.x + 4, rect.bottom + 2), size=11, color=(180, 180, 180))

    def _draw_gb_buttons(self) -> None:
        # Keyboard-only, like the joystick above: these hitboxes are drawn
        # for reference but not wired into _handle_click, since a mouse click
        # can't express "held" the way KEYDOWN/KEYUP can.
        pressed = pygame.key.get_pressed()
        for key, name in _GB_BUTTON_BINDINGS.items():
            rect = self._hitboxes[("gb_button", name)]
            held = pressed[key]
            pygame.draw.circle(self._native, (224, 122, 42) if held else (60, 60, 64), rect.center, rect.width // 2)
            pygame.draw.circle(self._native, (140, 140, 144), rect.center, rect.width // 2, 2)
            gfx.draw_text(self._native, name, (rect.x - 4, rect.bottom + 2), size=10, color=(180, 180, 180))

    def _draw_effort(self) -> None:
        for pos in ("LOW", "MED", "HIGH", "MAX"):
            rect = self._hitboxes[("effort", pos)]
            active = self._effort == pos
            color = (190, 120, 220) if active else (50, 50, 52)
            pygame.draw.circle(self._native, color, rect.center, rect.width // 2)
            pygame.draw.circle(self._native, (90, 90, 96), rect.center, rect.width // 2, 1)
            gfx.draw_text(self._native, pos[:2], (rect.x + 4, rect.y + 6), size=9, color=(20, 20, 20) if active else (180, 180, 180))
        first = self._hitboxes[("effort", "LOW")]
        gfx.draw_text(self._native, "EFFORT", (first.x, first.bottom + 2), size=10, color=(180, 180, 180))

    def _draw_volume(self) -> None:
        rect = self._hitboxes[("volume", "volume")]
        pygame.draw.circle(self._native, (60, 60, 64), rect.center, rect.width // 2)
        pygame.draw.circle(self._native, (140, 140, 144), rect.center, rect.width // 2, 2)
        angle = math.radians(210 - 240 * self._volume)
        end = (
            rect.centerx + rect.width * 0.35 * math.cos(angle),
            rect.centery - rect.width * 0.35 * math.sin(angle),
        )
        pygame.draw.line(self._native, (224, 122, 42), rect.center, end, 2)
        gfx.draw_text(self._native, "VOL", (rect.x + 2, rect.bottom + 2), size=10, color=(180, 180, 180))
