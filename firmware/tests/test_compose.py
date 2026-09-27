import pygame

from deck.panel.base import CANVAS_HEIGHT, CANVAS_WIDTH, GB_CANVAS_HEIGHT, GB_CANVAS_WIDTH, RAIL_HEIGHT, RAIL_WIDTH
from deck.ui.render import OUTPUT_HEIGHT, OUTPUT_WIDTH, compose_output


def _solid(w, h, color):
    s = pygame.Surface((w, h))
    s.fill(color)
    return s


def _rails():
    return _solid(RAIL_WIDTH, RAIL_HEIGHT, (0, 200, 0)), _solid(RAIL_WIDTH, RAIL_HEIGHT, (0, 0, 200))


def test_rails_land_in_the_side_bars():
    out = compose_output(_solid(CANVAS_WIDTH, CANVAS_HEIGHT, (200, 0, 0)), _rails())
    y = OUTPUT_HEIGHT // 2 + 1  # odd row, off the scanlines
    assert out.get_at((85, y)).g > 150
    assert out.get_at((OUTPUT_WIDTH - 85, y)).b > 150
    assert out.get_at((OUTPUT_WIDTH // 2, y)).r > 150


def test_rails_fit_beside_the_game_boy_canvas_too():
    out = compose_output(_solid(GB_CANVAS_WIDTH, GB_CANVAS_HEIGHT, (200, 0, 0)), _rails())
    y = OUTPUT_HEIGHT // 2 + 1
    assert out.get_at((128, y)).g > 150


def test_screen_level_zero_is_black_and_half_dims():
    canvas = _solid(CANVAS_WIDTH, CANVAS_HEIGHT, (200, 200, 200))
    y = OUTPUT_HEIGHT // 2 + 1
    assert compose_output(canvas, _rails(), 0.0).get_at((OUTPUT_WIDTH // 2, y))[:3] == (0, 0, 0)
    full = compose_output(canvas, None, 1.0).get_at((OUTPUT_WIDTH // 2, y)).r
    half = compose_output(canvas, None, 0.5).get_at((OUTPUT_WIDTH // 2, y)).r
    assert abs(half - full / 2) <= 2


def test_bloom_is_slight_not_doubling():
    canvas = _solid(CANVAS_WIDTH, CANVAS_HEIGHT, (100, 50, 20))
    r, g, b, _ = compose_output(canvas).get_at((OUTPUT_WIDTH // 2, OUTPUT_HEIGHT // 2 + 1))
    assert 100 <= r <= 112 and 50 <= g <= 56 and 20 <= b <= 24
