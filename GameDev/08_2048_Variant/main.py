import pygame
import sys
import random

# Configuration
SCREEN_SIZE = 600
GRID_SIZE = 4
TILE_SIZE = 140
PADDING = 10
FPS = 30

# Colors
BACKGROUND = (187, 173, 160)
EMPTY_TILE = (205, 193, 180)
TEXT_COLOR = (119, 110, 101)
LIGHT_TEXT = (249, 246, 242)

TILE_COLORS = {
    0: (205, 193, 180),
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
    2048: (237, 194, 46)
}

class Game2048:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_SIZE, SCREEN_SIZE))
        pygame.display.set_caption("2048 - Challenge #08")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 40, bold=True)
        self.score_font = pygame.font.SysFont("Arial", 24)

        self.reset_game()

    def reset_game(self):
        self.grid = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.score = 0
        self.game_over = False
        self.won = False
        self.spawn_tile()
        self.spawn_tile()

    def spawn_tile(self):
        empty_cells = [(r, c) for r in range(GRID_SIZE) for c in range(GRID_SIZE) if self.grid[r][c] == 0]
        if empty_cells:
            r, c = random.choice(empty_cells)
            self.grid[r][c] = 4 if random.random() > 0.9 else 2

    def compress(self, grid):
        new_grid = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
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
                if grid[r][c] != 0 and grid[r][c] == grid[r][c+1]:
                    grid[r][c] *= 2
                    self.score += grid[r][c]
                    grid[r][c+1] = 0
                    if grid[r][c] == 2048:
                        self.won = True
        return grid

    def reverse(self, grid):
        new_grid = []
        for r in range(GRID_SIZE):
            new_grid.append(grid[r][::-1])
        return new_grid

    def transpose(self, grid):
        new_grid = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                new_grid[c][r] = grid[r][c]
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

    def check_move(self, new_grid):
        if new_grid != self.grid:
            self.grid = new_grid
            self.spawn_tile()
            if not self.can_move():
                self.game_over = True

    def can_move(self):
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                if self.grid[r][c] == 0: return True
                if c < GRID_SIZE - 1 and self.grid[r][c] == self.grid[r][c+1]: return True
                if r < GRID_SIZE - 1 and self.grid[r][c] == self.grid[r+1][c]: return True
        return False

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if event.key == pygame.K_r:
                    self.reset_game()

                if not self.game_over:
                    if event.key == pygame.K_LEFT:
                        self.check_move(self.move_left())
                    elif event.key == pygame.K_RIGHT:
                        self.check_move(self.move_right())
                    elif event.key == pygame.K_UP:
                        self.check_move(self.move_up())
                    elif event.key == pygame.K_DOWN:
                        self.check_move(self.move_down())

    def draw(self):
        self.screen.fill(BACKGROUND)

        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                val = self.grid[r][c]
                color = TILE_COLORS.get(val, TILE_COLORS[2048])
                rect = pygame.Rect(
                    c * (TILE_SIZE + PADDING) + PADDING,
                    r * (TILE_SIZE + PADDING) + PADDING,
                    TILE_SIZE, TILE_SIZE
                )
                pygame.draw.rect(self.screen, color, rect, border_radius=5)

                if val != 0:
                    text_color = TEXT_COLOR if val <= 4 else LIGHT_TEXT
                    surf = self.font.render(str(val), True, text_color)
                    rect_surf = surf.get_rect(center=rect.center)
                    self.screen.blit(surf, rect_surf)

        if self.game_over:
             s = pygame.Surface((SCREEN_SIZE, SCREEN_SIZE), pygame.SRCALPHA)
             s.fill((255, 255, 255, 128))
             self.screen.blit(s, (0,0))

             msg = self.font.render("Game Over!", True, TEXT_COLOR)
             self.screen.blit(msg, (SCREEN_SIZE//2 - 100, SCREEN_SIZE//2))

        elif self.won:
             msg = self.font.render("You Win!", True, (255, 215, 0))
             self.screen.blit(msg, (10, 10)) # Simple win indicator

        pygame.display.flip()

    def run(self):
        while True:
            self.handle_input()
            self.draw()
            self.clock.tick(FPS)

if __name__ == "__main__":
    game = Game2048()
    game.run()
