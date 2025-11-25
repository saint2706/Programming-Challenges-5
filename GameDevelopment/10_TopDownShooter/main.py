import pygame
import math
import random
import sys

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
PLAYER_SPEED = 5
BULLET_SPEED = 10
ENEMY_SPEED = 3

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
GRAY = (50, 50, 50)

# Setup Screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Top-Down Shooter - Challenge 10")
clock = pygame.time.Clock()

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.original_image = pygame.Surface((40, 40), pygame.SRCALPHA)
        pygame.draw.circle(self.original_image, BLUE, (20, 20), 20)
        pygame.draw.rect(self.original_image, WHITE, (30, 15, 10, 10)) # Gun barrel
        self.image = self.original_image
        self.rect = self.image.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2))
        self.pos = pygame.math.Vector2(SCREEN_WIDTH/2, SCREEN_HEIGHT/2)
        self.health = 100

    def update(self):
        # Movement
        keys = pygame.key.get_pressed()
        move = pygame.math.Vector2(0, 0)
        if keys[pygame.K_w]: move.y = -1
        if keys[pygame.K_s]: move.y = 1
        if keys[pygame.K_a]: move.x = -1
        if keys[pygame.K_d]: move.x = 1
        
        if move.length() > 0:
            move = move.normalize() * PLAYER_SPEED
            self.pos += move
            
        # Clamp to screen
        self.pos.x = max(20, min(SCREEN_WIDTH - 20, self.pos.x))
        self.pos.y = max(20, min(SCREEN_HEIGHT - 20, self.pos.y))
        
        self.rect.center = self.pos

        # Rotation
        mouse_pos = pygame.mouse.get_pos()
        dx = mouse_pos[0] - self.rect.centerx
        dy = mouse_pos[1] - self.rect.centery
        angle = math.degrees(math.atan2(-dy, dx)) - 90
        self.image = pygame.transform.rotate(self.original_image, angle)
        self.rect = self.image.get_rect(center=self.rect.center)

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, angle):
        super().__init__()
        self.image = pygame.Surface((10, 10))
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect(center=(x, y))
        rad = math.radians(angle + 90)
        self.vel = pygame.math.Vector2(math.cos(rad) * BULLET_SPEED, -math.sin(rad) * BULLET_SPEED)
        self.pos = pygame.math.Vector2(x, y)

    def update(self):
        self.pos += self.vel
        self.rect.center = self.pos
        if not screen.get_rect().colliderect(self.rect):
            self.kill()

class Enemy(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((30, 30))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        
        # Spawn at edge
        side = random.choice(['top', 'bottom', 'left', 'right'])
        if side == 'top':
            self.rect.x = random.randint(0, SCREEN_WIDTH)
            self.rect.y = -40
        elif side == 'bottom':
            self.rect.x = random.randint(0, SCREEN_WIDTH)
            self.rect.y = SCREEN_HEIGHT + 40
        elif side == 'left':
            self.rect.x = -40
            self.rect.y = random.randint(0, SCREEN_HEIGHT)
        elif side == 'right':
            self.rect.x = SCREEN_WIDTH + 40
            self.rect.y = random.randint(0, SCREEN_HEIGHT)
            
        self.pos = pygame.math.Vector2(self.rect.center)

    def update(self, player_pos):
        # Move towards player
        direction = player_pos - self.pos
        if direction.length() > 0:
            direction = direction.normalize() * ENEMY_SPEED
            self.pos += direction
            self.rect.center = self.pos

def main():
    player = Player()
    all_sprites = pygame.sprite.Group()
    all_sprites.add(player)
    bullets = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    
    spawn_timer = 0
    score = 0
    font = pygame.font.Font(None, 36)
    
    running = True
    game_over = False
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if not game_over:
                    # Shoot
                    mouse_pos = pygame.mouse.get_pos()
                    dx = mouse_pos[0] - player.rect.centerx
                    dy = mouse_pos[1] - player.rect.centery
                    angle = math.degrees(math.atan2(-dy, dx)) - 90
                    bullet = Bullet(player.rect.centerx, player.rect.centery, angle)
                    all_sprites.add(bullet)
                    bullets.add(bullet)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and game_over:
                    # Restart
                    player = Player()
                    all_sprites = pygame.sprite.Group(player)
                    bullets = pygame.sprite.Group()
                    enemies = pygame.sprite.Group()
                    score = 0
                    game_over = False
                elif event.key == pygame.K_ESCAPE:
                    running = False

        if not game_over:
            # Spawn Enemies
            spawn_timer += 1
            if spawn_timer >= 60:
                spawn_timer = 0
                enemy = Enemy()
                all_sprites.add(enemy)
                enemies.add(enemy)

            # Update
            player.update()
            bullets.update()
            for enemy in enemies:
                enemy.update(player.pos)

            # Collisions
            # Bullet - Enemy
            hits = pygame.sprite.groupcollide(enemies, bullets, True, True)
            for hit in hits:
                score += 10

            # Enemy - Player
            hits = pygame.sprite.spritecollide(player, enemies, False)
            if hits:
                player.health -= 1
                if player.health <= 0:
                    game_over = True

        # Draw
        screen.fill(GRAY)
        all_sprites.draw(screen)
        
        # UI
        score_text = font.render(f"Score: {score}", True, WHITE)
        hp_text = font.render(f"HP: {player.health}", True, GREEN if player.health > 30 else RED)
        screen.blit(score_text, (10, 10))
        screen.blit(hp_text, (SCREEN_WIDTH - 120, 10))

        if game_over:
            msg = font.render("Game Over! Press R to Restart", True, WHITE)
            rect = msg.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2))
            screen.blit(msg, rect)

        pygame.display.update()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
