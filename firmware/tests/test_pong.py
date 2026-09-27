import pygame

from deck.ui.scenes.base import Context
from deck.ui.scenes.pong import KNOB_STEP, WIN_SCORE, PongScene

pygame.font.init()


def _frame(scene, dt=0.0, **inputs):
    canvas = pygame.Surface((160, 120))
    scene.draw(canvas, Context(now=0.0, dt=dt, deck=None, session=None, inputs=inputs))


def _start(mode_down: bool) -> PongScene:
    scene = PongScene()
    if mode_down:
        _frame(scene, joystick_edge={"down"})
    _frame(scene, encoder_push_edge=True)
    return scene


def test_picker_starts_one_player_by_default():
    scene = _start(mode_down=False)
    assert not scene.choosing and not scene.two_player


def test_knob_moves_the_right_paddle_only_in_two_player():
    scene = _start(mode_down=True)
    assert scene.two_player
    y = scene.ai_y
    _frame(scene, encoder_steps=2)
    assert scene.ai_y == y + 2 * KNOB_STEP

    solo = _start(mode_down=False)
    solo.ball = [80.0, 60.0]
    solo.ai_y = 60.0
    _frame(solo, encoder_steps=2)
    assert solo.ai_y == 60.0


def test_missed_ball_scores_for_the_other_side_and_match_ends_at_win_score():
    scene = _start(mode_down=True)
    scene.ai_y = 10.0  # right paddle well out of the way
    for _ in range(WIN_SCORE):
        scene.ball = [159.0, 110.0]
        scene.ball_v = [100.0, 0.0]
        _frame(scene, dt=0.05)
    assert scene.scores == [WIN_SCORE, 0]
    assert scene.game_over and scene.winner == 0
    assert not scene._hsf.active  # no high score entry in 2P
    _frame(scene, encoder_push_edge=True)
    assert not scene.game_over and scene.scores == [0, 0] and scene.two_player
