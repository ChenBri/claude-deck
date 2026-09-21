"""Code-defined pixel grids for the mascot, rendered to pygame surfaces at
build/import time. Each grid is a list of rows of single-char color keys;
"." is transparent. Frames are small and hand-authored here; if the look
needs polish, export a frame to PNG and touch it up in Piskel, then paste
the corrected grid back.

The mascot is an original starburst silhouette, not Anthropic artwork.
"""
from __future__ import annotations

import pygame

# Shared palette. Warm CRT phosphor tones: orange body, cream highlight.
PALETTE = {
    ".": None,
    "B": (40, 24, 16),      # outline
    "O": (224, 122, 42),    # body orange
    "L": (255, 178, 92),    # light orange / highlight
    "C": (255, 232, 196),   # cream (eyes, glow)
    "K": (24, 16, 12),      # near-black (pupils)
    "R": (214, 64, 48),     # red (mouth / alert)
    "G": (120, 200, 140),   # green (confetti)
    "Y": (240, 210, 90),    # yellow (confetti / spark)
    "W": (235, 235, 235),   # white (cloud / sign)
}

SCALE = 4  # each grid cell -> SCALE x SCALE pixels in the sprite sheet

# 16x16 starburst mascot, body only, arms/mouth vary per frame via overlays.
_BODY = [
    "................",
    ".......BB.......",
    "......BOOB......",
    ".....BOOOOB.....",
    "....BOOOOOOB....",
    "...BOOLLLLOOB...",
    "..BOOLLCCLLOOB..",
    ".BOOLCCKCCKLLOB.",
    ".BOOLCCKCCKLLOB.",
    "..BOOLLCCLLOOB..",
    "...BOOOOOOOOB...",
    "....BOO--OOB....",
    ".....BOOOOB.....",
    "......BOOB......",
    ".......BB.......",
    "................",
]


def _grid_to_surface(rows: list[str], overrides: dict[tuple[int, int], str] | None = None) -> pygame.Surface:
    overrides = overrides or {}
    h = len(rows)
    w = len(rows[0])
    surf = pygame.Surface((w * SCALE, h * SCALE), pygame.SRCALPHA)
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            ch = overrides.get((x, y), ch)
            if ch in ("-", "."):
                continue
            color = PALETTE.get(ch)
            if color is None:
                continue
            surf.fill(color, (x * SCALE, y * SCALE, SCALE, SCALE))
    return surf


def mascot_idle(blink: bool = False) -> pygame.Surface:
    overrides = {}
    if blink:
        overrides[(6, 7)] = "L"
        overrides[(9, 7)] = "L"
        overrides[(6, 8)] = "L"
        overrides[(9, 8)] = "L"
    return _grid_to_surface(_BODY, overrides)


def mascot_mouth(shape: str) -> pygame.Surface:
    """shape: 'smile' | 'flat' | 'open' | 'question'."""
    rows = list(_BODY)
    line = list(rows[11])
    if shape == "smile":
        line[6], line[7], line[8], line[9] = "R", "R", "R", "R"
    elif shape == "open":
        line[7], line[8] = "K", "K"
    elif shape == "question":
        line[7], line[8] = "R", "R"
    rows[11] = "".join(line)
    return _grid_to_surface(rows)


def confetti_particle(color: str = "Y") -> pygame.Surface:
    surf = pygame.Surface((SCALE, SCALE), pygame.SRCALPHA)
    surf.fill(PALETTE.get(color, PALETTE["Y"]))
    return surf


def storm_cloud() -> pygame.Surface:
    rows = [
        "................",
        "................",
        "......WWWW......",
        "....WWWWWWWW....",
        "...WWWWWWWWWW...",
        "..WWWWWWWWWWWW..",
        "..WWWWWWWWWWWW..",
        "...WWWWWWWWWW...",
        "................",
        ".....B..B.......",
        "....B..B..B.....",
        "...B..B..B......",
        "................",
        "................",
        "................",
        "................",
    ]
    return _grid_to_surface(rows)
