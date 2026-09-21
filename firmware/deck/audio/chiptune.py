"""Chiptune blips, one per event, generated in code. No sample files.

Output goes to the default pygame mixer device: the desktop speakers in the
simulator, the MAX98357A I2S amp on the real panel. The MUTE toggle and the
volume knob are both respected here, not by the caller, so nothing needs to
remember to check them.

Also owns the Game Boy app's audio: the mixer is stereo so PyBoy's raw
samples need no reshaping, and channel 0 is reserved so a running game's
streamed audio is never interrupted by an event blip stealing its channel.
"""
from __future__ import annotations

import array

import pygame

SAMPLE_RATE = 44100
_AMPLITUDE = 12000
_GB_CHANNEL_INDEX = 0

# name -> list of (frequency_hz, duration_s) notes played in sequence
_EVENTS = {
    "blocked": [(440.0, 0.08), (330.0, 0.12)],
    "finished": [(523.0, 0.08), (659.0, 0.08), (784.0, 0.14)],
    "error": [(220.0, 0.10), (196.0, 0.10), (174.0, 0.18)],
    "task_start": [(392.0, 0.06), (523.0, 0.08)],
    "subagent_spawn": [(659.0, 0.05), (784.0, 0.05)],
}

_muted = False
_volume = 1.0
_ready = False
_sounds: dict[str, pygame.mixer.Sound] = {}
_gb_channel: pygame.mixer.Channel | None = None


def _square_wave(freq: float, duration: float) -> array.array:
    n = int(SAMPLE_RATE * duration)
    period = SAMPLE_RATE / freq
    samples = array.array("h", [0]) * (n * 2)  # stereo interleaved, L == R
    for i in range(n):
        phase = (i % period) / period
        value = _AMPLITUDE if phase < 0.5 else -_AMPLITUDE
        samples[2 * i] = value
        samples[2 * i + 1] = value
    # short linear fade at the tail to avoid a click between notes
    fade = min(200, n)
    for i in range(fade):
        scaled = int(samples[2 * (n - 1 - i)] * (i / fade))
        samples[2 * (n - 1 - i)] = scaled
        samples[2 * (n - 1 - i) + 1] = scaled
    return samples


def _build_event(notes) -> pygame.mixer.Sound:
    combined = array.array("h")
    for freq, duration in notes:
        combined.extend(_square_wave(freq, duration))
    return pygame.mixer.Sound(buffer=combined.tobytes())


def init() -> None:
    global _ready, _gb_channel
    if _ready:
        return
    pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=2)
    pygame.mixer.set_num_channels(9)
    pygame.mixer.set_reserved(1)  # channel 0: Game Boy streaming only, see queue_gb_audio
    _gb_channel = pygame.mixer.Channel(_GB_CHANNEL_INDEX)
    for name, notes in _EVENTS.items():
        _sounds[name] = _build_event(notes)
    _ready = True


def set_muted(muted: bool) -> None:
    global _muted
    _muted = muted


def is_muted() -> bool:
    return _muted


def set_volume(level: float) -> None:
    """level is 0..1, straight off the volume knob (a real potentiometer
    into a spare ADS1115 channel on real hardware, see docs/HARDWARE.md).
    Independent of MUTE: the knob sets the level, MUTE is a hard override
    to silent regardless of where the knob sits."""
    global _volume
    _volume = max(0.0, min(1.0, level))


def play(event: str) -> None:
    if _muted or not _ready:
        return
    sound = _sounds.get(event)
    if sound is not None:
        sound.set_volume(_volume)
        sound.play()


def queue_gb_audio(stereo_int16_bytes: bytes) -> None:
    """Called once per drawn frame by the Game Boy app with however many
    emulated frames' worth of audio it produced since the last call, already
    stereo interleaved 16-bit to match the mixer format. Channel.queue()
    plays immediately if the channel is idle and gaplessly appends otherwise,
    so this doesn't need to track whether playback already started."""
    if not _ready or not stereo_int16_bytes:
        return
    _gb_channel.set_volume(0.0 if _muted else _volume)
    _gb_channel.queue(pygame.mixer.Sound(buffer=stereo_int16_bytes))
