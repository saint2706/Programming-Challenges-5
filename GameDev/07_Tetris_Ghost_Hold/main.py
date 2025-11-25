import pygame
import sys
import random

# Configuration
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 700
GRID_COLS = 10
GRID_ROWS = 20
BLOCK_SIZE = 30
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (50, 50, 50)
LIGHT_GRAY = (100, 100, 100)

COLORS = [
    (0, 0, 0),       # 0: Empty
    (0, 255, 255),   # 1: I - Cyan
    (0, 0, 255),     # 2: J - Blue
    (255, 165, 0),   # 3: L - Orange
    (255, 255, 0),   # 4: O - Yellow
    (0, 255, 0),     # 5: S - Green
    (128, 0, 128),   # 6: T - Purple
    (255, 0, 0)      # 7: Z - Red
]

# Tetromino shapes
SHAPES = [
    [],
    [[1, 1, 1, 1]], # I
    [[1, 0, 0], [1, 1, 1]], # J
    [[0, 0, 1], [1, 1, 1]], # L
    [[1, 1], [1, 1]], # O
    [[0, 1, 1], [1, 1, 0]], # S
    [[0, 1, 0], [1, 1, 1]], # T
    [[1, 1, 0], [0, 1, 1]]  # Z
]

class TetrisGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Tetris - Challenge #07")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 24)

        # Grid offset to center it
        self.offset_x = (SCREEN_WIDTH - GRID_COLS * BLOCK_SIZE) // 2
        self.offset_y = (SCREEN_HEIGHT - GRID_ROWS * BLOCK_SIZE) // 2

        self.grid = [[0 for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]
        self.score = 0
        self.game_over = False

        self.bag = []
        self.current_piece = self.new_piece()
        self.next_piece = self.new_piece()
        self.hold_piece_type = 0
        self.can_hold = True

        self.fall_time = 0
        self.fall_speed = 0.5 # seconds
        self.last_time = pygame.time.get_ticks()

    def new_piece(self):
        if not self.bag:
            self.bag = list(range(1, 8))
            random.shuffle(self.bag)

        type_idx = self.bag.pop()
        shape = SHAPES[type_idx]
        return {
            'type': type_idx,
            'shape': shape,
            'x': GRID_COLS // 2 - len(shape[0]) // 2,
            'y': 0
        }

    def rotate(self, shape):
        return [ [ shape[y][x] for y in range(len(shape)) ] for x in range(len(shape[0]) - 1, -1, -1) ]

    def valid_move(self, piece, adj_x=0, adj_y=0, new_shape=None):
        shape = new_shape if new_shape else piece['shape']
        for y, row in enumerate(shape):
            for x, cell in enumerate(row):
                if cell:
                    px = piece['x'] + x + adj_x
                    py = piece['y'] + y + adj_y

                    if px < 0 or px >= GRID_COLS or py >= GRID_ROWS:
                        return False
                    if py >= 0 and self.grid[py][px]:
                        return False
        return True

    def lock_piece(self):
        for y, row in enumerate(self.current_piece['shape']):
            for x, cell in enumerate(row):
                if cell:
                    px = self.current_piece['x'] + x
                    py = self.current_piece['y'] + y
                    if py >= 0:
                        self.grid[py][px] = self.current_piece['type']

        # Clear lines
        new_grid = [row for row in self.grid if any(c == 0 for c in row)]
        lines_cleared = GRID_ROWS - len(new_grid)
        if lines_cleared > 0:
            for _ in range(lines_cleared):
                new_grid.insert(0, [0] * GRID_COLS)
            self.grid = new_grid
            self.score += lines_cleared * 100

        self.current_piece = self.next_piece
        self.next_piece = self.new_piece()
        self.can_hold = True

        if not self.valid_move(self.current_piece):
            self.game_over = True

    def hard_drop(self):
        while self.valid_move(self.current_piece, adj_y=1):
            self.current_piece['y'] += 1
        self.lock_piece()

    def hold(self):
        if not self.can_hold: return

        if self.hold_piece_type == 0:
            self.hold_piece_type = self.current_piece['type']
            self.current_piece = self.next_piece
            self.next_piece = self.new_piece()
        else:
            self.hold_piece_type, self.current_piece['type'] = self.current_piece['type'], self.hold_piece_type
            self.current_piece['shape'] = SHAPES[self.current_piece['type']]
            self.current_piece['x'] = GRID_COLS // 2 - len(self.current_piece['shape'][0]) // 2
            self.current_piece['y'] = 0

        self.can_hold = False

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

                if not self.game_over:
                    if event.key == pygame.K_LEFT:
                        if self.valid_move(self.current_piece, adj_x=-1):
                            self.current_piece['x'] -= 1
                    elif event.key == pygame.K_RIGHT:
                        if self.valid_move(self.current_piece, adj_x=1):
                            self.current_piece['x'] += 1
                    elif event.key == pygame.K_DOWN:
                        if self.valid_move(self.current_piece, adj_y=1):
                            self.current_piece['y'] += 1
                    elif event.key == pygame.K_UP:
                        new_shape = self.rotate(self.current_piece['shape'])
                        if self.valid_move(self.current_piece, new_shape=new_shape):
                            self.current_piece['shape'] = new_shape
                    elif event.key == pygame.K_SPACE:
                        self.hard_drop()
                    elif event.key == pygame.K_c:
                        self.hold()
                    elif event.key == pygame.K_r and self.game_over:
                        self.__init__() # Cheap restart

    def update(self):
        if self.game_over: return

        now = pygame.time.get_ticks()
        if now - self.last_time > self.fall_speed * 1000:
            if self.valid_move(self.current_piece, adj_y=1):
                self.current_piece['y'] += 1
            else:
                self.lock_piece()
            self.last_time = now

    def draw_grid(self):
        pygame.draw.rect(self.screen, GRAY, (self.offset_x, self.offset_y, GRID_COLS * BLOCK_SIZE, GRID_ROWS * BLOCK_SIZE), 2)

        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                val = self.grid[r][c]
                if val:
                    color = COLORS[val]
                    rect = (self.offset_x + c * BLOCK_SIZE, self.offset_y + r * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE)
                    pygame.draw.rect(self.screen, color, rect)
                    pygame.draw.rect(self.screen, BLACK, rect, 1)

    def draw_piece(self, piece, ghost=False):
        shape = piece['shape']
        for r, row in enumerate(shape):
            for c, cell in enumerate(row):
                if cell:
                    x = self.offset_x + (piece['x'] + c) * BLOCK_SIZE
                    y = self.offset_y + (piece['y'] + r) * BLOCK_SIZE
                    color = COLORS[piece['type']]

                    if ghost:
                        # Draw outline only
                        pygame.draw.rect(self.screen, color, (x, y, BLOCK_SIZE, BLOCK_SIZE), 1)
                    else:
                        pygame.draw.rect(self.screen, color, (x, y, BLOCK_SIZE, BLOCK_SIZE))
                        pygame.draw.rect(self.screen, BLACK, (x, y, BLOCK_SIZE, BLOCK_SIZE), 1)

    def draw(self):
        self.screen.fill(BLACK)
        self.draw_grid()

        if not self.game_over:
            # Calculate Ghost Position
            ghost_y = self.current_piece['y']
            while self.valid_move(self.current_piece, adj_y=ghost_y - self.current_piece['y'] + 1):
                ghost_y += 1

            ghost_piece = self.current_piece.copy()
            ghost_piece['y'] = ghost_y
            self.draw_piece(ghost_piece, ghost=True)

            # Draw Current Piece
            self.draw_piece(self.current_piece)

        # HUD
        score_surf = self.font.render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_surf, (10, 10))

        hold_surf = self.font.render(f"Hold: {self.hold_piece_type}", True, WHITE) # Simplified hold display
        self.screen.blit(hold_surf, (10, 40))

        if self.game_over:
            go_surf = self.font.render("GAME OVER", True, WHITE)
            self.screen.blit(go_surf, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT // 2))

        pygame.display.flip()

    def run(self):
        while True:
            self.handle_input()
            self.update()
            self.draw()
            self.clock.tick(FPS)

if __name__ == "__main__":
    game = TetrisGame()
    game.run()
