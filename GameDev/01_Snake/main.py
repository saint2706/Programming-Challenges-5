import pygame
import sys
import random
import os

# Configuration
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
GRID_SIZE = 20
FPS = 15

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
GRAY = (100, 100, 100)
DARK_GRAY = (40, 40, 40)
BLUE = (50, 50, 255)

# Directions
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

HIGHSCORE_FILE = "highscore.txt"

class SnakeGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Snake - Challenge #01")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 24)
        self.large_font = pygame.font.SysFont("Arial", 48)

        self.state = "START"  # START, PLAYING, PAUSED, GAMEOVER
        self.score = 0
        self.high_score = self.load_high_score()
        self.reset_game()

    def load_high_score(self):
        if os.path.exists(HIGHSCORE_FILE):
            try:
                with open(HIGHSCORE_FILE, "r") as f:
                    return int(f.read().strip())
            except:
                return 0
        return 0

    def save_high_score(self):
        with open(HIGHSCORE_FILE, "w") as f:
            f.write(str(self.high_score))

    def reset_game(self):
        self.snake = [(10, 10), (9, 10), (8, 10)]  # Initial body
        self.direction = RIGHT
        self.next_direction = RIGHT
        self.food = self.spawn_food()
        self.score = 0

    def spawn_food(self):
        while True:
            x = random.randint(0, (SCREEN_WIDTH // GRID_SIZE) - 1)
            y = random.randint(0, (SCREEN_HEIGHT // GRID_SIZE) - 1)
            if (x, y) not in self.snake:
                return (x, y)

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if self.state == "START":
                    if event.key == pygame.K_RETURN:
                        self.state = "PLAYING"
                    elif event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()

                elif self.state == "PLAYING":
                    if event.key == pygame.K_UP and self.direction != DOWN:
                        self.next_direction = UP
                    elif event.key == pygame.K_DOWN and self.direction != UP:
                        self.next_direction = DOWN
                    elif event.key == pygame.K_LEFT and self.direction != RIGHT:
                        self.next_direction = LEFT
                    elif event.key == pygame.K_RIGHT and self.direction != LEFT:
                        self.next_direction = RIGHT
                    elif event.key == pygame.K_p:
                        self.state = "PAUSED"

                elif self.state == "PAUSED":
                    if event.key == pygame.K_p:
                        self.state = "PLAYING"

                elif self.state == "GAMEOVER":
                    if event.key == pygame.K_RETURN:
                        self.reset_game()
                        self.state = "PLAYING"
                    elif event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()

    def update(self):
        if self.state != "PLAYING":
            return

        self.direction = self.next_direction
        head_x, head_y = self.snake[0]
        dx, dy = self.direction
        new_head = (head_x + dx, head_y + dy)

        # Check collisions (Walls)
        if (new_head[0] < 0 or new_head[0] >= SCREEN_WIDTH // GRID_SIZE or
            new_head[1] < 0 or new_head[1] >= SCREEN_HEIGHT // GRID_SIZE):
            self.game_over()
            return

        # Check collisions (Self)
        if new_head in self.snake:
            self.game_over()
            return

        self.snake.insert(0, new_head)

        # Check Food
        if new_head == self.food:
            self.score += 10
            if self.score > self.high_score:
                self.high_score = self.score
                self.save_high_score()
            self.food = self.spawn_food()
        else:
            self.snake.pop()

    def game_over(self):
        self.state = "GAMEOVER"

    def draw(self):
        self.screen.fill(BLACK)

        if self.state == "START":
            self.draw_text_centered("SNAKE GAME", -50, self.large_font, GREEN)
            self.draw_text_centered("Press ENTER to Start", 10, self.font, WHITE)
            self.draw_text_centered(f"High Score: {self.high_score}", 50, self.font, GRAY)

        elif self.state == "PLAYING" or self.state == "PAUSED":
            # Draw Snake
            for segment in self.snake:
                rect = pygame.Rect(segment[0] * GRID_SIZE, segment[1] * GRID_SIZE, GRID_SIZE, GRID_SIZE)
                pygame.draw.rect(self.screen, GREEN, rect)
                pygame.draw.rect(self.screen, DARK_GRAY, rect, 1) # Border

            # Draw Food
            rect = pygame.Rect(self.food[0] * GRID_SIZE, self.food[1] * GRID_SIZE, GRID_SIZE, GRID_SIZE)
            pygame.draw.rect(self.screen, RED, rect)

            # HUD
            score_text = self.font.render(f"Score: {self.score}", True, WHITE)
            self.screen.blit(score_text, (10, 10))

            if self.state == "PAUSED":
                self.draw_text_centered("PAUSED", 0, self.large_font, BLUE)

        elif self.state == "GAMEOVER":
            self.draw_text_centered("GAME OVER", -50, self.large_font, RED)
            self.draw_text_centered(f"Final Score: {self.score}", 10, self.font, WHITE)
            self.draw_text_centered("Press ENTER to Restart", 50, self.font, GRAY)

        pygame.display.flip()

    def draw_text_centered(self, text, y_offset, font, color):
        surface = font.render(text, True, color)
        rect = surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + y_offset))
        self.screen.blit(surface, rect)

    def run(self):
        while True:
            self.handle_input()
            self.update()
            self.draw()
            self.clock.tick(FPS)

if __name__ == "__main__":
    game = SnakeGame()
    game.run()
