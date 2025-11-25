import pygame
import sys
import random

# Configuration
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
PADDLE_WIDTH = 100
PADDLE_HEIGHT = 15
BALL_RADIUS = 8
BRICK_ROWS = 6
BRICK_COLS = 10
BRICK_WIDTH = 70
BRICK_HEIGHT = 20
BRICK_PADDING = 8
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (50, 50, 255)
RED = (255, 50, 50)
GREEN = (50, 255, 50)
YELLOW = (255, 255, 50)
ORANGE = (255, 165, 0)
GRAY = (100, 100, 100)

class BreakoutGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Breakout - Challenge #02")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 24)
        self.large_font = pygame.font.SysFont("Arial", 48)

        self.state = "START"
        self.score = 0
        self.lives = 3
        self.reset_game()

    def reset_game(self):
        self.paddle_x = (SCREEN_WIDTH - PADDLE_WIDTH) // 2
        self.paddle_y = SCREEN_HEIGHT - 40
        self.ball_x = SCREEN_WIDTH // 2
        self.ball_y = self.paddle_y - BALL_RADIUS - 1
        self.ball_dx = 0
        self.ball_dy = 0
        self.ball_active = False

        # Create bricks
        self.bricks = []
        start_x = (SCREEN_WIDTH - (BRICK_COLS * (BRICK_WIDTH + BRICK_PADDING))) // 2
        start_y = 60
        colors = [RED, ORANGE, YELLOW, GREEN, BLUE, WHITE]

        for row in range(BRICK_ROWS):
            for col in range(BRICK_COLS):
                bx = start_x + col * (BRICK_WIDTH + BRICK_PADDING)
                by = start_y + row * (BRICK_HEIGHT + BRICK_PADDING)
                color = colors[row % len(colors)]
                self.bricks.append(pygame.Rect(bx, by, BRICK_WIDTH, BRICK_HEIGHT))

    def reset_ball(self):
        self.ball_x = self.paddle_x + PADDLE_WIDTH // 2
        self.ball_y = self.paddle_y - BALL_RADIUS - 1
        self.ball_dx = 0
        self.ball_dy = 0
        self.ball_active = False

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if self.state == "START" or self.state == "GAMEOVER" or self.state == "WIN":
                    if event.key == pygame.K_RETURN:
                        self.score = 0
                        self.lives = 3
                        self.reset_game()
                        self.state = "PLAYING"
                    elif event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()

                elif self.state == "PLAYING":
                    if event.key == pygame.K_SPACE and not self.ball_active:
                        self.ball_active = True
                        self.ball_dx = random.choice([-4, 4])
                        self.ball_dy = -5
                    elif event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()

        # Continuous key check for paddle
        if self.state == "PLAYING":
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT]:
                self.paddle_x -= 7
            if keys[pygame.K_RIGHT]:
                self.paddle_x += 7

            # Mouse control
            mouse_x, _ = pygame.mouse.get_pos()
            # If mouse moved significantly, use it? Or just simple override if mouse is in window
            if pygame.mouse.get_focused():
                 # Centering paddle on mouse
                 self.paddle_x = mouse_x - PADDLE_WIDTH // 2

            # Clamp paddle
            if self.paddle_x < 0: self.paddle_x = 0
            if self.paddle_x > SCREEN_WIDTH - PADDLE_WIDTH: self.paddle_x = SCREEN_WIDTH - PADDLE_WIDTH

            if not self.ball_active:
                self.ball_x = self.paddle_x + PADDLE_WIDTH // 2

    def update(self):
        if self.state != "PLAYING":
            return

        if self.ball_active:
            self.ball_x += self.ball_dx
            self.ball_y += self.ball_dy

            # Wall Collisions
            if self.ball_x - BALL_RADIUS < 0:
                self.ball_x = BALL_RADIUS
                self.ball_dx *= -1
            elif self.ball_x + BALL_RADIUS > SCREEN_WIDTH:
                self.ball_x = SCREEN_WIDTH - BALL_RADIUS
                self.ball_dx *= -1

            if self.ball_y - BALL_RADIUS < 0:
                self.ball_y = BALL_RADIUS
                self.ball_dy *= -1

            # Paddle Collision
            paddle_rect = pygame.Rect(self.paddle_x, self.paddle_y, PADDLE_WIDTH, PADDLE_HEIGHT)
            ball_rect = pygame.Rect(self.ball_x - BALL_RADIUS, self.ball_y - BALL_RADIUS, BALL_RADIUS*2, BALL_RADIUS*2)

            if ball_rect.colliderect(paddle_rect):
                self.ball_dy *= -1
                self.ball_y = self.paddle_y - BALL_RADIUS - 1 # Prevent sticking
                # Add "English" / Spin effect based on where it hit
                hit_pos = (self.ball_x - self.paddle_x) / PADDLE_WIDTH
                self.ball_dx = (hit_pos - 0.5) * 10

            # Brick Collision
            hit_index = ball_rect.collidelist(self.bricks)
            if hit_index != -1:
                brick = self.bricks.pop(hit_index)
                self.ball_dy *= -1 # Simple bounce
                self.score += 10
                if not self.bricks:
                    self.state = "WIN"

            # Death
            if self.ball_y > SCREEN_HEIGHT:
                self.lives -= 1
                if self.lives <= 0:
                    self.state = "GAMEOVER"
                else:
                    self.reset_ball()

    def draw(self):
        self.screen.fill(BLACK)

        if self.state == "START":
            self.draw_text_centered("BREAKOUT", -50, self.large_font, BLUE)
            self.draw_text_centered("Press ENTER to Start", 10, self.font, WHITE)

        elif self.state == "PLAYING" or self.state == "GAMEOVER" or self.state == "WIN":
            # Draw Bricks
            colors = [RED, ORANGE, YELLOW, GREEN, BLUE, WHITE]
            # Since we popped bricks, we don't know their original row for color easily unless we store it.
            # Simplified: just draw them Red for now or random color from list if not stored.
            # Better: Make brick object. For now, let's just draw them White or colorful if we iterate.
            # Actually, let's iterate remaining bricks. To keep color, we could have stored (rect, color).
            # But for MVP, let's just draw them all Green.
            for brick in self.bricks:
                pygame.draw.rect(self.screen, GREEN, brick)
                pygame.draw.rect(self.screen, BLACK, brick, 1)

            # Draw Paddle
            pygame.draw.rect(self.screen, BLUE, (self.paddle_x, self.paddle_y, PADDLE_WIDTH, PADDLE_HEIGHT))

            # Draw Ball
            pygame.draw.circle(self.screen, WHITE, (int(self.ball_x), int(self.ball_y)), BALL_RADIUS)

            # HUD
            score_text = self.font.render(f"Score: {self.score}", True, WHITE)
            lives_text = self.font.render(f"Lives: {self.lives}", True, WHITE)
            self.screen.blit(score_text, (10, 10))
            self.screen.blit(lives_text, (SCREEN_WIDTH - 100, 10))

            if self.state == "GAMEOVER":
                self.draw_text_centered("GAME OVER", 0, self.large_font, RED)
                self.draw_text_centered("Press ENTER to Restart", 60, self.font, GRAY)
            elif self.state == "WIN":
                self.draw_text_centered("YOU WIN!", 0, self.large_font, YELLOW)
                self.draw_text_centered("Press ENTER to Restart", 60, self.font, GRAY)

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
    game = BreakoutGame()
    game.run()
