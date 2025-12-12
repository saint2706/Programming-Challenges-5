"""Turn-Based Strategy Microgame using Pygame.

A grid-based tactical game where the player controls a unit and faces AI-controlled
enemies in turn-based combat. Features simple AI that moves towards the player
and attacks when in range.

Controls:
    Left click on tile: Move or attack (depending on selected unit and range)
    ESC: Quit game
    R: Restart (when game over)
"""

import sys
from enum import Enum

import pygame

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 700
GRID_SIZE = 10
TILE_SIZE = 60
GRID_OFFSET_X = 50
GRID_OFFSET_Y = 50
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
LIGHT_GRAY = (200, 200, 200)
DARK_GRAY = (50, 50, 50)
BLUE = (70, 130, 255)
DARK_BLUE = (40, 80, 180)
RED = (255, 70, 70)
DARK_RED = (180, 40, 40)
GREEN = (70, 255, 70)
YELLOW = (255, 255, 100)
ORANGE = (255, 165, 0)

# Setup Screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Turn-Based Strategy - Challenge 11")
clock = pygame.time.Clock()


class GameState(Enum):
    PLAYER_TURN = 1
    ENEMY_TURN = 2
    GAME_OVER = 3
    VICTORY = 4


class Unit:
    """Base class for all units in the game."""

    def __init__(self, x, y, color, name, is_player=False):
        self.grid_x = x
        self.grid_y = y
        self.color = color
        self.name = name
        self.is_player = is_player
        self.max_hp = 100
        self.hp = 100
        self.attack_damage = 30
        self.movement_range = 3
        self.attack_range = 1
        self.has_moved = False
        self.has_attacked = False

    def can_move_to(self, x, y, grid):
        """Check if the unit can move to the given position."""
        if x < 0 or x >= GRID_SIZE or y < 0 or y >= GRID_SIZE:
            return False

        # Check if occupied
        if grid[y][x] is not None:
            return False

        # Check distance
        distance = abs(x - self.grid_x) + abs(y - self.grid_y)
        return distance <= self.movement_range and not self.has_moved

    def can_attack(self, target):
        """Check if the unit can attack the target."""
        if self.has_attacked:
            return False
        distance = abs(target.grid_x - self.grid_x) + abs(target.grid_y - self.grid_y)
        return distance <= self.attack_range

    def move_to(self, x, y):
        """Move the unit to the given position."""
        self.grid_x = x
        self.grid_y = y
        self.has_moved = True

    def attack(self, target):
        """Attack the target unit."""
        target.hp -= self.attack_damage
        self.has_attacked = True

    def reset_turn(self):
        """Reset turn flags."""
        self.has_moved = False
        self.has_attacked = False

    def draw(self, screen, selected=False):
        """Draw the unit on the screen."""
        x = GRID_OFFSET_X + self.grid_x * TILE_SIZE
        y = GRID_OFFSET_Y + self.grid_y * TILE_SIZE

        # Draw selection highlight
        if selected:
            pygame.draw.rect(
                screen,
                YELLOW,
                (x, y, TILE_SIZE, TILE_SIZE),
                4,
            )

        # Draw unit
        center_x = x + TILE_SIZE // 2
        center_y = y + TILE_SIZE // 2
        pygame.draw.circle(screen, self.color, (center_x, center_y), TILE_SIZE // 3)

        # Draw HP bar
        hp_width = TILE_SIZE - 10
        hp_height = 8
        hp_x = x + 5
        hp_y = y + TILE_SIZE - 15

        # Background
        pygame.draw.rect(screen, DARK_GRAY, (hp_x, hp_y, hp_width, hp_height))

        # HP fill
        hp_fill = int(hp_width * (self.hp / self.max_hp))
        hp_color = GREEN if self.hp > 50 else ORANGE if self.hp > 25 else RED
        pygame.draw.rect(screen, hp_color, (hp_x, hp_y, hp_fill, hp_height))


class Game:
    """Main game class managing grid, units, and game state."""

    def __init__(self):
        self.grid = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.player = Unit(2, 7, BLUE, "Player", is_player=True)
        self.grid[self.player.grid_y][self.player.grid_x] = self.player

        # Create enemies
        self.enemies = []
        enemy_positions = [(7, 2), (8, 3), (6, 1)]
        for i, (x, y) in enumerate(enemy_positions):
            enemy = Unit(x, y, RED, f"Enemy {i+1}", is_player=False)
            self.enemies.append(enemy)
            self.grid[y][x] = enemy

        self.state = GameState.PLAYER_TURN
        self.selected_unit = None
        self.font = pygame.font.Font(None, 30)
        self.title_font = pygame.font.Font(None, 48)
        self.highlighted_tiles = []

    def get_unit_at(self, x, y):
        """Get the unit at the given grid position."""
        if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
            return self.grid[y][x]
        return None

    def get_valid_moves(self, unit):
        """Get all valid move positions for the unit."""
        valid_moves = []
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                if unit.can_move_to(x, y, self.grid):
                    valid_moves.append((x, y))
        return valid_moves

    def get_valid_attacks(self, unit):
        """Get all valid attack targets for the unit."""
        valid_targets = []
        for enemy in self.enemies if unit.is_player else [self.player]:
            if enemy.hp > 0 and unit.can_attack(enemy):
                valid_targets.append((enemy.grid_x, enemy.grid_y))
        return valid_targets

    def handle_click(self, grid_x, grid_y):
        """Handle mouse click on grid."""
        if self.state != GameState.PLAYER_TURN:
            return

        clicked_unit = self.get_unit_at(grid_x, grid_y)

        # If clicking on player unit
        if clicked_unit == self.player:
            self.selected_unit = self.player
            self.highlighted_tiles = self.get_valid_moves(self.player)
            self.highlighted_tiles.extend(self.get_valid_attacks(self.player))
            return

        # If player is selected
        if self.selected_unit == self.player:
            # Try to attack
            if clicked_unit and not clicked_unit.is_player and clicked_unit.hp > 0:
                if self.player.can_attack(clicked_unit):
                    self.player.attack(clicked_unit)
                    if clicked_unit.hp <= 0:
                        self.grid[clicked_unit.grid_y][clicked_unit.grid_x] = None

                    # Check victory
                    if all(e.hp <= 0 for e in self.enemies):
                        self.state = GameState.VICTORY
                    elif self.player.has_moved and self.player.has_attacked:
                        self.end_player_turn()

                    self.selected_unit = None
                    self.highlighted_tiles = []
                    return

            # Try to move
            if self.player.can_move_to(grid_x, grid_y, self.grid):
                # Remove from old position
                self.grid[self.player.grid_y][self.player.grid_x] = None

                # Move to new position
                self.player.move_to(grid_x, grid_y)
                self.grid[grid_y][grid_x] = self.player

                # Update highlights for attacks
                self.highlighted_tiles = self.get_valid_attacks(self.player)
                return

    def end_player_turn(self):
        """End the player's turn and start enemy turns."""
        self.selected_unit = None
        self.highlighted_tiles = []
        self.player.reset_turn()
        self.state = GameState.ENEMY_TURN
        pygame.time.set_timer(pygame.USEREVENT, 800)  # Delay for AI moves

    def execute_enemy_turn(self):
        """Execute AI turns for all enemies."""
        for enemy in self.enemies:
            if enemy.hp <= 0:
                continue

            # Try to attack player if in range
            if enemy.can_attack(self.player):
                enemy.attack(self.player)
                if self.player.hp <= 0:
                    self.state = GameState.GAME_OVER
                    return
            # Otherwise try to move closer
            elif not enemy.has_moved:
                best_move = self.find_best_move(enemy)
                if best_move:
                    # Remove from old position
                    self.grid[enemy.grid_y][enemy.grid_x] = None

                    # Move to new position
                    enemy.move_to(best_move[0], best_move[1])
                    self.grid[best_move[1]][best_move[0]] = enemy

                    # Try to attack after moving
                    if enemy.can_attack(self.player):
                        enemy.attack(self.player)
                        if self.player.hp <= 0:
                            self.state = GameState.GAME_OVER
                            return

            enemy.reset_turn()

        # Start player turn
        self.state = GameState.PLAYER_TURN

    def find_best_move(self, enemy):
        """Find the best move for an enemy unit (move towards player)."""
        valid_moves = self.get_valid_moves(enemy)
        if not valid_moves:
            return None

        # Find move that gets closest to player
        best_move = None
        best_distance = float("inf")

        for move_x, move_y in valid_moves:
            distance = abs(move_x - self.player.grid_x) + abs(
                move_y - self.player.grid_y
            )
            if distance < best_distance:
                best_distance = distance
                best_move = (move_x, move_y)

        return best_move

    def draw_grid(self):
        """Draw the game grid."""
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                rect_x = GRID_OFFSET_X + x * TILE_SIZE
                rect_y = GRID_OFFSET_Y + y * TILE_SIZE

                # Determine tile color
                if (x, y) in self.highlighted_tiles:
                    # Check if it's an attack highlight
                    is_attack = False
                    if self.selected_unit:
                        target = self.get_unit_at(x, y)
                        if target and not target.is_player:
                            is_attack = True

                    color = ORANGE if is_attack else GREEN
                else:
                    color = LIGHT_GRAY if (x + y) % 2 == 0 else WHITE

                pygame.draw.rect(screen, color, (rect_x, rect_y, TILE_SIZE, TILE_SIZE))
                pygame.draw.rect(
                    screen, GRAY, (rect_x, rect_y, TILE_SIZE, TILE_SIZE), 1
                )

    def draw_ui(self):
        """Draw UI elements."""
        # Turn indicator
        turn_text = ""
        if self.state == GameState.PLAYER_TURN:
            turn_text = "Your Turn"
            color = BLUE
        elif self.state == GameState.ENEMY_TURN:
            turn_text = "Enemy Turn"
            color = RED
        elif self.state == GameState.GAME_OVER:
            turn_text = "Defeat!"
            color = RED
        elif self.state == GameState.VICTORY:
            turn_text = "Victory!"
            color = GREEN

        text = self.font.render(turn_text, True, color)
        screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, 10))

        # End turn button
        if self.state == GameState.PLAYER_TURN:
            button_text = self.font.render(
                "End Turn (or make all actions)", True, WHITE
            )
            button_rect = pygame.Rect(SCREEN_WIDTH - 250, SCREEN_HEIGHT - 50, 240, 40)
            pygame.draw.rect(screen, DARK_BLUE, button_rect)
            pygame.draw.rect(screen, BLUE, button_rect, 2)
            screen.blit(button_text, (button_rect.x + 10, button_rect.y + 10))

        # Game over / victory message
        if self.state in [GameState.GAME_OVER, GameState.VICTORY]:
            msg = "Press R to Restart"
            text = self.font.render(msg, True, WHITE)
            screen.blit(
                text, (SCREEN_WIDTH // 2 - text.get_width() // 2, SCREEN_HEIGHT // 2)
            )

        # Instructions
        if self.state == GameState.PLAYER_TURN:
            inst_text = "Click your unit, then click to move or attack"
            text = self.font.render(inst_text, True, DARK_GRAY)
            screen.blit(text, (10, SCREEN_HEIGHT - 30))

    def draw(self):
        """Draw everything."""
        screen.fill(DARK_GRAY)
        self.draw_grid()

        # Draw units
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                unit = self.grid[y][x]
                if unit and unit.hp > 0:
                    unit.draw(screen, selected=(unit == self.selected_unit))

        self.draw_ui()

    def restart(self):
        """Restart the game."""
        self.__init__()


def main():
    game = Game()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    mouse_x, mouse_y = event.pos

                    # Convert to grid coordinates
                    grid_x = (mouse_x - GRID_OFFSET_X) // TILE_SIZE
                    grid_y = (mouse_y - GRID_OFFSET_Y) // TILE_SIZE

                    if 0 <= grid_x < GRID_SIZE and 0 <= grid_y < GRID_SIZE:
                        game.handle_click(grid_x, grid_y)

                    # Check end turn button
                    button_rect = pygame.Rect(
                        SCREEN_WIDTH - 250, SCREEN_HEIGHT - 50, 240, 40
                    )
                    if (
                        button_rect.collidepoint(mouse_x, mouse_y)
                        and game.state == GameState.PLAYER_TURN
                    ):
                        game.end_player_turn()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r and game.state in [
                    GameState.GAME_OVER,
                    GameState.VICTORY,
                ]:
                    game.restart()
                elif (
                    event.key == pygame.K_SPACE and game.state == GameState.PLAYER_TURN
                ):
                    game.end_player_turn()

            elif event.type == pygame.USEREVENT:
                # AI turn execution
                if game.state == GameState.ENEMY_TURN:
                    game.execute_enemy_turn()
                    pygame.time.set_timer(pygame.USEREVENT, 0)  # Stop timer

        game.draw()
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
