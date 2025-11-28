"""2048 puzzle game variant using Pygame.

A sliding tile puzzle where tiles with the same value merge when pushed
together. The goal is to create a tile with the value 2048 or higher.

Controls:
    Arrow keys: Slide tiles
    R: Restart game
    ESC: Quit game
"""

import random
import sys

import pygame

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 500
SCREEN_HEIGHT = 600
GRID_SIZE = 4
TILE_SIZE = 100
GAP = 10
BOARD_SIZE = GRID_SIZE * TILE_SIZE + (GRID_SIZE + 1) * GAP
TOP_OFFSET = SCREEN_HEIGHT - BOARD_SIZE
FPS = 60

# Colors
BACKGROUND_COLOR = (187, 173, 160)
EMPTY_TILE_COLOR = (205, 193, 180)
FONT_COLOR = (119, 110, 101)
TILE_COLORS = {
    2: (238, 228, 218),
    4: (237, 224, 200),
    8: (242, 177, 121),
    16: (245, 149, 99),
    32: (246, 124, 95),
    64: (246, 94, 59),
    128: (237, 207, 114),
    256: (237, 204, 97),
    512: (237, 200, 80),
    1024: (237, 197, 63),
    2048: (237, 194, 46),
}
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# Setup Screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("2048 - Challenge 8")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 55)
score_font = pygame.font.Font(None, 40)


class Game2048:
    def __init__(self):
        self.grid = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
        self.score = 0
        self.add_new_tile()
        self.add_new_tile()
        self.game_over = False

    def add_new_tile(self):
        empty_cells = [
            (r, c)
            for r in range(GRID_SIZE)
            for c in range(GRID_SIZE)
            if self.grid[r][c] == 0
        ]
        if empty_cells:
            r, c = random.choice(empty_cells)
            self.grid[r][c] = 2 if random.random() < 0.9 else 4

    def compress(self, grid):
        new_grid = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
        for r in range(GRID_SIZE):
            pos = 0
            for c in range(GRID_SIZE):
                if grid[r][c] != 0:
                    new_grid[r][pos] = grid[r][c]
                    pos += 1
        return new_grid

    def merge(self, grid):
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE - 1):
                if grid[r][c] != 0 and grid[r][c] == grid[r][c + 1]:
                    grid[r][c] *= 2
                    grid[r][c + 1] = 0
                    self.score += grid[r][c]
        return grid

    def reverse(self, grid):
        new_grid = []
        for r in range(GRID_SIZE):
            new_grid.append(grid[r][::-1])
        return new_grid

    def transpose(self, grid):
        new_grid = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                new_grid[r][c] = grid[c][r]
        return new_grid

    def move_left(self):
        new_grid = self.compress(self.grid)
        new_grid = self.merge(new_grid)
        new_grid = self.compress(new_grid)
        return new_grid

    def move_right(self):
        new_grid = self.reverse(self.grid)
        new_grid = self.compress(new_grid)
        new_grid = self.merge(new_grid)
        new_grid = self.compress(new_grid)
        new_grid = self.reverse(new_grid)
        return new_grid

    def move_up(self):
        new_grid = self.transpose(self.grid)
        new_grid = self.compress(new_grid)
        new_grid = self.merge(new_grid)
        new_grid = self.compress(new_grid)
        new_grid = self.transpose(new_grid)
        return new_grid

    def move_down(self):
        new_grid = self.transpose(self.grid)
        new_grid = self.reverse(new_grid)
        new_grid = self.compress(new_grid)
        new_grid = self.merge(new_grid)
        new_grid = self.compress(new_grid)
        new_grid = self.reverse(new_grid)
        new_grid = self.transpose(new_grid)
        return new_grid

    def move(self, direction):
        if self.game_over:
            return

        if direction == "UP":
            new_grid = self.move_up()
        elif direction == "DOWN":
            new_grid = self.move_down()
        elif direction == "LEFT":
            new_grid = self.move_left()
        elif direction == "RIGHT":
            new_grid = self.move_right()

        if new_grid != self.grid:
            self.grid = new_grid
            self.add_new_tile()
            if self.check_game_over():
                self.game_over = True

    def check_game_over(self):
        # Check for empty cells
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                if self.grid[r][c] == 0:
                    return False

        # Check for merges
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE - 1):
                if self.grid[r][c] == self.grid[r][c + 1]:
                    return False
        for r in range(GRID_SIZE - 1):
            for c in range(GRID_SIZE):
                if self.grid[r][c] == self.grid[r + 1][c]:
                    return False
        return True

    def draw(self, surface):
        surface.fill(BACKGROUND_COLOR)

        # Draw Score
        score_text = score_font.render(f"Score: {self.score}", True, WHITE)
        surface.blit(score_text, (20, 20))

        # Draw Grid
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                val = self.grid[r][c]
                color = (
                    TILE_COLORS.get(val, TILE_COLORS[2048])
                    if val > 0
                    else EMPTY_TILE_COLOR
                )
                rect = pygame.Rect(
                    GAP + c * (TILE_SIZE + GAP),
                    TOP_OFFSET + GAP + r * (TILE_SIZE + GAP),
                    TILE_SIZE,
                    TILE_SIZE,
                )
                pygame.draw.rect(surface, color, rect, border_radius=5)

                if val > 0:
                    text_color = FONT_COLOR if val < 8 else WHITE
                    text = font.render(str(val), True, text_color)
                    text_rect = text.get_rect(center=rect.center)
                    surface.blit(text, text_rect)

        if self.game_over:
            s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            s.set_alpha(128)
            s.fill(BLACK)
            surface.blit(s, (0, 0))

            msg = font.render("Game Over!", True, WHITE)
            rect = msg.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2))
            surface.blit(msg, rect)

            sub = score_font.render("Press SPACE to Restart", True, WHITE)
            sub_rect = sub.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 60))
            surface.blit(sub, sub_rect)

    def reset(self):
        self.grid = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
        self.score = 0
        self.add_new_tile()
        self.add_new_tile()
        self.game_over = False


def main():
    game = Game2048()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    game.move("UP")
                elif event.key == pygame.K_DOWN:
                    game.move("DOWN")
                elif event.key == pygame.K_LEFT:
                    game.move("LEFT")
                elif event.key == pygame.K_RIGHT:
                    game.move("RIGHT")
                elif event.key == pygame.K_SPACE and game.game_over:
                    game.reset()
                elif event.key == pygame.K_ESCAPE:
                    running = False

        game.draw(screen)
        pygame.display.update()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
