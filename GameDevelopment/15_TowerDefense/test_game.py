"""Headless tests for the tower defense engine.

Only :mod:`core` is imported — the Pygame renderer in ``main.py`` and the
terminal front-end are deliberately left alone so the suite runs without a
display. Because the engine steps in fixed ticks, every combat assertion below
is exactly reproducible.

Run with ``pytest`` or directly with ``python test_game.py``.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core import (  # noqa: E402
    ENEMY_KINDS,
    SELL_REFUND,
    TICK,
    TOWER_KINDS,
    BuildError,
    Enemy,
    GameStatus,
    Level,
    Projectile,
    Route,
    SpawnGroup,
    TargetMode,
    TowerDefenseGame,
    Vec2,
    Wave,
    discover_levels,
    parse_tile,
    tile_label,
)


# ---------------------------------------------------------------------------
# Fixtures built in code, so the tests do not depend on the shipped levels
# ---------------------------------------------------------------------------
def straight_level(**overrides):
    """A 10x3 map with one straight road along the middle row."""
    data = {
        "name": "Test Straight",
        "cols": 10,
        "rows": 3,
        "tile_size": 48,
        "starting_gold": 1000,
        "starting_lives": 10,
        "wave_break": 5.0,
        "waypoints": [[0, 1], [9, 1]],
        "plots": [[2, 0], [4, 0], [6, 0], [2, 2], [4, 2], [6, 2]],
        "waves": [{"groups": [{"enemy": "grunt", "count": 2, "interval": 1.0}]}],
    }
    data.update(overrides)
    return Level.from_dict(data)


def game(**overrides):
    return TowerDefenseGame(straight_level(**overrides), seed=1)


# ---------------------------------------------------------------------------
# Vec2 and Route
# ---------------------------------------------------------------------------
def test_vec2_arithmetic():
    a = Vec2(3, 4)
    assert a + Vec2(1, 1) == Vec2(4, 5)
    assert a - Vec2(1, 1) == Vec2(2, 3)
    assert a * 2 == Vec2(6, 8)
    assert 2 * a == Vec2(6, 8)
    assert a.length() == 5.0
    assert a.distance_to(Vec2(0, 0)) == 5.0


def test_vec2_normalised_handles_zero():
    assert Vec2(0, 5).normalised() == Vec2(0, 1)
    assert Vec2(0, 0).normalised() == Vec2(0, 0)


def test_vec2_angle_is_clockwise_from_up():
    # Sprites face up, so "up" must be 0 degrees and "right" must be +90.
    assert math.isclose(Vec2(0, -1).angle_degrees(), 0.0)
    assert math.isclose(Vec2(1, 0).angle_degrees(), 90.0)
    assert math.isclose(Vec2(0, 1).angle_degrees(), 180.0)
    assert math.isclose(Vec2(-1, 0).angle_degrees(), -90.0)


def test_route_length_and_lookup():
    route = Route([Vec2(0, 0), Vec2(100, 0), Vec2(100, 50)])
    assert route.length == 150
    assert route.position_at(0) == Vec2(0, 0)
    assert route.position_at(50) == Vec2(50, 0)
    assert route.position_at(125) == Vec2(100, 25)


def test_route_clamps_out_of_range_distances():
    route = Route([Vec2(0, 0), Vec2(60, 0)])
    assert route.position_at(-20) == Vec2(0, 0)
    assert route.position_at(500) == Vec2(60, 0)


def test_route_heading_follows_the_current_segment():
    route = Route([Vec2(0, 0), Vec2(100, 0), Vec2(100, 100)])
    assert route.heading_at(10) == Vec2(1, 0)
    assert route.heading_at(150) == Vec2(0, 1)


def test_route_needs_two_points():
    try:
        Route([Vec2(0, 0)])
    except ValueError:
        pass
    else:  # pragma: no cover - guard
        raise AssertionError("a one-point route should be rejected")


# ---------------------------------------------------------------------------
# Levels
# ---------------------------------------------------------------------------
def test_shipped_levels_load_and_validate():
    paths = discover_levels()
    assert paths, "no level files found"
    for path in paths:
        level = Level.load(path)
        assert level.waves, f"{level.name} has no waves"
        assert level.plots, f"{level.name} has no build plots"
        path_tiles = set(level.path_tiles())
        assert not path_tiles & set(level.plots)
        for col, row, _sprite in level.decor:
            assert level.in_bounds(col, row)
            assert (col, row) not in path_tiles


def test_path_tiles_walk_every_step():
    level = straight_level()
    assert list(level.path_tiles()) == [(c, 1) for c in range(10)]


def test_plot_on_the_path_is_rejected():
    try:
        straight_level(plots=[[3, 1]])
    except ValueError as exc:
        assert "path" in str(exc)
    else:  # pragma: no cover - guard
        raise AssertionError("a plot on the road should be rejected")


def test_diagonal_waypoints_are_rejected():
    try:
        list(straight_level(waypoints=[[0, 0], [5, 2]]).path_tiles())
    except ValueError as exc:
        assert "diagonal" in str(exc)
    else:  # pragma: no cover - guard
        raise AssertionError("diagonal waypoints should be rejected")


def test_off_map_plot_is_rejected():
    try:
        straight_level(plots=[[99, 0]])
    except ValueError:
        pass
    else:  # pragma: no cover - guard
        raise AssertionError("an off-map plot should be rejected")


def test_tile_centre_and_tile_at_round_trip():
    level = straight_level()
    for tile in ((0, 0), (4, 2), (9, 1)):
        assert level.tile_at(level.tile_centre(*tile)) == tile


def test_air_path_is_a_straight_line():
    level = straight_level(
        waypoints=[[0, 1], [4, 1], [4, 2], [9, 2]], plots=[[2, 0], [6, 0]]
    )
    ground, air = level.ground_path(), level.air_path()
    assert air.length < ground.length
    assert len(air.points) == 2


def test_wave_parsing_and_summary():
    wave = Wave.from_dict(
        {
            "groups": [
                {"enemy": "grunt", "count": 3},
                {"enemy": "runner", "count": 2, "interval": 0.5, "delay": 2.0},
            ],
            "reward": 40,
        }
    )
    assert wave.total_enemies == 5
    assert wave.reward == 40
    assert "3x Grunt" in wave.summary() and "2x Runner" in wave.summary()


def test_unknown_enemy_in_a_wave_is_rejected():
    try:
        SpawnGroup.from_dict({"enemy": "dragon", "count": 1})
    except ValueError as exc:
        assert "dragon" in str(exc)
    else:  # pragma: no cover - guard
        raise AssertionError("unknown enemies should be rejected")


def test_spawn_group_duration():
    assert SpawnGroup(enemy="grunt", count=4, interval=0.5, delay=1.0).duration == 2.5


# ---------------------------------------------------------------------------
# Building economy
# ---------------------------------------------------------------------------
def test_build_deducts_gold_and_occupies_the_plot():
    g = game(starting_gold=100)
    tower = g.build((2, 0), "gun")
    assert g.gold == 100 - TOWER_KINDS["gun"].cost
    assert g.tower_at((2, 0)) is tower
    assert not g.is_buildable((2, 0))


def test_cannot_build_off_a_plot():
    g = game()
    for tile in ((3, 1), (0, 0), (9, 2)):
        try:
            g.build(tile, "gun")
        except BuildError:
            continue
        raise AssertionError(f"{tile} is not a plot")  # pragma: no cover


def test_cannot_build_twice_on_one_plot():
    g = game()
    g.build((2, 0), "gun")
    try:
        g.build((2, 0), "gatling")
    except BuildError as exc:
        assert "already" in str(exc)
    else:  # pragma: no cover - guard
        raise AssertionError("double-building should be rejected")


def test_cannot_afford_is_rejected():
    g = game(starting_gold=10)
    try:
        g.build((2, 0), "mortar")
    except BuildError as exc:
        assert "gold" in str(exc)
    else:  # pragma: no cover - guard
        raise AssertionError("an unaffordable tower should be rejected")


def test_unknown_tower_is_rejected():
    g = game()
    try:
        g.build((2, 0), "railgun")
    except BuildError as exc:
        assert "railgun" in str(exc)
    else:  # pragma: no cover - guard
        raise AssertionError("unknown towers should be rejected")


def test_upgrade_improves_stats_and_costs_gold():
    g = game()
    tower = g.build((2, 0), "gun")
    base_damage, base_range = tower.damage, tower.range
    cost = tower.kind.upgrade_cost(0)
    gold_before = g.gold
    g.upgrade((2, 0))
    assert tower.tier == 1
    assert g.gold == gold_before - cost
    assert tower.damage > base_damage
    assert tower.range >= base_range


def test_upgrade_stops_at_the_top_tier():
    g = game(starting_gold=5000)
    tower = g.build((2, 0), "gun")
    for _ in range(tower.kind.max_tier):
        g.upgrade((2, 0))
    assert tower.tier == tower.kind.max_tier
    assert tower.kind.upgrade_cost(tower.tier) is None
    try:
        g.upgrade((2, 0))
    except BuildError as exc:
        assert "fully upgraded" in str(exc)
    else:  # pragma: no cover - guard
        raise AssertionError("upgrading past the top tier should be rejected")


def test_upgrading_an_empty_plot_is_rejected():
    g = game()
    try:
        g.upgrade((2, 0))
    except BuildError as exc:
        assert "no tower" in str(exc)
    else:  # pragma: no cover - guard
        raise AssertionError("upgrading nothing should be rejected")


def test_sell_refunds_a_fraction_of_the_investment():
    g = game()
    tower = g.build((2, 0), "gun")
    g.upgrade((2, 0))
    invested = tower.invested
    gold_before = g.gold
    refund = g.sell((2, 0))
    assert refund == int(invested * SELL_REFUND)
    assert g.gold == gold_before + refund
    assert g.tower_at((2, 0)) is None
    assert g.is_buildable((2, 0))


# ---------------------------------------------------------------------------
# Targeting
# ---------------------------------------------------------------------------
def make_enemy(kind_key, distance, path, hp_scale=1.0):
    kind = ENEMY_KINDS[kind_key]
    hp = kind.hp * hp_scale
    enemy = Enemy(kind=kind, max_hp=hp, hp=hp, path=path, distance=distance)
    enemy.refresh_position()
    return enemy


def test_tower_ignores_enemies_out_of_range():
    g = game()
    tower = g.build((2, 0), "gun")
    far = make_enemy("grunt", g.ground_path.length - 1, g.ground_path)
    assert not tower.can_target(far)
    near = make_enemy("grunt", 2 * 48, g.ground_path)
    assert tower.can_target(near)


def test_ground_only_tower_cannot_hit_aircraft():
    g = game()
    mortar = g.build((4, 0), "mortar")
    bomber = make_enemy("bomber", 4 * 48, g.air_path)
    assert not mortar.can_target(bomber)


def test_anti_air_tower_cannot_hit_ground_units():
    g = game()
    flak = g.build((4, 0), "flak")
    grunt = make_enemy("grunt", 4 * 48, g.ground_path)
    assert not flak.can_target(grunt)
    bomber = make_enemy("bomber", 4 * 48, g.air_path)
    assert flak.can_target(bomber)


def test_target_modes_pick_different_enemies():
    g = game()
    tower = g.build((4, 0), "gun")
    tower.tier = 2  # widest range, so all three candidates are reachable
    early = make_enemy("grunt", 3 * 48, g.ground_path)
    middle = make_enemy("grunt", 4 * 48, g.ground_path, hp_scale=4.0)
    late = make_enemy("grunt", 5 * 48, g.ground_path)
    pool = [early, middle, late]

    tower.target_mode = TargetMode.FIRST
    assert tower.pick_target(pool) is late
    tower.target_mode = TargetMode.LAST
    assert tower.pick_target(pool) is early
    tower.target_mode = TargetMode.CLOSEST
    assert tower.pick_target(pool) is middle
    tower.target_mode = TargetMode.STRONGEST
    assert tower.pick_target(pool) is middle


def test_setting_an_invalid_target_mode_raises():
    g = game()
    g.build((2, 0), "gun")
    try:
        g.set_target_mode((2, 0), "sideways")
    except ValueError:
        pass
    else:  # pragma: no cover - guard
        raise AssertionError("an unknown target mode should be rejected")


# ---------------------------------------------------------------------------
# Damage, armour, slow, splash
# ---------------------------------------------------------------------------
def test_armour_reduces_damage_but_never_below_one():
    g = game()
    armoured = make_enemy("armoured", 0, g.ground_path)
    dealt = armoured.take_damage(10)
    assert dealt == 10 - ENEMY_KINDS["armoured"].armour
    heavy = make_enemy("armoured", 0, g.ground_path)
    assert heavy.take_damage(1) == 1  # a hit always registers


def test_armour_pierce_bypasses_plating():
    g = game()
    plain = make_enemy("armoured", 0, g.ground_path)
    pierced = make_enemy("armoured", 0, g.ground_path)
    assert pierced.take_damage(10, armour_pierce=4) > plain.take_damage(10)


def test_damage_never_exceeds_remaining_hp():
    g = game()
    enemy = make_enemy("grunt", 0, g.ground_path)
    dealt = enemy.take_damage(10_000)
    assert dealt == ENEMY_KINDS["grunt"].hp
    assert not enemy.alive


def test_slow_reduces_speed_and_expires():
    g = game()
    enemy = make_enemy("runner", 0, g.ground_path)
    full_speed = enemy.speed
    enemy.apply_slow(0.5, 1.0)
    assert enemy.speed == full_speed * 0.5
    enemy.advance(1.5)
    assert enemy.speed == full_speed


def test_harsher_slow_wins_and_duration_refreshes():
    g = game()
    enemy = make_enemy("runner", 0, g.ground_path)
    enemy.apply_slow(0.8, 1.0)
    enemy.apply_slow(0.4, 0.5)
    assert enemy.slow_factor == 0.4
    assert enemy.slow_timer == 1.0  # the longer timer is kept
    enemy.apply_slow(1.0, 5.0)  # a no-op slow changes nothing
    assert enemy.slow_factor == 0.4


def test_splash_damages_every_enemy_in_the_blast():
    g = game()
    close = make_enemy("grunt", 100, g.ground_path)
    also_close = make_enemy("grunt", 120, g.ground_path)
    far = make_enemy("grunt", 500, g.ground_path)
    g.enemies = [close, also_close, far]
    shot = Projectile(
        position=close.position,
        target=close,
        speed=400,
        damage=20,
        splash_radius=60,
    )
    g._impact(shot)
    assert close.hp < close.max_hp
    assert also_close.hp < also_close.max_hp
    assert far.hp == far.max_hp


def test_projectile_is_wasted_when_its_target_dies_mid_flight():
    g = game()
    enemy = make_enemy("grunt", 200, g.ground_path)
    shot = Projectile(position=Vec2(0, 0), target=enemy, speed=100, damage=5)
    enemy.alive = False
    assert shot.advance(0.1) is False
    assert not shot.alive


def test_enemy_advance_reports_reaching_the_exit():
    g = game()
    enemy = make_enemy("grunt", g.ground_path.length - 1, g.ground_path)
    assert enemy.advance(1.0) is True


# ---------------------------------------------------------------------------
# Waves, lives and outcomes
# ---------------------------------------------------------------------------
def test_start_wave_queues_every_enemy():
    g = game()
    wave = g.start_wave()
    assert g.status is GameStatus.WAVE
    assert g.pending_spawns == wave.total_enemies
    assert g.alive_enemies == 0


def test_starting_a_second_wave_mid_wave_is_rejected():
    g = game()
    g.start_wave()
    try:
        g.start_wave()
    except BuildError as exc:
        assert "already" in str(exc)
    else:  # pragma: no cover - guard
        raise AssertionError("overlapping waves should be rejected")


def test_enemies_spawn_on_schedule():
    g = game(waves=[{"groups": [{"enemy": "grunt", "count": 3, "interval": 1.0}]}])
    g.start_wave()
    g.run_seconds(0.1)
    assert g.alive_enemies == 1
    g.run_seconds(1.0)
    assert g.alive_enemies == 2
    g.run_seconds(1.0)
    assert g.alive_enemies == 3
    assert g.pending_spawns == 0


def test_flying_enemies_use_the_air_route():
    level = straight_level(
        waypoints=[[0, 1], [4, 1], [4, 2], [9, 2]],
        plots=[[2, 0], [6, 0]],
        waves=[{"groups": [{"enemy": "bomber", "count": 1}]}],
    )
    g = TowerDefenseGame(level, seed=1)
    g.start_wave()
    g.run_seconds(0.1)
    assert g.enemies[0].path is g.air_path


def test_undefended_wave_leaks_and_costs_lives():
    g = game(starting_lives=10)
    g.start_wave()
    g.run_seconds(40)
    assert g.leaked == 2
    assert g.lives == 10 - 2 * ENEMY_KINDS["grunt"].leak_damage


def test_a_juggernaut_leak_costs_several_lives():
    g = game(
        starting_lives=20,
        waves=[{"groups": [{"enemy": "juggernaut", "count": 1}]}],
    )
    g.start_wave()
    g.run_seconds(60)
    assert g.lives == 20 - ENEMY_KINDS["juggernaut"].leak_damage


def test_running_out_of_lives_loses_the_run():
    g = game(
        starting_lives=1,
        waves=[{"groups": [{"enemy": "grunt", "count": 3, "interval": 0.5}]}],
    )
    g.start_wave()
    g.run_seconds(40)
    assert g.status is GameStatus.LOST
    assert g.lives == 0


def test_no_further_simulation_after_a_loss():
    g = game(starting_lives=1)
    g.start_wave()
    g.run_seconds(40)
    snapshot = g.stats()
    g.run_seconds(10)
    assert g.stats() == snapshot


def test_clearing_the_last_wave_wins():
    g = game(starting_gold=1000)
    for tile in ((2, 0), (4, 0), (6, 0), (2, 2), (4, 2)):
        g.build(tile, "gun")
    g.start_wave()
    g.run_seconds(40)
    assert g.status is GameStatus.WON
    assert g.leaked == 0
    assert g.killed == 2


def test_clearing_a_wave_pays_the_bounty_and_the_reward():
    g = game(
        starting_gold=1000,
        waves=[{"groups": [{"enemy": "grunt", "count": 1}], "reward": 50}],
    )
    for tile in ((2, 0), (4, 0), (2, 2)):
        g.build(tile, "gun")
    gold_after_building = g.gold
    g.start_wave()
    g.run_seconds(40)
    expected = gold_after_building + ENEMY_KINDS["grunt"].bounty + 50
    assert g.gold == expected
    assert g.score == ENEMY_KINDS["grunt"].bounty + 50


def test_build_phase_auto_starts_the_next_wave():
    g = game(wave_break=2.0)
    assert g.status is GameStatus.BUILDING
    g.run_seconds(1.0)
    assert g.status is GameStatus.BUILDING
    g.run_seconds(1.5)
    assert g.status is GameStatus.WAVE


def test_towers_credit_their_kills():
    g = game(starting_gold=1000)
    tower = g.build((4, 0), "gun")
    g.build((2, 0), "gun")
    g.start_wave()
    g.run_seconds(40)
    assert g.killed == 2
    assert tower.damage_dealt > 0
    assert sum(t.kills for t in g.towers.values()) == 2


def test_frost_tower_slows_what_it_hits():
    g = game(
        starting_gold=1000,
        waves=[{"groups": [{"enemy": "juggernaut", "count": 1}]}],
    )
    g.build((2, 0), "frost")
    g.start_wave()
    g.run_seconds(6)
    boss = g.enemies[0]
    assert boss.slow_timer > 0
    assert boss.speed < boss.kind.speed


# ---------------------------------------------------------------------------
# Events and determinism
# ---------------------------------------------------------------------------
def test_events_are_emitted_and_drained_once():
    g = game(starting_gold=1000)
    g.build((2, 0), "gun")
    assert any(e.kind == "build" for e in g.drain_events())
    assert g.drain_events() == []
    g.start_wave()
    g.run_seconds(10)
    kinds = {e.kind for e in g.drain_events()}
    assert "wave" in kinds and "shoot" in kinds


def test_same_orders_and_seed_give_identical_results():
    def play():
        g = game(starting_gold=1000)
        g.build((2, 0), "gun")
        g.build((4, 2), "gatling")
        g.start_wave()
        g.run_ticks(1800)
        return g.stats()

    assert play() == play()


def test_tick_length_matches_run_seconds():
    g = game()
    g.run_ticks(60)
    assert math.isclose(g.elapsed, 60 * TICK, rel_tol=1e-9)


# ---------------------------------------------------------------------------
# Tile labels
# ---------------------------------------------------------------------------
def test_tile_label_and_parse_round_trip():
    for tile in ((0, 0), (2, 5), (15, 11)):
        assert parse_tile(tile_label(tile)) == tile


def test_parse_tile_accepts_numeric_pairs():
    assert parse_tile("2,5") == (2, 5)
    assert parse_tile(" 2 , 5 ") == (2, 5)


def test_parse_tile_rejects_nonsense():
    for bad in ("", "hello world", "??"):
        try:
            parse_tile(bad)
        except ValueError:
            continue
        raise AssertionError(f"{bad!r} should not parse")  # pragma: no cover


# ---------------------------------------------------------------------------
# Standalone runner
# ---------------------------------------------------------------------------
def _run_all() -> int:
    tests = [
        (name, obj)
        for name, obj in sorted(globals().items())
        if name.startswith("test_") and callable(obj)
    ]
    failures = 0
    for name, test in tests:
        try:
            test()
        except Exception as exc:  # pragma: no cover - standalone runner
            failures += 1
            print(f"  ✗ {name}: {type(exc).__name__}: {exc}")
        else:
            print(f"  ✓ {name}")
    print(f"\n{len(tests) - failures}/{len(tests)} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(_run_all())
