import pygame
import sys

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
GRAVITY = 0.8
JUMP_POWER = -16
MOVE_SPEED = 5

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (50, 50, 255)
GREEN = (50, 200, 50)
RED = (255, 50, 50)
GRAY = (100, 100, 100)
SKY_BLUE = (135, 206, 235)

# Setup Screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Platformer - Challenge 9")
clock = pygame.time.Clock()

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((30, 50))
        self.image.fill(BLUE)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.vel_y = 0
        self.vel_x = 0
        self.on_ground = False
        self.jumping = False

    def update(self, platforms):
        # Apply Gravity
        self.vel_y += GRAVITY
        
        # Movement
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.vel_x = -MOVE_SPEED
        elif keys[pygame.K_RIGHT]:
            self.vel_x = MOVE_SPEED
        else:
            self.vel_x = 0

        # Jump
        if keys[pygame.K_SPACE] and self.on_ground:
            self.vel_y = JUMP_POWER
            self.on_ground = False
            self.jumping = True

        # X Collision
        self.rect.x += self.vel_x
        hits = pygame.sprite.spritecollide(self, platforms, False)
        for platform in hits:
            if self.vel_x > 0:
                self.rect.right = platform.rect.left
            elif self.vel_x < 0:
                self.rect.left = platform.rect.right

        # Y Collision
        self.rect.y += self.vel_y
        self.on_ground = False
        hits = pygame.sprite.spritecollide(self, platforms, False)
        for platform in hits:
            if self.vel_y > 0:
                self.rect.bottom = platform.rect.top
                self.vel_y = 0
                self.on_ground = True
                self.jumping = False
            elif self.vel_y < 0:
                self.rect.top = platform.rect.bottom
                self.vel_y = 0

        # Screen Bounds (Death)
        if self.rect.top > SCREEN_HEIGHT + 200:
            self.reset()

    def reset(self):
        self.rect.x = 100
        self.rect.y = SCREEN_HEIGHT - 150
        self.vel_y = 0
        self.vel_x = 0

class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h, color=GREEN):
        super().__init__()
        self.image = pygame.Surface((w, h))
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

class Camera:
    def __init__(self, width, height):
        self.camera = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height

    def apply(self, entity):
        return entity.rect.move(self.camera.topleft)

    def update(self, target):
        x = -target.rect.centerx + int(SCREEN_WIDTH / 2)
        y = -target.rect.centery + int(SCREEN_HEIGHT / 2)

        # Limit scrolling to map size
        x = min(0, x) # Left
        y = min(0, y) # Top
        x = max(-(self.width - SCREEN_WIDTH), x) # Right
        y = max(-(self.height - SCREEN_HEIGHT), y) # Bottom
        
        self.camera = pygame.Rect(x, y, self.width, self.height)

def main():
    # Level Setup
    all_sprites = pygame.sprite.Group()
    platforms = pygame.sprite.Group()

    level_width = 2000
    level_height = SCREEN_HEIGHT

    # Floor
    p = Platform(0, SCREEN_HEIGHT - 40, level_width, 40, GRAY)
    all_sprites.add(p)
    platforms.add(p)

    # Platforms
    coords = [
        (300, SCREEN_HEIGHT - 150, 200, 20),
        (600, SCREEN_HEIGHT - 250, 150, 20),
        (850, SCREEN_HEIGHT - 350, 150, 20),
        (1100, SCREEN_HEIGHT - 450, 150, 20),
        (1400, SCREEN_HEIGHT - 300, 200, 20),
        (1700, SCREEN_HEIGHT - 200, 100, 20)
    ]

    for (x, y, w, h) in coords:
        p = Platform(x, y, w, h)
        all_sprites.add(p)
        platforms.add(p)

    # Goal
    goal = Platform(1900, SCREEN_HEIGHT - 100, 50, 50, RED)
    all_sprites.add(goal)
    platforms.add(goal)

    player = Player(100, SCREEN_HEIGHT - 150)
    all_sprites.add(player)

    camera = Camera(level_width, level_height)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        player.update(platforms)
        camera.update(player)

        # Draw
        screen.fill(SKY_BLUE)
        for sprite in all_sprites:
            screen.blit(sprite.image, camera.apply(sprite))

        # Check Win
        if player.rect.colliderect(goal.rect):
            font = pygame.font.Font(None, 74)
            text = font.render("YOU WIN!", True, WHITE)
            rect = text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2))
            screen.blit(text, rect)
            pygame.display.update()
            pygame.time.delay(2000)
            player.reset()

        pygame.display.update()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
