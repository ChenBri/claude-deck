"""Chiptune blips, one per event, generated in code. No sample files.

Output goes to the default pygame mixer device: the desktop speakers in the
simulator, the MAX98357A I2S amp on the real panel. The MUTE toggle is
respected here, not by the caller, so nothing needs to remember to check it.
"""
from __future__ import annotations

import array

import pygame

SAMPLE_RATE = 44100
_AMPLITUDE = 12000

# name -> list of (frequency_hz, duration_s) notes played in sequence
_EVENTS = {
    "blocked": [(440.0, 0.08), (330.0, 0.12)],
    "finished": [(523.0, 0.08), (659.0, 0.08), (784.0, 0.14)],
    "error": [(220.0, 0.10), (196.0, 0.10), (174.0, 0.18)],
    "task_start": [(392.0, 0.06), (523.0, 0.08)],
    "subagent_spawn": [(659.0, 0.05), (784.0, 0.05)],
}

_muted = False
_ready = False
_sounds: dict[str, pygame.mixer.Sound] = {}


def _square_wave(freq: float, duration: float) -> array.array:
    n = int(SAMPLE_RATE * duration)
    period = SAMPLE_RATE / freq
    samples = array.array("h", [0] * n)
    for i in range(n):
        phase = (i % period) / period
        samples[i] = _AMPLITUDE if phase < 0.5 else -_AMPLITUDE
    # short linear fade at the tail to avoid a click between notes
    fade = min(200, n)
    for i in range(fade):
        samples[n - 1 - i] = int(samples[n - 1 - i] * (i / fade))
    return samples


def _build_event(notes) -> pygame.mixer.Sound:
    combined = array.array("h")
    for freq, duration in notes:
        combined.extend(_square_wave(freq, duration))
    return pygame.mixer.Sound(buffer=combined.tobytes())


def init() -> None:
    global _ready
    if _ready:
        return
    pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=1)
    for name, notes in _EVENTS.items():
        _sounds[name] = _build_event(notes)
    _ready = True


def set_muted(muted: bool) -> None:
    global _muted
    _muted = muted


def play(event: str) -> None:
    if _muted or not _ready:
        return
    sound = _sounds.get(event)
    if sound is not None:
        sound.play()
