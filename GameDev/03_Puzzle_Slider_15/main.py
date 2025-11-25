import pygame
import sys
import random

# Configuration
SCREEN_SIZE = 600
GRID_SIZE = 4
TILE_SIZE = SCREEN_SIZE // GRID_SIZE
FPS = 30

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
DARK_GRAY = (50, 50, 50)
GREEN = (50, 200, 50)
BLUE = (50, 100, 200)

class PuzzleGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_SIZE, SCREEN_SIZE))
        pygame.display.set_caption("15-Puzzle - Challenge #03")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 40)

        self.tiles = []
        self.empty_pos = (GRID_SIZE - 1, GRID_SIZE - 1)
        self.solved_state = []
        self.init_grid()
        self.shuffle()

    def init_grid(self):
        # Create solved state
        self.tiles = []
        count = 1
        for y in range(GRID_SIZE):
            row = []
            for x in range(GRID_SIZE):
                if count < GRID_SIZE * GRID_SIZE:
                    row.append(count)
                    count += 1
                else:
                    row.append(0) # 0 represents empty
            self.tiles.append(row)

        self.empty_pos = (GRID_SIZE - 1, GRID_SIZE - 1)

    def is_solvable(self, flat_list):
        # Count inversions
        inversions = 0
        for i in range(len(flat_list)):
            for j in range(i + 1, len(flat_list)):
                if flat_list[i] != 0 and flat_list[j] != 0 and flat_list[i] > flat_list[j]:
                    inversions += 1

        # Grid width is even
        if GRID_SIZE % 2 == 0:
            # If blank is on an even row counting from bottom
            # (In 0-indexed from top: 3 is odd from bottom (row 1), 2 is even (row 2), etc.)
            # Wait, standard formula:
            # If grid width is even, solvable if (inversions + row_of_blank_from_bottom) is odd.
            # Row 3 (bottom) is 1 (odd). Row 2 is 2 (even).
            empty_row_from_bottom = GRID_SIZE - self.empty_pos[1]
            if empty_row_from_bottom % 2 == 0:
                return inversions % 2 != 0
            else:
                return inversions % 2 == 0
        else:
            return inversions % 2 == 0

    def shuffle(self):
        # Simple shuffle: just perform random valid moves
        # This guarantees solvability without complex math checks
        for _ in range(1000):
            moves = []
            r, c = self.empty_pos
            if r > 0: moves.append((r - 1, c))
            if r < GRID_SIZE - 1: moves.append((r + 1, c))
            if c > 0: moves.append((r, c - 1))
            if c < GRID_SIZE - 1: moves.append((r, c + 1))

            target = random.choice(moves)
            self.swap(target, self.empty_pos)
            self.empty_pos = target

    def swap(self, pos1, pos2):
        r1, c1 = pos1
        r2, c2 = pos2
        self.tiles[r1][c1], self.tiles[r2][c2] = self.tiles[r2][c2], self.tiles[r1][c1]

    def check_win(self):
        count = 1
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                if y == GRID_SIZE - 1 and x == GRID_SIZE - 1:
                    if self.tiles[y][x] != 0: return False
                elif self.tiles[y][x] != count:
                    return False
                count += 1
        return True

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
                    self.shuffle()

                # Arrow keys move the tile INTO the empty space
                # e.g. UP key means "Empty space moves UP" (swapping with tile above)
                # Or standard interpretation: UP key moves the tile BELOW the empty space UP?
                # Usually arrows control the sliding tile.
                # If I press DOWN, I expect the tile ABOVE the empty space to move DOWN?
                # Let's assume arrows move the "camera" or the empty slot.
                # Let's do: Arrow moves the empty slot.
                r, c = self.empty_pos
                target = None
                if event.key == pygame.K_UP and r > 0: target = (r - 1, c)
                elif event.key == pygame.K_DOWN and r < GRID_SIZE - 1: target = (r + 1, c)
                elif event.key == pygame.K_LEFT and c > 0: target = (r, c - 1)
                elif event.key == pygame.K_RIGHT and c < GRID_SIZE - 1: target = (r, c + 1)

                if target:
                    self.swap(target, self.empty_pos)
                    self.empty_pos = target

            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                c = mx // TILE_SIZE
                r = my // TILE_SIZE

                # Check adjacency
                er, ec = self.empty_pos
                if abs(r - er) + abs(c - ec) == 1:
                    self.swap((r, c), self.empty_pos)
                    self.empty_pos = (r, c)

    def draw(self):
        self.screen.fill(BLACK)

        is_win = self.check_win()

        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                val = self.tiles[r][c]
                if val != 0:
                    rect = pygame.Rect(c * TILE_SIZE, r * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                    color = GREEN if is_win else BLUE
                    pygame.draw.rect(self.screen, color, rect)
                    pygame.draw.rect(self.screen, WHITE, rect, 2)

                    text = self.font.render(str(val), True, WHITE)
                    text_rect = text.get_rect(center=rect.center)
                    self.screen.blit(text, text_rect)

        if is_win:
             text = self.font.render("SOLVED! Press R", True, WHITE)
             # Draw with shadow
             text_rect = text.get_rect(center=(SCREEN_SIZE // 2, SCREEN_SIZE // 2))
             pygame.draw.rect(self.screen, BLACK, text_rect.inflate(20, 20))
             self.screen.blit(text, text_rect)

        pygame.display.flip()

    def run(self):
        while True:
            self.handle_input()
            self.draw()
            self.clock.tick(FPS)

if __name__ == "__main__":
    game = PuzzleGame()
    game.run()
