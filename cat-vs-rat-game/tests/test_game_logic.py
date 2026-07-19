import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import game


def test_move_enemy_bounces_off_right_wall():
    enemy_x, enemy_y, speed_x, speed_y = game.move_enemy(90, 10, 3, 3, 100, 100, 10)

    assert enemy_x == 93
    assert enemy_y == 13
    assert speed_x == -3
    assert speed_y == 3


def test_collision_detects_overlapping_rectangles():
    assert game.is_collision(0, 0, 10, 5, 5, 10) is True
    assert game.is_collision(0, 0, 10, 40, 40, 10) is False
