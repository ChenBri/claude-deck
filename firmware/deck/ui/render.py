"""Scene compositor and the CRT post pass shared by every Panel backend."""
from __future__ import annotations

import pygame

from deck.panel.base import CANVAS_HEIGHT, CANVAS_WIDTH
from deck.state import State
from deck.ui.scenes.base import Context, Scene
from deck.ui.scenes.blocked import BlockedInputScene, BlockedPermissionScene
from deck.ui.scenes.boot import BootScene
from deck.ui.scenes.compacting import CompactingScene
from deck.ui.scenes.done import DoneScene
from deck.ui.scenes.error import ErrorScene
from deck.ui.scenes.gameboy import GameBoyScene
from deck.ui.scenes.idle import IdleScene
from deck.ui.scenes.interrupted import InterruptedScene
from deck.ui.scenes.offline import OfflineScene
from deck.ui.scenes.ready import ReadyScene
from deck.ui.scenes.snake import SnakeScene
from deck.ui.scenes.subagents import SubagentsScene
from deck.ui.scenes.tetris import TetrisScene
from deck.ui.scenes.working import WorkingScene

OUTPUT_SCALE = 2
OUTPUT_WIDTH = CANVAS_WIDTH * OUTPUT_SCALE
OUTPUT_HEIGHT = CANVAS_HEIGHT * OUTPUT_SCALE

_STATE_SCENES: dict[State, type[Scene]] = {
    State.READY: ReadyScene,
    State.WORKING: WorkingScene,
    State.SUBAGENTS: SubagentsScene,
    State.BLOCKED_PERMISSION: BlockedPermissionScene,
    State.BLOCKED_INPUT: BlockedInputScene,
    State.COMPACTING: CompactingScene,
    State.DONE: DoneScene,
    State.ERROR: ErrorScene,
    State.IDLE: IdleScene,
    State.OFFLINE: OfflineScene,
    State.INTERRUPTED: InterruptedScene,
}

GAMES: dict[str, type[Scene]] = {
    "snake": SnakeScene,
    "tetris": TetrisScene,
    "gameboy": GameBoyScene,
}


class SceneManager:
    """Picks the scene for the current state (or an active game) and keeps
    one instance alive per class so animation state survives frame to frame."""

    def __init__(self) -> None:
        self._instances: dict[type, Scene] = {}
        self._active: Scene | None = None
        self.boot = BootScene()

    def _get(self, cls: type[Scene]) -> Scene:
        scene = self._instances.get(cls)
        if scene is None:
            scene = cls()
            self._instances[cls] = scene
        return scene

    def draw(self, canvas: pygame.Surface, ctx: Context, booting: bool = False, game: str | None = None) -> None:
        if booting:
            self.boot.draw(canvas, ctx)
            return

        if game is not None:
            scene = self._get(GAMES[game])
        else:
            scene_cls = _STATE_SCENES.get(ctx.deck.current_state(ctx.now), ReadyScene)
            scene = self._get(scene_cls)

        if scene is not self._active:
            if self._active is not None:
                self._active.on_exit(ctx)
            scene.on_enter(ctx)
            self._active = scene

        scene.draw(canvas, ctx)


def new_canvas(width: int = CANVAS_WIDTH, height: int = CANVAS_HEIGHT) -> pygame.Surface:
    return pygame.Surface((width, height))


def compose_output(canvas: pygame.Surface) -> pygame.Surface:
    """Scale the logical canvas onto the physical OUTPUT_WIDTH x OUTPUT_HEIGHT
    panel, nearest-neighbour, and lay a light CRT pass (scanlines + a soft
    additive bloom) on top. Shared by SimPanel and RealPanel so the look is
    identical on the desktop and on the real display.

    The scale is derived from whatever size `canvas` happens to be, not
    hardcoded to CANVAS_WIDTH/HEIGHT: every scene shares the 160x120 logical
    canvas and gets an exact 2x fill, but the Game Boy app hands in its own
    160x144 (native GB resolution, see ui/scenes/gameboy.py) and gets the
    largest scale that still fits, letterboxed and centred.

    Bloom is tuned deliberately weak: at this resolution, small UI text like
    the ticker and settings menu, a wide/strong bloom radius smears glyph
    strokes into an unreadable glow well before it looks like a CRT. "Slight
    bloom" per docs/DECISIONS.md #28 means legible-but-warm, not blurred.
    """
    cw, ch = canvas.get_size()
    scale = min(OUTPUT_WIDTH / cw, OUTPUT_HEIGHT / ch)
    sw, sh = round(cw * scale), round(ch * scale)
    ox, oy = (OUTPUT_WIDTH - sw) // 2, (OUTPUT_HEIGHT - sh) // 2

    scaled = pygame.Surface((OUTPUT_WIDTH, OUTPUT_HEIGHT))
    scaled.blit(pygame.transform.scale(canvas, (sw, sh)), (ox, oy))

    bloom_small = pygame.transform.smoothscale(canvas, (max(cw // 2, 1), max(ch // 2, 1)))
    bloom = pygame.transform.smoothscale(bloom_small, (sw, sh))
    bloom.set_alpha(22)
    scaled.blit(bloom, (ox, oy), special_flags=pygame.BLEND_RGB_ADD)

    scanlines = _scanline_overlay()
    scaled.blit(scanlines, (0, 0))
    return scaled


_scanline_cache: pygame.Surface | None = None


def _scanline_overlay() -> pygame.Surface:
    global _scanline_cache
    if _scanline_cache is None:
        overlay = pygame.Surface((OUTPUT_WIDTH, OUTPUT_HEIGHT), pygame.SRCALPHA)
        for y in range(0, OUTPUT_HEIGHT, 2):
            pygame.draw.line(overlay, (0, 0, 0, 32), (0, y), (OUTPUT_WIDTH, y))
        _scanline_cache = overlay
    return _scanline_cache
