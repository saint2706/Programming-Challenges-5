"""Breakout/Arkanoid clone using Pygame.

A classic brick-breaking game where the player controls a paddle to bounce
a ball and destroy bricks. Features multiple brick rows, score tracking,
and lives system.

Controls:
    Left/Right arrows or A/D: Move paddle
    Space: Launch ball
    ESC: Quit game
"""
import pygame
import sys
import os
import random

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)

# Setup Screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Breakout - Challenge 2")
clock = pygame.time.Clock()

# Load Assets
def load_asset(name, size=None):
    """
    Docstring for load_asset.
    """
    path = os.path.join("assets", name)
    if os.path.exists(path):
        img = pygame.image.load(path).convert_alpha()
        if size:
            img = pygame.transform.scale(img, size)
        return img
    return None

PADDLE_WIDTH = 100
PADDLE_HEIGHT = 20
BALL_SIZE = 20
BRICK_WIDTH = 75
BRICK_HEIGHT = 30

PADDLE_IMG = load_asset("paddle.png", (PADDLE_WIDTH, PADDLE_HEIGHT))
BALL_IMG = load_asset("ball.png", (BALL_SIZE, BALL_SIZE))
BRICK_IMG = load_asset("brick.png", (BRICK_WIDTH, BRICK_HEIGHT))

class Paddle:
    """
    Docstring for Paddle.
    """
    def __init__(self):
        """
        Docstring for __init__.
        """
        self.rect = pygame.Rect(SCREEN_WIDTH // 2 - PADDLE_WIDTH // 2, SCREEN_HEIGHT - 50, PADDLE_WIDTH, PADDLE_HEIGHT)
        self.speed = 8

    def move(self, dx):
        """
        Docstring for move.
        """
        self.rect.x += dx
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH

    def draw(self, surface):
        """
        Docstring for draw.
        """
        if PADDLE_IMG:
            surface.blit(PADDLE_IMG, self.rect)
        else:
            pygame.draw.rect(surface, BLUE, self.rect)

class Ball:
    """
    Docstring for Ball.
    """
    def __init__(self):
        """
        Docstring for __init__.
        """
        self.rect = pygame.Rect(SCREEN_WIDTH // 2 - BALL_SIZE // 2, SCREEN_HEIGHT // 2, BALL_SIZE, BALL_SIZE)
        self.dx = 5 * random.choice([-1, 1])
        self.dy = -5
        self.active = False

    def reset(self):
        """
        Docstring for reset.
        """
        self.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.dx = 5 * random.choice([-1, 1])
        self.dy = -5
        self.active = False

    def move(self):
        """
        Docstring for move.
        """
        if not self.active:
            return

        self.rect.x += self.dx
        self.rect.y += self.dy

        # Wall collisions
        if self.rect.left <= 0 or self.rect.right >= SCREEN_WIDTH:
            self.dx *= -1
        if self.rect.top <= 0:
            self.dy *= -1
        
        # Bottom collision (death) handled in main loop

    def draw(self, surface):
        """
        Docstring for draw.
        """
        if BALL_IMG:
            surface.blit(BALL_IMG, self.rect)
        else:
            pygame.draw.ellipse(surface, WHITE, self.rect)

class Brick:
    """
    Docstring for Brick.
    """
    def __init__(self, x, y, color):
        """
        Docstring for __init__.
        """
        self.rect = pygame.Rect(x, y, BRICK_WIDTH, BRICK_HEIGHT)
        self.color = color
        self.active = True

    def draw(self, surface):
        """
        Docstring for draw.
        """
        if not self.active:
            return
        
        if BRICK_IMG:
            # Tinting logic could go here, but for now just use the image or rect
            # To tint properly with an image is complex in simple pygame without creating new surfaces
            # Let's just draw the image and maybe a colored overlay with multiply mode if we wanted
            # For now, just drawing the image. If we want colors, we might fall back to rects if image is just red.
            # But let's try to use the image.
            surface.blit(BRICK_IMG, self.rect)
            # Optional: Draw a colored rect with alpha to tint?
            # s = pygame.Surface((BRICK_WIDTH, BRICK_HEIGHT))
            # s.set_alpha(100)
            # s.fill(self.color)
            # surface.blit(s, self.rect.topleft)
        else:
            pygame.draw.rect(surface, self.color, self.rect)
            pygame.draw.rect(surface, BLACK, self.rect, 1)

def create_bricks():
    """
    Docstring for create_bricks.
    """
    bricks = []
    colors = [RED, RED, YELLOW, YELLOW, GREEN, GREEN, BLUE, BLUE]
    for row in range(8):
        for col in range(SCREEN_WIDTH // (BRICK_WIDTH + 5)):
            x = 35 + col * (BRICK_WIDTH + 5)
            y = 50 + row * (BRICK_HEIGHT + 5)
            bricks.append(Brick(x, y, colors[row]))
    return bricks

def main():
    """
    Docstring for main.
    """
    paddle = Paddle()
    ball = Ball()
    bricks = create_bricks()
    lives = 3
    score = 0
    font = pygame.font.Font(None, 36)
    
    running = True
    game_over = False
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if not ball.active and not game_over:
                        ball.active = True
                    elif game_over:
                        # Restart
                        lives = 3
                        score = 0
                        bricks = create_bricks()
                        ball.reset()
                        game_over = False
                elif event.key == pygame.K_ESCAPE:
                    running = False

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            paddle.move(-paddle.speed)
        if keys[pygame.K_RIGHT]:
            paddle.move(paddle.speed)

        if not game_over:
            ball.move()

            # Ball-Paddle Collision
            if ball.rect.colliderect(paddle.rect):
                ball.dy *= -1
                # Adjust angle based on hit position
                hit_pos = (ball.rect.centerx - paddle.rect.centerx) / (PADDLE_WIDTH / 2)
                ball.dx = hit_pos * 8

            # Ball-Brick Collision
            for brick in bricks:
                if brick.active and ball.rect.colliderect(brick.rect):
                    brick.active = False
                    ball.dy *= -1
                    score += 10
                    break # Only hit one brick at a time

            # Ball out of bounds
            if ball.rect.top > SCREEN_HEIGHT:
                lives -= 1
                ball.reset()
                if lives <= 0:
                    game_over = True
            
            # Check win
            if all(not b.active for b in bricks):
                game_over = True # Win state, but let's just say Game Over for now

        # Draw
        screen.fill(BLACK)
        paddle.draw(screen)
        ball.draw(screen)
        for brick in bricks:
            brick.draw(screen)

        # UI
        score_text = font.render(f"Score: {score}", True, WHITE)
        lives_text = font.render(f"Lives: {lives}", True, WHITE)
        screen.blit(score_text, (10, 10))
        screen.blit(lives_text, (SCREEN_WIDTH - 120, 10))

        if game_over:
            if lives > 0:
                msg = "You Win! Press SPACE"
            else:
                msg = "Game Over! Press SPACE"
            text = font.render(msg, True, WHITE)
            rect = text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2))
            screen.blit(text, rect)
        elif not ball.active:
            text = font.render("Press SPACE to Start", True, WHITE)
            rect = text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + 50))
            screen.blit(text, rect)

        pygame.display.update()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
