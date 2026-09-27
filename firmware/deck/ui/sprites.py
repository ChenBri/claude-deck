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
    "N": (96, 58, 36),      # coffee brown
    "U": (70, 96, 168),     # book cover blue
    "P": (168, 92, 60),     # terracotta pot
    "D": (60, 120, 70),     # dark leaf green
    "M": (236, 228, 200),   # moon
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


# Eyes sit on rows 7-8: left eye is cells 5-7, right eye 8-10, pupils drawn
# as K on the chosen column of each eye (the base grid looks right).
_EYE_ROWS = (7, 8)
_EYES = ((5, 6, 7), (8, 9, 10))
_PUPIL_COLUMN = {"left": 0, "center": 1, "right": 2}


def _face_overrides(look: str = "right", closed: bool = False) -> dict[tuple[int, int], str]:
    overrides: dict[tuple[int, int], str] = {}
    for eye in _EYES:
        for x in eye:
            if closed:
                overrides[(x, 7)] = "L"
                overrides[(x, 8)] = "B"
                continue
            for y in _EYE_ROWS:
                overrides[(x, y)] = "C"
        if closed:
            continue
        column = eye[_PUPIL_COLUMN.get(look, 1)]  # up/down look straight on
        rows = (8,) if look == "down" else (7,) if look == "up" else _EYE_ROWS
        for y in rows:
            overrides[(column, y)] = "K"
    return overrides


def mascot_idle(blink: bool = False) -> pygame.Surface:
    return _grid_to_surface(_BODY, _face_overrides(closed=True) if blink else {})


def mascot_face(look: str = "right", closed: bool = False, mouth: str | None = None) -> pygame.Surface:
    """look: 'left' | 'center' | 'right' | 'up' | 'down'. mouth as in mascot_mouth."""
    rows = list(_BODY)
    if mouth is not None:
        rows[11] = _mouth_row(mouth)
    return _grid_to_surface(rows, _face_overrides(look, closed))


def _mouth_row(shape: str) -> str:
    line = list(_BODY[11])
    if shape == "smile":
        line[6], line[7], line[8], line[9] = "R", "R", "R", "R"
    elif shape == "open":
        line[7], line[8] = "K", "K"
    elif shape == "question":
        line[7], line[8] = "R", "R"
    return "".join(line)


def mascot_mouth(shape: str) -> pygame.Surface:
    """shape: 'smile' | 'flat' | 'open' | 'question'."""
    rows = list(_BODY)
    rows[11] = _mouth_row(shape)
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


# Props for the mascot-life scenes (ui/scenes/life.py). Same 4px cell as the
# mascot so everything in a room shares one pixel grid.

def mug() -> pygame.Surface:
    return _grid_to_surface([
        "BBBBB.",
        "BWNWB.",
        "BWWWBB",
        "BWWWB.B",
        "BWWWBB.",
        ".BBB...",
    ])


def book(flip: bool = False) -> pygame.Surface:
    """Open book seen from the front; flip shows the right page mid-turn."""
    rows = [
        "BBBBBBBBBBB",
        "BWWWWBWWWWB",
        "BWKKWBWKKWB",
        "BWWWWBWWWWB",
        "BWKKWBWKKWB",
        "BUUUUUUUUUB",
    ]
    if flip:
        rows = [
            "BBBBBBBB...",
            "BWWWWBWB...",
            "BWKKWBWB...",
            "BWWWWBWB...",
            "BWKKWBWB...",
            "BUUUUUUUB..",
        ]
    return _grid_to_surface(rows)


def plant() -> pygame.Surface:
    return _grid_to_surface([
        ".G.D.",
        "GDGDG",
        ".DGD.",
        "..D..",
        "PPPPP",
        ".PPP.",
        ".PPP.",
    ])


def moon() -> pygame.Surface:
    return _grid_to_surface([
        ".MMM.",
        "MMM..",
        "MM...",
        "MMM..",
        ".MMM.",
    ])
