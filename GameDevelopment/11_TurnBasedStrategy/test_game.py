"""Quick verification script to test Turn-Based Strategy game mechanics."""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from main import GRID_SIZE, Game, GameState, Unit


def test_unit_creation():
    """Test that units are created correctly."""
    unit = Unit(5, 5, (255, 0, 0), "Test Unit", is_player=True)
    assert unit.grid_x == 5
    assert unit.grid_y == 5
    assert unit.hp == 100
    assert unit.max_hp == 100
    assert unit.is_player == True
    print("✓ Unit creation test passed")


def test_unit_movement():
    """Test unit movement mechanics."""
    grid = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
    unit = Unit(5, 5, (255, 0, 0), "Test Unit", is_player=True)

    # Can move within range
    assert unit.can_move_to(6, 5, grid) == True  # 1 tile away
    assert unit.can_move_to(7, 5, grid) == True  # 2 tiles away
    assert unit.can_move_to(8, 5, grid) == True  # 3 tiles away (max range)
    assert unit.can_move_to(9, 5, grid) == False  # 4 tiles away (too far)

    # Cannot move to occupied tile  (grid is [y][x])
    grid[5][6] = Unit(6, 5, (0, 0, 255), "Blocker", is_player=False)
    assert unit.can_move_to(6, 5, grid) == False
    grid[5][6] = None  # Clean up

    # Cannot move twice
    unit.move_to(6, 5)
    grid[5][5] = None
    grid[5][6] = unit
    assert unit.can_move_to(7, 5, grid) == False  # Has already moved

    print("✓ Unit movement test passed")


def test_unit_attack():
    """Test unit attack mechanics."""
    attacker = Unit(5, 5, (255, 0, 0), "Attacker", is_player=True)
    target = Unit(6, 5, (0, 0, 255), "Target", is_player=False)

    # Can attack within range
    assert attacker.can_attack(target) == True

    # Attack reduces HP
    initial_hp = target.hp
    attacker.attack(target)
    assert target.hp == initial_hp - attacker.attack_damage
    assert attacker.has_attacked == True

    # Cannot attack twice
    assert attacker.can_attack(target) == False

    print("✓ Unit attack test passed")


def test_game_initialization():
    """Test game initialization."""
    game = Game()

    # Check player exists
    assert game.player is not None
    assert game.player.is_player == True
    assert game.grid[game.player.grid_y][game.player.grid_x] == game.player

    # Check enemies exist
    assert len(game.enemies) == 3
    for enemy in game.enemies:
        assert enemy.is_player == False
        assert game.grid[enemy.grid_y][enemy.grid_x] == enemy

    # Check initial state
    assert game.state == GameState.PLAYER_TURN

    print("✓ Game initialization test passed")


def test_valid_moves():
    """Test getting valid moves for a unit."""
    game = Game()

    # Player should have valid moves
    valid_moves = game.get_valid_moves(game.player)
    assert len(valid_moves) > 0

    # All moves should be within movement range
    for move_x, move_y in valid_moves:
        distance = abs(move_x - game.player.grid_x) + abs(move_y - game.player.grid_y)
        assert distance <= game.player.movement_range

    print("✓ Valid moves test passed")


def test_ai_pathfinding():
    """Test that AI finds best move towards player."""
    game = Game()

    # Get an enemy
    enemy = game.enemies[0]
    initial_distance = abs(enemy.grid_x - game.player.grid_x) + abs(
        enemy.grid_y - game.player.grid_y
    )

    # Find best move
    best_move = game.find_best_move(enemy)

    if best_move:
        new_distance = abs(best_move[0] - game.player.grid_x) + abs(
            best_move[1] - game.player.grid_y
        )
        # Best move should reduce distance to player (or stay same if can't get closer)
        assert new_distance <= initial_distance

    print("✓ AI pathfinding test passed")


def run_all_tests():
    """Run all verification tests."""
    print("\n=== Running Turn-Based Strategy Game Tests ===\n")

    try:
        test_unit_creation()
        test_unit_movement()
        test_unit_attack()
        test_game_initialization()
        test_valid_moves()
        test_ai_pathfinding()

        print("\n=== All tests passed! ✓ ===\n")
        return True
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}\n")
        return False
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}\n")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
