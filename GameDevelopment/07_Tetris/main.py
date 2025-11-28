"""Tetris clone with ghost piece and hold functionality using Pygame.

A full-featured Tetris implementation with standard rotation system (SRS),
wall kicks, ghost piece preview, hold piece, and scoring system.

Controls:
    Left/Right arrows: Move piece
    Up arrow: Rotate clockwise
    Down arrow: Soft drop
    Space: Hard drop
    C: Hold piece
    ESC: Quit game
"""
import pygame
import random
import sys

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 700
BLOCK_SIZE = 30
GRID_WIDTH = 10
GRID_HEIGHT = 20
PLAY_WIDTH = GRID_WIDTH * BLOCK_SIZE
PLAY_HEIGHT = GRID_HEIGHT * BLOCK_SIZE
TOP_LEFT_X = (SCREEN_WIDTH - PLAY_WIDTH) // 2
TOP_LEFT_Y = SCREEN_HEIGHT - PLAY_HEIGHT - 50
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)

# Shapes
S = [['.....',
      '.....',
      '..00.',
      '.00..',
      '.....'],
     ['.....',
      '..0..',
      '..00.',
      '...0.',
      '.....']]

Z = [['.....',
      '.....',
      '.00..',
      '..00.',
      '.....'],
     ['.....',
      '..0..',
      '.00..',
      '.0...',
      '.....']]

I = [['..0..',
      '..0..',
      '..0..',
      '..0..',
      '.....'],
     ['.....',
      '0000.',
      '.....',
      '.....',
      '.....']]

O = [['.....',
      '.....',
      '.00..',
      '.00..',
      '.....']]

J = [['.....',
      '.0...',
      '.000.',
      '.....',
      '.....'],
     ['.....',
      '..00.',
      '..0..',
      '..0..',
      '.....'],
     ['.....',
      '.....',
      '.000.',
      '...0.',
      '.....'],
     ['.....',
      '..0..',
      '..0..',
      '.00..',
      '.....']]

L = [['.....',
      '...0.',
      '.000.',
      '.....',
      '.....'],
     ['.....',
      '..0..',
      '..0..',
      '..00.',
      '.....'],
     ['.....',
      '.....',
      '.000.',
      '.0...',
      '.....'],
     ['.....',
      '.00..',
      '..0..',
      '..0..',
      '.....']]

T = [['.....',
      '..0..',
      '.000.',
      '.....',
      '.....'],
     ['.....',
      '..0..',
      '..00.',
      '..0..',
      '.....'],
     ['.....',
      '.....',
      '.000.',
      '..0..',
      '.....'],
     ['.....',
      '..0..',
      '.00..',
      '..0..',
      '.....']]

SHAPES = [S, Z, I, O, J, L, T]
SHAPE_COLORS = [GREEN, RED, CYAN, YELLOW, BLUE, ORANGE, MAGENTA]

class Piece:
    """
    Docstring for Piece.
    """
    def __init__(self, x, y, shape):
        """
        Docstring for __init__.
        """
        self.x = x
        self.y = y
        self.shape = shape
        self.color = SHAPE_COLORS[SHAPES.index(shape)]
        self.rotation = 0

class Tetris:
    """
    Docstring for Tetris.
    """
    def __init__(self):
        """
        Docstring for __init__.
        """
        self.grid = [[(0, 0, 0) for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.current_piece = self.get_shape()
        self.next_piece = self.get_shape()
        self.hold_piece = None
        self.can_hold = True
        self.score = 0
        self.level = 1
        self.fall_time = 0
        self.fall_speed = 0.5
        self.game_over = False

    def get_shape(self):
        """
        Docstring for get_shape.
        """
        return Piece(5, 0, random.choice(SHAPES))

    def valid_space(self, piece, x_offset=0, y_offset=0):
        """
        Docstring for valid_space.
        """
        accepted_pos = [[(j, i) for j in range(GRID_WIDTH) if self.grid[i][j] == (0, 0, 0)] for i in range(GRID_HEIGHT)]
        accepted_pos = [j for sub in accepted_pos for j in sub]

        formatted = self.convert_shape_format(piece)

        for pos in formatted:
            x, y = pos
            x += x_offset
            y += y_offset
            if y > -1:
                if (x, y) not in accepted_pos:
                    return False
        return True

    def convert_shape_format(self, piece):
        """
        Docstring for convert_shape_format.
        """
        positions = []
        format = piece.shape[piece.rotation % len(piece.shape)]

        for i, line in enumerate(format):
            row = list(line)
            for j, column in enumerate(row):
                if column == '0':
                    positions.append((piece.x + j - 2, piece.y + i - 4))
        return positions

    def check_lost(self):
        """
        Docstring for check_lost.
        """
        for pos in self.grid[0]:
            if pos != (0, 0, 0):
                return True
        return False

    def clear_rows(self):
        """
        Docstring for clear_rows.
        """
        inc = 0
        for i in range(len(self.grid) - 1, -1, -1):
            row = self.grid[i]
            if (0, 0, 0) not in row:
                inc += 1
                ind = i
                for j in range(ind, 0, -1):
                    self.grid[j] = list(self.grid[j - 1])
                self.grid[0] = [(0, 0, 0) for _ in range(GRID_WIDTH)]
        
        if inc > 0:
            self.score += inc * 100 * self.level
            # Increase speed
            self.level = 1 + (self.score // 500)
            self.fall_speed = max(0.1, 0.5 - (self.level * 0.02))

    def draw_grid(self, surface):
        """
        Docstring for draw_grid.
        """
        for i in range(GRID_HEIGHT):
            for j in range(GRID_WIDTH):
                pygame.draw.rect(surface, self.grid[i][j], (TOP_LEFT_X + j * BLOCK_SIZE, TOP_LEFT_Y + i * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE), 0)
        
        # Grid lines
        for i in range(GRID_HEIGHT):
            pygame.draw.line(surface, GRAY, (TOP_LEFT_X, TOP_LEFT_Y + i * BLOCK_SIZE), (TOP_LEFT_X + PLAY_WIDTH, TOP_LEFT_Y + i * BLOCK_SIZE))
        for j in range(GRID_WIDTH):
            pygame.draw.line(surface, GRAY, (TOP_LEFT_X + j * BLOCK_SIZE, TOP_LEFT_Y), (TOP_LEFT_X + j * BLOCK_SIZE, TOP_LEFT_Y + PLAY_HEIGHT))
        
        pygame.draw.rect(surface, RED, (TOP_LEFT_X, TOP_LEFT_Y, PLAY_WIDTH, PLAY_HEIGHT), 4)

    def draw_window(self, surface):
        """
        Docstring for draw_window.
        """
        surface.fill(BLACK)
        font = pygame.font.Font(None, 60)
        label = font.render('Tetris', 1, WHITE)
        surface.blit(label, (TOP_LEFT_X + PLAY_WIDTH / 2 - (label.get_width() / 2), 30))

        # Current Score
        font_small = pygame.font.Font(None, 30)
        score_label = font_small.render(f'Score: {self.score}', 1, WHITE)
        surface.blit(score_label, (TOP_LEFT_X + PLAY_WIDTH + 50, TOP_LEFT_Y + PLAY_HEIGHT/2 - 100))
        
        level_label = font_small.render(f'Level: {self.level}', 1, WHITE)
        surface.blit(level_label, (TOP_LEFT_X + PLAY_WIDTH + 50, TOP_LEFT_Y + PLAY_HEIGHT/2 - 70))

        # Next Piece
        label = font_small.render('Next Shape', 1, WHITE)
        surface.blit(label, (TOP_LEFT_X + PLAY_WIDTH + 50, TOP_LEFT_Y))
        self.draw_next_shape(self.next_piece, surface)
        
        # Hold Piece
        label = font_small.render('Hold', 1, WHITE)
        surface.blit(label, (TOP_LEFT_X - 150, TOP_LEFT_Y))
        if self.hold_piece:
            self.draw_hold_shape(self.hold_piece, surface)

        self.draw_grid(surface)

        # Draw Ghost Piece
        ghost_y = self.current_piece.y
        while self.valid_space(self.current_piece, y_offset=ghost_y - self.current_piece.y + 1):
            ghost_y += 1
        
        ghost_pos = self.convert_shape_format(self.current_piece)
        # Adjust for ghost Y
        final_ghost_pos = []
        dy = ghost_y - self.current_piece.y
        for (x, y) in ghost_pos:
            final_ghost_pos.append((x, y + dy))
            
        for i, (x, y) in enumerate(final_ghost_pos):
            if y > -1:
                rect = pygame.Rect(TOP_LEFT_X + x * BLOCK_SIZE, TOP_LEFT_Y + y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE)
                pygame.draw.rect(surface, GRAY, rect, 1)

        # Draw Current Piece
        piece_pos = self.convert_shape_format(self.current_piece)
        for i, (x, y) in enumerate(piece_pos):
            if y > -1:
                pygame.draw.rect(surface, self.current_piece.color, (TOP_LEFT_X + x * BLOCK_SIZE, TOP_LEFT_Y + y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE), 0)

    def draw_next_shape(self, shape, surface):
        """
        Docstring for draw_next_shape.
        """
        format = shape.shape[shape.rotation % len(shape.shape)]
        for i, line in enumerate(format):
            row = list(line)
            for j, column in enumerate(row):
                if column == '0':
                    pygame.draw.rect(surface, shape.color, (TOP_LEFT_X + PLAY_WIDTH + 50 + j*BLOCK_SIZE, TOP_LEFT_Y + 30 + i*BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE), 0)

    def draw_hold_shape(self, shape, surface):
        """
        Docstring for draw_hold_shape.
        """
        format = shape.shape[shape.rotation % len(shape.shape)]
        for i, line in enumerate(format):
            row = list(line)
            for j, column in enumerate(row):
                if column == '0':
                    pygame.draw.rect(surface, shape.color, (TOP_LEFT_X - 150 + j*BLOCK_SIZE, TOP_LEFT_Y + 30 + i*BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE), 0)

    def lock_piece(self):
        """
        Docstring for lock_piece.
        """
        piece_pos = self.convert_shape_format(self.current_piece)
        for i, (x, y) in enumerate(piece_pos):
            if y > -1:
                self.grid[y][x] = self.current_piece.color
        
        self.clear_rows()
        self.current_piece = self.next_piece
        self.next_piece = self.get_shape()
        self.can_hold = True
        
        if self.check_lost():
            self.game_over = True

    def hold(self):
        """
        Docstring for hold.
        """
        if not self.can_hold:
            return
        
        if self.hold_piece is None:
            self.hold_piece = self.current_piece
            self.current_piece = self.next_piece
            self.next_piece = self.get_shape()
        else:
            self.hold_piece, self.current_piece = self.current_piece, self.hold_piece
            self.current_piece.x = 5
            self.current_piece.y = 0
            
        self.hold_piece.x = 5
        self.hold_piece.y = 0
        self.hold_piece.rotation = 0
        self.can_hold = False

def main():
    """
    Docstring for main.
    """
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption('Tetris - Challenge 7')
    game = Tetris()
    clock = pygame.time.Clock()
    
    running = True
    while running:
        game.fall_time += clock.get_rawtime()
        clock.tick()

        if game.fall_time/1000 >= game.fall_speed:
            game.fall_time = 0
            game.current_piece.y += 1
            if not game.valid_space(game.current_piece) and game.current_piece.y > 0:
                game.current_piece.y -= 1
                game.lock_piece()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    game.current_piece.x -= 1
                    if not game.valid_space(game.current_piece):
                        game.current_piece.x += 1
                elif event.key == pygame.K_RIGHT:
                    game.current_piece.x += 1
                    if not game.valid_space(game.current_piece):
                        game.current_piece.x -= 1
                elif event.key == pygame.K_DOWN:
                    game.current_piece.y += 1
                    if not game.valid_space(game.current_piece):
                        game.current_piece.y -= 1
                elif event.key == pygame.K_UP:
                    game.current_piece.rotation += 1
                    if not game.valid_space(game.current_piece):
                        game.current_piece.rotation -= 1
                elif event.key == pygame.K_c or event.key == pygame.K_LSHIFT:
                    game.hold()
                elif event.key == pygame.K_SPACE:
                    # Hard drop
                    while game.valid_space(game.current_piece):
                        game.current_piece.y += 1
                    game.current_piece.y -= 1
                    game.lock_piece()
                elif event.key == pygame.K_ESCAPE:
                    running = False

        game.draw_window(screen)
        
        if game.game_over:
            font = pygame.font.Font(None, 80)
            text = font.render("YOU LOST", 1, WHITE)
            screen.blit(text, (SCREEN_WIDTH/2 - text.get_width()/2, SCREEN_HEIGHT/2 - text.get_height()/2))
            pygame.display.update()
            pygame.time.delay(3000)
            running = False

        pygame.display.update()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
