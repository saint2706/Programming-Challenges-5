"""Snake game with polished UX using Pygame.

A classic snake game implementation featuring smooth controls, score tracking,
and optional custom graphics. The snake grows when eating food and the game
ends on collision with walls or self.

Controls:
    Arrow keys: Move snake
    R: Restart after game over
    ESC: Quit game
"""

import os
import random
import sys

import pygame

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
GRID_SIZE = 20
GRID_WIDTH = SCREEN_WIDTH // GRID_SIZE
GRID_HEIGHT = SCREEN_HEIGHT // GRID_SIZE
FPS = 10

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (40, 40, 40)
RED = (255, 0, 0)
GREEN = (0, 255, 0)

# Setup Screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Snake - Challenge 1")
clock = pygame.time.Clock()


# Load Assets
def load_asset(name, scale=True):
    path = os.path.join("assets", name)
    if os.path.exists(path):
        img = pygame.image.load(path).convert_alpha()
        if scale:
            img = pygame.transform.scale(img, (GRID_SIZE, GRID_SIZE))
        return img
    return None


HEAD_IMG = load_asset("snake_head.png")
BODY_IMG = load_asset("snake_body.png")
APPLE_IMG = load_asset("apple.png")


class Snake:
    def __init__(self):
        self.length = 1
        self.positions = [((SCREEN_WIDTH // 2), (SCREEN_HEIGHT // 2))]
        self.direction = random.choice([UP, DOWN, LEFT, RIGHT])
        self.color = GREEN
        self.score = 0

    def get_head_position(self):
        return self.positions[0]

    def turn(self, point):
        if self.length > 1 and (point[0] * -1, point[1] * -1) == self.direction:
            return
        else:
            self.direction = point

    def move(self):
        cur = self.get_head_position()
        x, y = self.direction
        (
            ((cur[0] + (x * GRID_SIZE)) % SCREEN_WIDTH),
            (cur[1] + (y * GRID_SIZE)) % SCREEN_HEIGHT,
        )

        # Check for self collision (classic snake rules usually kill you, but wrapping is also a variant.
        # Let's do wall death for "Polished UX" usually implies standard rules, but wrapping is easier for beginners.
        # Let's implement wall death.
        new_x = cur[0] + (x * GRID_SIZE)
        new_y = cur[1] + (y * GRID_SIZE)

        if new_x < 0 or new_x >= SCREEN_WIDTH or new_y < 0 or new_y >= SCREEN_HEIGHT:
            return False  # Game Over

        if (new_x, new_y) in self.positions[2:]:
            return False  # Game Over

        self.positions.insert(0, (new_x, new_y))
        if len(self.positions) > self.length:
            self.positions.pop()
        return True

    def reset(self):
        self.length = 1
        self.positions = [((SCREEN_WIDTH // 2), (SCREEN_HEIGHT // 2))]
        self.direction = random.choice([UP, DOWN, LEFT, RIGHT])
        self.score = 0

    def draw(self, surface):
        for index, p in enumerate(self.positions):
            r = pygame.Rect((p[0], p[1]), (GRID_SIZE, GRID_SIZE))
            if index == 0 and HEAD_IMG:
                # Rotate head based on direction
                angle = 0
                if self.direction == UP:
                    angle = 90
                elif self.direction == DOWN:
                    angle = -90
                elif self.direction == LEFT:
                    angle = 180
                elif self.direction == RIGHT:
                    angle = 0

                rotated_head = pygame.transform.rotate(HEAD_IMG, angle)
                surface.blit(rotated_head, r)
            elif BODY_IMG:
                surface.blit(BODY_IMG, r)
            else:
                pygame.draw.rect(surface, self.color, r)
                pygame.draw.rect(surface, BLACK, r, 1)


class Food:
    def __init__(self):
        self.position = (0, 0)
        self.color = RED
        self.randomize_position()

    def randomize_position(self):
        self.position = (
            random.randint(0, GRID_WIDTH - 1) * GRID_SIZE,
            random.randint(0, GRID_HEIGHT - 1) * GRID_SIZE,
        )

    def draw(self, surface):
        r = pygame.Rect((self.position[0], self.position[1]), (GRID_SIZE, GRID_SIZE))
        if APPLE_IMG:
            surface.blit(APPLE_IMG, r)
        else:
            pygame.draw.rect(surface, self.color, r)
            pygame.draw.rect(surface, BLACK, r, 1)


# Directions
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)


def draw_grid(surface):
    for y in range(0, int(SCREEN_HEIGHT), int(GRID_SIZE)):
        for x in range(0, int(SCREEN_WIDTH), int(GRID_SIZE)):
            r = pygame.Rect(x, y, GRID_SIZE, GRID_SIZE)
            pygame.draw.rect(surface, GRAY, r, 1)


def main():
    snake = Snake()
    food = Food()

    # Font
    font = pygame.font.Font(None, 36)

    running = True
    game_over = False

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    snake.turn(UP)
                elif event.key == pygame.K_DOWN:
                    snake.turn(DOWN)
                elif event.key == pygame.K_LEFT:
                    snake.turn(LEFT)
                elif event.key == pygame.K_RIGHT:
                    snake.turn(RIGHT)
                elif event.key == pygame.K_r and game_over:
                    snake.reset()
                    food.randomize_position()
                    game_over = False
                elif event.key == pygame.K_ESCAPE:
                    running = False

        if not game_over:
            if not snake.move():
                game_over = True

            if snake.get_head_position() == food.position:
                snake.length += 1
                snake.score += 1
                food.randomize_position()
                # Ensure food doesn't spawn on snake
                while food.position in snake.positions:
                    food.randomize_position()

        # Draw
        screen.fill(BLACK)
        # draw_grid(screen) # Optional, maybe looks better without for "polished" look

        snake.draw(screen)
        food.draw(screen)

        # Score
        score_text = font.render(f"Score: {snake.score}", True, WHITE)
        screen.blit(score_text, (10, 10))

        if game_over:
            game_over_text = font.render("Game Over! Press R to Restart", True, WHITE)
            text_rect = game_over_text.get_rect(
                center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
            )
            screen.blit(game_over_text, text_rect)

        pygame.display.update()
        clock.tick(FPS + (snake.score // 5))  # Increase speed slightly

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
