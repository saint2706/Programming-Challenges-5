"""Tests for the physics engine and level/puzzle logic.

These tests exercise ``physics.py`` and ``levels.py`` only; the Pygame renderer
in ``main.py`` is deliberately not imported so the suite runs headlessly.

Run with ``pytest`` or directly with ``python test_game.py``.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from levels import (
    BallSpec,
    GameStatus,
    Level,
    PuzzleGame,
    discover_levels,
)
from physics import Body, Rect, Vec2, World


# ---------------------------------------------------------------------------
# Vec2
# ---------------------------------------------------------------------------
def test_vec2_arithmetic():
    a = Vec2(3, 4)
    assert (a + Vec2(1, 1)) == Vec2(4, 5)
    assert (a - Vec2(1, 1)) == Vec2(2, 3)
    assert (a * 2) == Vec2(6, 8)
    assert (2 * a) == Vec2(6, 8)


def test_vec2_length_and_dot():
    a = Vec2(3, 4)
    assert a.length() == 5.0
    assert a.length_squared() == 25.0
    assert a.dot(Vec2(1, 0)) == 3.0


def test_vec2_normalized():
    n = Vec2(0, 5).normalized()
    assert math.isclose(n.x, 0.0)
    assert math.isclose(n.y, 1.0)
    # Zero vector normalizes to zero without error.
    assert Vec2(0, 0).normalized() == Vec2(0, 0)


# ---------------------------------------------------------------------------
# Rect
# ---------------------------------------------------------------------------
def test_rect_edges_and_contains():
    r = Rect(10, 20, 100, 50)
    assert (r.left, r.top, r.right, r.bottom) == (10, 20, 110, 70)
    assert r.contains_point(Vec2(50, 40))
    assert not r.contains_point(Vec2(5, 40))


def test_rect_closest_point():
    r = Rect(0, 0, 10, 10)
    # Point outside to the right -> clamps onto the right edge.
    assert r.closest_point(Vec2(20, 5)) == Vec2(10, 5)
    # Point inside stays where it is.
    assert r.closest_point(Vec2(3, 4)) == Vec2(3, 4)


# ---------------------------------------------------------------------------
# World integration & collisions
# ---------------------------------------------------------------------------
def test_gravity_accelerates_body():
    world = World(gravity=Vec2(0, 1000), linear_damping=0.0)
    body = world.add_body(Body(position=Vec2(0, 0), radius=5))
    world.step(0.1, substeps=1)
    # After one step velocity ~ g*dt and it has moved downward.
    assert body.velocity.y > 0
    assert body.position.y > 0


def test_body_rests_on_floor():
    world = World(gravity=Vec2(0, 1000), bounds=Rect(0, 0, 400, 400))
    world.add_wall(Rect(0, 300, 400, 100, name="floor"))
    body = world.add_body(Body(position=Vec2(200, 100), radius=10, restitution=0.2))
    for _ in range(240):  # ~4 seconds
        world.step(1 / 60)
    # It should settle just on top of the floor (center at floor_top - radius).
    assert math.isclose(body.position.y, 290, abs_tol=2.0)
    assert abs(body.velocity.y) < world.sleep_speed


def test_ball_bounces_off_floor():
    world = World(gravity=Vec2(0, 1000), linear_damping=0.0)
    world.add_wall(Rect(0, 200, 400, 50, name="floor"))
    body = world.add_body(Body(position=Vec2(100, 180), radius=10, restitution=0.9))
    body.velocity = Vec2(0, 400)  # moving down into the floor
    # Step until it has been pushed above the floor with upward velocity.
    bounced = False
    for _ in range(60):
        world.step(1 / 60)
        if body.velocity.y < 0:
            bounced = True
            break
    assert bounced, "ball should bounce upward off the floor"


def test_two_balls_separate_after_collision():
    world = World(gravity=Vec2(0, 0), linear_damping=0.0)
    a = world.add_body(Body(position=Vec2(100, 100), radius=15, restitution=1.0))
    b = world.add_body(Body(position=Vec2(160, 100), radius=15, restitution=1.0))
    a.velocity = Vec2(300, 0)  # a moves toward b
    # Step until they have collided (b starts moving).
    for _ in range(30):
        world.step(1 / 60)
        if b.velocity.x > 0:
            break
    # Momentum should transfer: b speeds up, a slows down.
    assert b.velocity.x > 0
    assert b.velocity.x >= a.velocity.x


def test_static_body_has_zero_inverse_mass():
    body = Body(position=Vec2(0, 0), radius=5, mass=0)
    assert body.inv_mass == 0.0


def test_bounds_keep_body_inside():
    world = World(gravity=Vec2(0, 0), bounds=Rect(0, 0, 200, 200), linear_damping=0.0)
    body = world.add_body(Body(position=Vec2(190, 100), radius=10))
    body.velocity = Vec2(500, 0)
    for _ in range(30):
        world.step(1 / 60)
    assert body.position.x + body.radius <= 200 + 1e-6


# ---------------------------------------------------------------------------
# Level loading
# ---------------------------------------------------------------------------
def test_level_from_dict_minimal():
    data = {
        "name": "Test",
        "launch": {"x": 10, "y": 20},
        "target": {"x": 30, "y": 40},
        "goal": {"x": 0, "y": 0, "w": 50, "h": 50},
    }
    level = Level.from_dict(data)
    assert level.name == "Test"
    assert isinstance(level.launch, BallSpec)
    assert level.goal.w == 50
    assert level.gravity.y == 800.0  # default gravity


def test_level_missing_key_raises():
    try:
        Level.from_dict({"name": "bad"})  # no launch/target/goal
    except ValueError as exc:
        assert "launch" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("missing required key should raise ValueError")


def test_discover_levels_finds_json():
    paths = discover_levels()
    assert len(paths) >= 1
    assert all(str(p).endswith(".json") for p in paths)


def test_all_bundled_levels_parse():
    for path in discover_levels():
        level = Level.load(path)
        assert level.width > 0 and level.height > 0
        assert level.goal.w > 0 and level.goal.h > 0


# ---------------------------------------------------------------------------
# PuzzleGame logic
# ---------------------------------------------------------------------------
def _basic_level():
    return Level.from_dict(
        {
            "name": "Basic",
            "width": 800,
            "height": 600,
            "gravity": [0, 900],
            "launch": {"x": 120, "y": 523, "radius": 15, "friction": 0.02},
            "target": {"x": 400, "y": 522, "radius": 18, "friction": 0.02},
            "goal": {"x": 620, "y": 460, "w": 170, "h": 100},
            "walls": [{"x": 0, "y": 560, "w": 800, "h": 40, "name": "floor"}],
        }
    )


def test_puzzle_starts_in_aiming_state():
    game = PuzzleGame(_basic_level())
    assert game.status == GameStatus.AIMING
    assert game.attempts == 0
    # Two balls exist: launch + target.
    assert len(game.world.bodies) == 2


def test_aim_velocity_is_slingshot_and_capped():
    game = PuzzleGame(_basic_level())
    # Dragging down-left should launch up-right.
    v = game.aim_velocity(Vec2(100, 100), Vec2(90, 110))
    assert v.x > 0 and v.y < 0
    # Capped to max power.
    huge = game.aim_velocity(Vec2(0, 0), Vec2(-10000, 0))
    assert huge.length() <= game.level.max_power + 1e-6


def test_launch_increments_attempts_and_simulates():
    game = PuzzleGame(_basic_level())
    game.launch(Vec2(500, 0))
    assert game.attempts == 1
    assert game.status == GameStatus.SIMULATING


def test_reset_restores_positions_and_keeps_attempts():
    game = PuzzleGame(_basic_level())
    start = game.launch_ball.position.copy()
    game.launch(Vec2(500, -200))
    game.update(1 / 60)
    game.reset()
    assert game.status == GameStatus.AIMING
    assert game.launch_ball.position == start
    assert game.attempts == 1  # attempts are preserved across a reset


def test_winnable_level_can_be_solved():
    game = PuzzleGame(_basic_level())
    game.launch(Vec2(1100, 0))  # known winning shot (see level tuning)
    assert game.simulate() == GameStatus.WON


def test_hazard_causes_loss():
    level = Level.from_dict(
        {
            "name": "Hazard",
            "width": 400,
            "height": 400,
            "gravity": [0, 900],
            "launch": {"x": 50, "y": 50, "radius": 10},
            "target": {"x": 200, "y": 50, "radius": 12},
            "goal": {"x": 380, "y": 0, "w": 20, "h": 20},
            "hazards": [{"x": 0, "y": 300, "w": 400, "h": 100, "name": "pit"}],
        }
    )
    game = PuzzleGame(level)
    game.launch(Vec2(0, 10))  # target just falls into the pit
    assert game.simulate() == GameStatus.LOST


def test_bundled_level_one_is_solvable():
    paths = [p for p in discover_levels() if "01" in p.name]
    assert paths, "expected a level 01 file"
    game = PuzzleGame(Level.load(paths[0]))
    game.launch(Vec2(1100, 0))
    assert game.simulate() == GameStatus.WON


def run_all_tests():
    print("\n=== Running Physics Puzzle Tests ===\n")
    tests = [obj for name, obj in sorted(globals().items()) if name.startswith("test_")]
    failures = 0
    for test in tests:
        try:
            test()
            print(f"✓ {test.__name__}")
        except Exception as exc:  # pragma: no cover - reporting path
            failures += 1
            print(f"✗ {test.__name__}: {exc}")
    if failures:
        print(f"\n✗ {failures} test(s) failed\n")
        return False
    print(f"\n=== All {len(tests)} tests passed! ✓ ===\n")
    return True


if __name__ == "__main__":
    sys.exit(0 if run_all_tests() else 1)
