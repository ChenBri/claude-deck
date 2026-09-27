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

# theme -> (waveform, amplitude scale, event name -> list of (frequency_hz, duration_s)
# notes played in sequence). Picked from Settings; "classic" is the original set.
THEMES = {
    "classic": ("square", 1.0, {
        "blocked": [(440.0, 0.08), (330.0, 0.12)],
        "finished": [(523.0, 0.08), (659.0, 0.08), (784.0, 0.14)],
        "error": [(220.0, 0.10), (196.0, 0.10), (174.0, 0.18)],
        "task_start": [(392.0, 0.06), (523.0, 0.08)],
        "subagent_spawn": [(659.0, 0.05), (784.0, 0.05)],
        "tick": [(880.0, 0.03)],
    }),
    "soft": ("triangle", 0.8, {
        "blocked": [(330.0, 0.12), (262.0, 0.18)],
        "finished": [(392.0, 0.10), (494.0, 0.10), (587.0, 0.20)],
        "error": [(196.0, 0.16), (147.0, 0.24)],
        "task_start": [(294.0, 0.08), (392.0, 0.10)],
        "subagent_spawn": [(494.0, 0.06), (587.0, 0.06)],
        "tick": [(660.0, 0.03)],
    }),
    "arcade": ("pulse25", 0.9, {
        "blocked": [(784.0, 0.04), (0.0, 0.03), (784.0, 0.04), (0.0, 0.03), (587.0, 0.10)],
        "finished": [(523.0, 0.04), (659.0, 0.04), (784.0, 0.04), (1047.0, 0.04), (1319.0, 0.12)],
        "error": [(392.0, 0.05), (370.0, 0.05), (349.0, 0.05), (330.0, 0.05), (311.0, 0.18)],
        "task_start": [(523.0, 0.03), (784.0, 0.03), (1047.0, 0.05)],
        "subagent_spawn": [(1047.0, 0.03), (1319.0, 0.03), (1568.0, 0.04)],
        "tick": [(1319.0, 0.02)],
    }),
    "minimal": ("triangle", 0.6, {
        "blocked": [(523.0, 0.06)],
        "finished": [(784.0, 0.06)],
        "error": [(220.0, 0.08)],
        "task_start": [(659.0, 0.03)],
        "subagent_spawn": [(988.0, 0.02)],
        "tick": [(1047.0, 0.015)],
    }),
}
DEFAULT_THEME = "classic"

_muted = False
_volume = 1.0
_theme = DEFAULT_THEME
_ready = False
_sounds: dict[str, pygame.mixer.Sound] = {}
_gb_channel: pygame.mixer.Channel | None = None


def _wave_value(waveform: str, phase: float) -> float:
    if waveform == "triangle":
        return 4 * phase - 1 if phase < 0.5 else 3 - 4 * phase
    if waveform == "pulse25":
        return 1.0 if phase < 0.25 else -1.0
    return 1.0 if phase < 0.5 else -1.0


def _tone(freq: float, duration: float, waveform: str = "square", amplitude: float = 1.0) -> array.array:
    """freq 0 is a rest: silence for the duration."""
    n = int(SAMPLE_RATE * duration)
    samples = array.array("h", [0]) * (n * 2)  # stereo interleaved, L == R
    if freq <= 0 or n == 0:
        return samples
    period = SAMPLE_RATE / freq
    peak = _AMPLITUDE * amplitude
    for i in range(n):
        value = int(peak * _wave_value(waveform, (i % period) / period))
        samples[2 * i] = value
        samples[2 * i + 1] = value
    # short linear fade at the tail to avoid a click between notes
    fade = min(200, n)
    for i in range(fade):
        scaled = int(samples[2 * (n - 1 - i)] * (i / fade))
        samples[2 * (n - 1 - i)] = scaled
        samples[2 * (n - 1 - i) + 1] = scaled
    return samples


def _build_event(notes, waveform: str, amplitude: float) -> pygame.mixer.Sound:
    combined = array.array("h")
    for freq, duration in notes:
        combined.extend(_tone(freq, duration, waveform, amplitude))
    return pygame.mixer.Sound(buffer=combined.tobytes())


def _load_theme(name: str) -> None:
    waveform, amplitude, events = THEMES[name]
    _sounds.clear()
    for event, notes in events.items():
        _sounds[event] = _build_event(notes, waveform, amplitude)


def init() -> None:
    global _ready, _gb_channel
    if _ready:
        return
    pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=2)
    pygame.mixer.set_num_channels(9)
    pygame.mixer.set_reserved(1)  # channel 0: Game Boy streaming only, see queue_gb_audio
    _gb_channel = pygame.mixer.Channel(_GB_CHANNEL_INDEX)
    _ready = True
    _load_theme(_theme)


def set_theme(name: str) -> None:
    """Unknown names fall back to the default, so a hand-edited settings.yaml
    with a typo still makes sound rather than going silent."""
    global _theme
    _theme = name if name in THEMES else DEFAULT_THEME
    if _ready:
        _load_theme(_theme)


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
