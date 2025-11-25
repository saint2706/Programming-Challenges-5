import pygame
import sys

# Configuration
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
GRAVITY = 0.5
JUMP_STRENGTH = -12
MOVE_SPEED = 5

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (50, 50, 255)
GREEN = (50, 255, 50)
RED = (255, 50, 50)
GRAY = (100, 100, 100)

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((30, 30))
        self.image.fill(BLUE)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

        self.vel_x = 0
        self.vel_y = 0
        self.on_ground = False

    def update(self, platforms):
        # Gravity
        self.vel_y += GRAVITY

        # Horizontal Movement
        self.rect.x += self.vel_x

        # Horizontal Collisions
        hits = pygame.sprite.spritecollide(self, platforms, False)
        for platform in hits:
            if self.vel_x > 0:
                self.rect.right = platform.rect.left
            elif self.vel_x < 0:
                self.rect.left = platform.rect.right

        # Vertical Movement
        self.rect.y += self.vel_y
        self.on_ground = False # Assume air until collision check

        # Vertical Collisions
        hits = pygame.sprite.spritecollide(self, platforms, False)
        for platform in hits:
            if self.vel_y > 0:
                self.rect.bottom = platform.rect.top
                self.vel_y = 0
                self.on_ground = True
            elif self.vel_y < 0:
                self.rect.top = platform.rect.bottom
                self.vel_y = 0

    def jump(self):
        if self.on_ground:
            self.vel_y = JUMP_STRENGTH

class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h, color=GRAY):
        super().__init__()
        self.image = pygame.Surface((w, h))
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

class PlatformerGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Platformer - Challenge #09")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 48)

        self.all_sprites = pygame.sprite.Group()
        self.platforms = pygame.sprite.Group()
        self.hazards = pygame.sprite.Group()
        self.goals = pygame.sprite.Group()

        self.setup_level()

    def setup_level(self):
        self.all_sprites.empty()
        self.platforms.empty()
        self.hazards.empty()
        self.goals.empty()

        self.player = Player(50, 500)
        self.all_sprites.add(self.player)

        # Level Design
        # Floor
        p1 = Platform(0, SCREEN_HEIGHT - 20, SCREEN_WIDTH, 20)
        self.platforms.add(p1)
        self.all_sprites.add(p1)

        # Platforms
        coords = [(200, 500, 100, 20), (350, 400, 100, 20), (500, 300, 100, 20), (200, 250, 100, 20)]
        for (x, y, w, h) in coords:
            p = Platform(x, y, w, h)
            self.platforms.add(p)
            self.all_sprites.add(p)

        # Hazard
        h1 = Platform(300, SCREEN_HEIGHT - 40, 100, 20, RED)
        self.hazards.add(h1)
        self.all_sprites.add(h1)

        # Goal
        g1 = Platform(700, 200, 40, 40, GREEN)
        self.goals.add(g1)
        self.all_sprites.add(g1)

        self.game_over = False
        self.win = False

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if event.key == pygame.K_SPACE:
                    self.player.jump()
                if event.key == pygame.K_r:
                    self.setup_level()

        keys = pygame.key.get_pressed()
        self.player.vel_x = 0
        if keys[pygame.K_LEFT]:
            self.player.vel_x = -MOVE_SPEED
        if keys[pygame.K_RIGHT]:
            self.player.vel_x = MOVE_SPEED

    def update(self):
        if self.game_over or self.win:
            return

        self.player.update(self.platforms)

        # Check Hazards
        if pygame.sprite.spritecollide(self.player, self.hazards, False):
            self.game_over = True

        # Check Win
        if pygame.sprite.spritecollide(self.player, self.goals, False):
            self.win = True

        # Check Falls
        if self.player.rect.top > SCREEN_HEIGHT:
            self.game_over = True

    def draw(self):
        self.screen.fill(BLACK)

        self.all_sprites.draw(self.screen)

        if self.game_over:
            msg = self.font.render("GAME OVER! Press R", True, RED)
            self.screen.blit(msg, (SCREEN_WIDTH//2 - 200, SCREEN_HEIGHT//2))
        elif self.win:
            msg = self.font.render("YOU WIN! Press R", True, GREEN)
            self.screen.blit(msg, (SCREEN_WIDTH//2 - 200, SCREEN_HEIGHT//2))

        pygame.display.flip()

    def run(self):
        while True:
            self.handle_input()
            self.update()
            self.draw()
            self.clock.tick(FPS)

if __name__ == "__main__":
    game = PlatformerGame()
    game.run()
