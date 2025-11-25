import pygame
import sys
import math
import random

# Configuration
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
PLAYER_SPEED = 4
BULLET_SPEED = 10
ENEMY_SPEED = 2
ENEMY_SPAWN_RATE = 60 # Frames

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (50, 50, 255)
RED = (255, 50, 50)
YELLOW = (255, 255, 50)
GREEN = (50, 255, 50)

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image_original = pygame.Surface((30, 30), pygame.SRCALPHA)
        pygame.draw.polygon(self.image_original, BLUE, [(0, 30), (15, 0), (30, 30)]) # Triangle
        self.image = self.image_original
        self.rect = self.image.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
        self.pos = pygame.Vector2(self.rect.center)
        self.hp = 100

    def update(self):
        keys = pygame.key.get_pressed()
        move = pygame.Vector2(0, 0)
        if keys[pygame.K_w]: move.y = -1
        if keys[pygame.K_s]: move.y = 1
        if keys[pygame.K_a]: move.x = -1
        if keys[pygame.K_d]: move.x = 1

        if move.length() > 0:
            move = move.normalize() * PLAYER_SPEED
            self.pos += move

            # Clamp
            self.pos.x = max(0, min(self.pos.x, SCREEN_WIDTH))
            self.pos.y = max(0, min(self.pos.y, SCREEN_HEIGHT))
            self.rect.center = self.pos

        # Rotate towards mouse
        mouse_pos = pygame.mouse.get_pos()
        dx, dy = mouse_pos[0] - self.rect.centerx, mouse_pos[1] - self.rect.centery
        angle = math.degrees(math.atan2(-dy, dx)) - 90
        self.image = pygame.transform.rotate(self.image_original, angle)
        self.rect = self.image.get_rect(center=self.rect.center)

class Bullet(pygame.sprite.Sprite):
    def __init__(self, start_pos, target_pos):
        super().__init__()
        self.image = pygame.Surface((10, 10))
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect(center=start_pos)

        direction = pygame.Vector2(target_pos) - pygame.Vector2(start_pos)
        if direction.length() > 0:
            self.velocity = direction.normalize() * BULLET_SPEED
        else:
            self.velocity = pygame.Vector2(0, 0)
        self.pos = pygame.Vector2(start_pos)

    def update(self):
        self.pos += self.velocity
        self.rect.center = self.pos

        if (self.rect.right < 0 or self.rect.left > SCREEN_WIDTH or
            self.rect.bottom < 0 or self.rect.top > SCREEN_HEIGHT):
            self.kill()

class Enemy(pygame.sprite.Sprite):
    def __init__(self, player_ref):
        super().__init__()
        self.image = pygame.Surface((30, 30))
        self.image.fill(RED)
        self.rect = self.image.get_rect()

        # Spawn at edge
        side = random.choice(['top', 'bottom', 'left', 'right'])
        if side == 'top':
            self.rect.center = (random.randint(0, SCREEN_WIDTH), -30)
        elif side == 'bottom':
            self.rect.center = (random.randint(0, SCREEN_WIDTH), SCREEN_HEIGHT + 30)
        elif side == 'left':
            self.rect.center = (-30, random.randint(0, SCREEN_HEIGHT))
        elif side == 'right':
            self.rect.center = (SCREEN_WIDTH + 30, random.randint(0, SCREEN_HEIGHT))

        self.pos = pygame.Vector2(self.rect.center)
        self.player_ref = player_ref

    def update(self):
        direction = pygame.Vector2(self.player_ref.rect.center) - self.pos
        if direction.length() > 0:
            self.velocity = direction.normalize() * ENEMY_SPEED
            self.pos += self.velocity
            self.rect.center = self.pos

class ShooterGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Top-Down Shooter - Challenge #10")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 24)

        self.all_sprites = pygame.sprite.Group()
        self.bullets = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()

        self.player = Player()
        self.all_sprites.add(self.player)

        self.score = 0
        self.game_over = False
        self.spawn_timer = 0

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN and not self.game_over:
                if event.button == 1: # Left click
                    bullet = Bullet(self.player.rect.center, event.pos)
                    self.all_sprites.add(bullet)
                    self.bullets.add(bullet)

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if event.key == pygame.K_r and self.game_over:
                    self.__init__() # Restart

    def update(self):
        if self.game_over: return

        self.all_sprites.update()

        # Spawn Enemies
        self.spawn_timer += 1
        if self.spawn_timer > ENEMY_SPAWN_RATE:
            enemy = Enemy(self.player)
            self.all_sprites.add(enemy)
            self.enemies.add(enemy)
            self.spawn_timer = 0

        # Bullet - Enemy Collision
        hits = pygame.sprite.groupcollide(self.enemies, self.bullets, True, True)
        for hit in hits:
            self.score += 10

        # Player - Enemy Collision
        hits = pygame.sprite.spritecollide(self.player, self.enemies, False)
        if hits:
            self.player.hp -= 1
            if self.player.hp <= 0:
                self.game_over = True
            # Optional: push back enemies or i-frames

    def draw(self):
        self.screen.fill(BLACK)

        self.all_sprites.draw(self.screen)

        # HUD
        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_text, (10, 10))

        hp_text = self.font.render(f"HP: {self.player.hp}", True, GREEN if self.player.hp > 30 else RED)
        self.screen.blit(hp_text, (10, 40))

        if self.game_over:
            go_text = self.font.render("GAME OVER! Press R", True, RED)
            rect = go_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
            self.screen.blit(go_text, rect)

        pygame.display.flip()

    def run(self):
        while True:
            self.handle_input()
            self.update()
            self.draw()
            self.clock.tick(FPS)

if __name__ == "__main__":
    game = ShooterGame()
    game.run()
