"""Game Boy / Game Boy Color emulator, one of the icons on the home screen.
Runs PyBoy headless and blits its frame buffer straight onto the deck's own
GB_CANVAS_WIDTH x GB_CANVAS_HEIGHT canvas (native GB resolution) instead of
the 160x120 canvas every other scene shares - ui.render.compose_output scales
whatever size it is handed to fit the physical panel, letterboxed, so this
needs no special casing there.

ROMs are never shipped in this repo: see firmware/roms/README.md. Drop your
own legally-dumped .gb/.gbc files there, or point DECK_ROMS_DIR elsewhere.
Save states live under ${DECK_VAR}/gb_saves/, one per ROM.

Audio goes through deck.audio.chiptune, which owns the mixer: PyBoy's raw
stereo samples are queued onto a channel chiptune reserves so the app's
audio and the deck's own event blips never fight over the same channel, and
respect the MUTE toggle the same way.
"""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pygame

from deck.audio import chiptune
from deck.panel.base import GB_CANVAS_HEIGHT, GB_CANVAS_WIDTH
from deck.ui.gfx import clear, draw_text
from deck.ui.scenes.base import Context, Scene

ROMS_DIR = Path(os.environ.get("DECK_ROMS_DIR", str(Path(__file__).resolve().parents[3] / "roms")))
ROM_EXTENSIONS = (".gb", ".gbc")
VISIBLE_ROWS = 6

# 4194304 Hz master clock / 70224 cycles per frame, the exact DMG/CGB rate.
# tick() doesn't pace itself to real time (it'll run flat out, thousands of
# fps, if called in a tight loop), so this scene ticks it in step with real
# elapsed time itself, capped so a lagged frame can't spiral into catch-up.
GB_FRAME_SECONDS = 70224 / 4194304
MAX_CATCHUP_TICKS = 4

_GB_BUTTON_NAMES = {"A": "a", "B": "b", "START": "start", "SELECT": "select"}


def _list_roms() -> list[Path]:
    if not ROMS_DIR.is_dir():
        return []
    return sorted(p for p in ROMS_DIR.iterdir() if p.suffix.lower() in ROM_EXTENSIONS)


class GameBoyScene(Scene):
    """Joystick is the d-pad, A/B/START/SELECT are dedicated buttons,
    encoder rotate scrolls the rom picker, encoder push loads a rom or
    pauses/resumes a running one - mirrors Snake/Tetris's use of the
    encoder push for the same job."""

    def __init__(self) -> None:
        self._pyboy = None
        self._rom_path: Path | None = None
        self._state_path: Path | None = None
        self._picker_index = 0
        self._held_dpad: set[str] = set()
        self._paused = False
        self._error: str | None = None
        self._tick_accum = 0.0

    def on_exit(self, ctx: Context) -> None:
        self._save()

    def _save_dir(self) -> Path:
        path = Path(os.environ.get("DECK_VAR", "./var/deck")) / "gb_saves"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _save(self) -> None:
        if self._pyboy is not None and self._state_path is not None:
            with open(self._state_path, "wb") as f:
                self._pyboy.save_state(f)

    def _load(self, rom_path: Path) -> None:
        from pyboy import PyBoy  # deferred: only this app needs the dependency

        self._save()
        state_path = self._save_dir() / (rom_path.stem + ".state")
        try:
            pyboy = PyBoy(
                str(rom_path), window="null", sound_emulated=True, sound_sample_rate=chiptune.SAMPLE_RATE
            )
            if state_path.exists():
                with open(state_path, "rb") as f:
                    pyboy.load_state(f)
        except Exception as exc:  # a bad or unsupported dump shouldn't crash the deck
            self._error = str(exc)[:40]
            return
        self._pyboy = pyboy
        self._rom_path = rom_path
        self._state_path = state_path
        self._held_dpad = set()
        self._paused = False
        self._error = None
        self._tick_accum = 0.0

    def _handle_picker_input(self, ctx: Context) -> None:
        roms = _list_roms()
        if not roms:
            return
        self._picker_index %= len(roms)
        edge = ctx.inputs.get("encoder_edge")
        if edge == "cw":
            self._picker_index = (self._picker_index + 1) % len(roms)
        elif edge == "ccw":
            self._picker_index = (self._picker_index - 1) % len(roms)
        if ctx.inputs.get("encoder_push_edge", False):
            self._load(roms[self._picker_index])

    def _handle_running_input(self, ctx: Context) -> None:
        if ctx.inputs.get("encoder_push_edge", False):
            self._paused = not self._paused
            if self._paused:
                self._save()
        if self._paused:
            return

        jx, jy = ctx.inputs.get("joystick", (0, 0))
        wanted: set[str] = set()
        if jx < 0:
            wanted.add("left")
        elif jx > 0:
            wanted.add("right")
        if jy < 0:
            wanted.add("up")
        elif jy > 0:
            wanted.add("down")
        for direction in wanted - self._held_dpad:
            self._pyboy.button_press(direction)
        for direction in self._held_dpad - wanted:
            self._pyboy.button_release(direction)
        self._held_dpad = wanted

        held = ctx.inputs.get("gb_buttons", frozenset())
        for label, gb_name in _GB_BUTTON_NAMES.items():
            if label in held:
                self._pyboy.button_press(gb_name)
            else:
                self._pyboy.button_release(gb_name)

        # Advance in step with real elapsed time rather than once per drawn
        # frame: our own render loop runs at 20-30fps, well under the GB's
        # ~59.7fps, so a single tick() per draw would play the game in slow
        # motion. Collect every catch-up tick's audio and queue it as one
        # chunk so playback stays continuous instead of one Sound per tick.
        self._tick_accum = min(self._tick_accum + ctx.dt, GB_FRAME_SECONDS * MAX_CATCHUP_TICKS)
        audio_chunks = []
        while self._tick_accum >= GB_FRAME_SECONDS:
            self._pyboy.tick()
            audio_chunks.append(self._pyboy.sound.ndarray.copy())
            self._tick_accum -= GB_FRAME_SECONDS
        if audio_chunks:
            combined = audio_chunks[0] if len(audio_chunks) == 1 else np.concatenate(audio_chunks, axis=0)
            chiptune.queue_gb_audio((combined.astype(np.int16) << 8).tobytes())

    def draw(self, canvas: pygame.Surface, ctx: Context) -> None:
        if self._pyboy is None:
            self._handle_picker_input(ctx)
            self._draw_picker(canvas)
            return

        self._handle_running_input(ctx)
        frame = pygame.image.frombuffer(
            self._pyboy.screen.ndarray.tobytes(), (GB_CANVAS_WIDTH, GB_CANVAS_HEIGHT), "RGBA"
        )
        canvas.blit(frame, (0, 0))
        if self._paused:
            cx, cy = canvas.get_width() // 2, canvas.get_height() // 2
            pygame.draw.rect(canvas, (10, 8, 8), (cx - 30, cy - 6, 60, 16))
            draw_text(canvas, "paused", (cx - 24, cy), size=9)

    def _draw_picker(self, canvas: pygame.Surface) -> None:
        clear(canvas, color=(14, 14, 18))
        draw_text(canvas, "GAME BOY", (4, 2), size=10, color=(224, 122, 42))
        roms = _list_roms()
        y = 20
        if self._error:
            draw_text(canvas, "load failed:", (4, y), size=8, color=(220, 90, 80))
            draw_text(canvas, self._error, (4, y + 12), size=7, color=(180, 180, 180))
            y += 28
        if not roms:
            draw_text(canvas, "no roms found", (4, y), size=8, color=(170, 170, 170))
            draw_text(canvas, "drop .gb/.gbc files in", (4, y + 12), size=7, color=(140, 140, 140))
            draw_text(canvas, "firmware/roms", (4, y + 24), size=7, color=(140, 140, 140))
            return
        top = max(0, min(self._picker_index - 2, max(0, len(roms) - VISIBLE_ROWS)))
        for i in range(top, min(top + VISIBLE_ROWS, len(roms))):
            focused = i == self._picker_index
            color = (255, 210, 140) if focused else (170, 170, 170)
            prefix = ">" if focused else " "
            draw_text(canvas, f"{prefix} {roms[i].stem}"[:26], (4, y), size=8, color=color)
            y += 12
        draw_text(canvas, "rotate: pick  push: load", (4, canvas.get_height() - 10), size=7, color=(120, 120, 120))
