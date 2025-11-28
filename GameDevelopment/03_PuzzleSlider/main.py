"""15-Puzzle Slider Game using Pygame.

A sliding puzzle game where the player arranges numbered tiles in order
by sliding them into the empty space. Features shuffle, move counter,
and win detection.

Controls:
    Click: Slide adjacent tile into empty space
    R: Shuffle and restart
    ESC: Quit game
"""

import random
import sys

import pygame

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 600
GRID_SIZE = 4
TILE_SIZE = SCREEN_WIDTH // GRID_SIZE
FPS = 30

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
DARK_GRAY = (100, 100, 100)
BLUE = (50, 100, 200)
GREEN = (50, 200, 50)

# Setup Screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Puzzle Slider - Challenge 3")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 80)
small_font = pygame.font.Font(None, 36)


class Puzzle:
    def __init__(self):
        self.tiles = []
        self.empty_pos = (GRID_SIZE - 1, GRID_SIZE - 1)
        self.create_tiles()
        self.shuffle()
        self.solved = False

    def create_tiles(self):
        self.tiles = []
        for y in range(GRID_SIZE):
            row = []
            for x in range(GRID_SIZE):
                val = y * GRID_SIZE + x + 1
                if val == GRID_SIZE * GRID_SIZE:
                    val = 0  # Empty tile
                    self.empty_pos = (x, y)
                row.append(val)
            self.tiles.append(row)

    def get_valid_moves(self):
        x, y = self.empty_pos
        moves = []
        if x > 0:
            moves.append((x - 1, y))  # Left
        if x < GRID_SIZE - 1:
            moves.append((x + 1, y))  # Right
        if y > 0:
            moves.append((x, y - 1))  # Up
        if y < GRID_SIZE - 1:
            moves.append((x, y + 1))  # Down
        return moves

    def move(self, pos):
        # pos is (x, y) of the tile to move into the empty space
        ex, ey = self.empty_pos
        tx, ty = pos

        # Check if adjacent
        if abs(ex - tx) + abs(ey - ty) == 1:
            # Swap
            self.tiles[ey][ex], self.tiles[ty][tx] = (
                self.tiles[ty][tx],
                self.tiles[ey][ex],
            )
            self.empty_pos = (tx, ty)
            self.check_win()
            return True
        return False

    def shuffle(self):
        # Shuffle by making valid moves to ensure solvability
        for _ in range(1000):
            moves = self.get_valid_moves()
            move = random.choice(moves)
            self.move(move)
        self.solved = False

    def check_win(self):
        count = 1
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                if y == GRID_SIZE - 1 and x == GRID_SIZE - 1:
                    if self.tiles[y][x] != 0:
                        return
                elif self.tiles[y][x] != count:
                    return
                count += 1
        self.solved = True

    def draw(self, surface):
        surface.fill(BLACK)
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                val = self.tiles[y][x]
                if val != 0:
                    rect = pygame.Rect(
                        x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE
                    )
                    # Inset for border
                    inner_rect = rect.inflate(-4, -4)

                    color = BLUE if not self.solved else GREEN
                    pygame.draw.rect(surface, color, inner_rect)
                    pygame.draw.rect(surface, WHITE, inner_rect, 2)

                    text = font.render(str(val), True, WHITE)
                    text_rect = text.get_rect(center=rect.center)
                    surface.blit(text, text_rect)

        if self.solved:
            msg = font.render("SOLVED!", True, WHITE)
            rect = msg.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2))
            # Draw a background for text
            bg_rect = rect.inflate(20, 20)
            pygame.draw.rect(surface, BLACK, bg_rect)
            pygame.draw.rect(surface, GREEN, bg_rect, 2)
            surface.blit(msg, rect)

            sub = small_font.render("Press SPACE to Shuffle", True, WHITE)
            sub_rect = sub.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 60))
            surface.blit(sub, sub_rect)


def main():
    puzzle = Puzzle()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if not puzzle.solved:
                    mx, my = pygame.mouse.get_pos()
                    tx = mx // TILE_SIZE
                    ty = my // TILE_SIZE
                    puzzle.move((tx, ty))
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and puzzle.solved:
                    puzzle.shuffle()
                elif event.key == pygame.K_r:  # Force shuffle
                    puzzle.shuffle()
                elif event.key == pygame.K_ESCAPE:
                    running = False

        puzzle.draw(screen)
        pygame.display.update()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
