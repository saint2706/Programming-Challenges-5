import pygame
import sys
import random

# Configuration
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 50, 50)
GREEN = (50, 255, 50)
YELLOW = (255, 255, 50)

WORD_LIST = [
    "python", "pygame", "code", "debug", "compile", "execute", "variable",
    "function", "class", "object", "inherit", "syntax", "error", "keyboard",
    "screen", "pixel", "mouse", "loop", "condition", "binary", "integer",
    "string", "boolean", "float", "array", "list", "tuple", "dictionary",
    "algorithm", "structure", "data", "base", "network", "server", "client"
]

class Word:
    def __init__(self, text, x, speed):
        self.text = text
        self.x = x
        self.y = -30
        self.speed = speed
        self.matched_len = 0 # How many chars typed correctly

    def draw(self, screen, font):
        # Draw matched part in Green, rest in White
        matched = self.text[:self.matched_len]
        remainder = self.text[self.matched_len:]

        surf_m = font.render(matched, True, GREEN)
        surf_r = font.render(remainder, True, WHITE)

        screen.blit(surf_m, (self.x, self.y))
        screen.blit(surf_r, (self.x + surf_m.get_width(), self.y))

class TypingGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Typing Game - Challenge #06")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Courier New", 28, bold=True)
        self.large_font = pygame.font.SysFont("Arial", 48)

        self.state = "PLAYING"
        self.score = 0
        self.lives = 3
        self.words = []
        self.spawn_timer = 0
        self.active_word_index = -1 # -1 means no word currently being typed

    def reset_game(self):
        self.score = 0
        self.lives = 3
        self.words = []
        self.spawn_timer = 0
        self.active_word_index = -1
        self.state = "PLAYING"

    def spawn_word(self):
        text = random.choice(WORD_LIST)
        x = random.randint(50, SCREEN_WIDTH - 150)
        speed = 1 + (self.score / 50) # Increase speed with score
        self.words.append(Word(text, x, speed))

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

                if self.state == "GAMEOVER":
                    if event.key == pygame.K_RETURN:
                        self.reset_game()
                    return

                if self.state == "PLAYING":
                    char = event.unicode
                    if not char: continue

                    # If we have an active word, check it
                    if self.active_word_index != -1:
                        word = self.words[self.active_word_index]
                        next_char = word.text[word.matched_len]
                        if char == next_char:
                            word.matched_len += 1
                            if word.matched_len == len(word.text):
                                # Word complete
                                self.score += 10
                                self.words.pop(self.active_word_index)
                                self.active_word_index = -1
                        else:
                             # Wrong key for active word? Maybe reset or penalty?
                             # Let's just ignore or flash red? Ignoring for now.
                             pass
                    else:
                        # Try to find a word starting with this char
                        # Prioritize lowest (closest to bottom)?
                        # Or just first found?
                        # Let's find one that starts with this char
                        found_index = -1
                        lowest_y = -9999

                        for i, word in enumerate(self.words):
                            if word.text.startswith(char):
                                if word.y > lowest_y:
                                    lowest_y = word.y
                                    found_index = i

                        if found_index != -1:
                            self.active_word_index = found_index
                            self.words[found_index].matched_len = 1
                            if self.words[found_index].matched_len == len(self.words[found_index].text):
                                 # One letter word case
                                 self.score += 10
                                 self.words.pop(found_index)
                                 self.active_word_index = -1

    def update(self):
        if self.state != "PLAYING":
            return

        self.spawn_timer += 1
        if self.spawn_timer > 60: # Spawn every second approx
            self.spawn_word()
            self.spawn_timer = 0

        # Update words
        for i in range(len(self.words) - 1, -1, -1):
            word = self.words[i]
            word.y += word.speed

            if word.y > SCREEN_HEIGHT:
                self.lives -= 1
                self.words.pop(i)
                if i == self.active_word_index:
                    self.active_word_index = -1
                elif i < self.active_word_index:
                    self.active_word_index -= 1 # Shift index

                if self.lives <= 0:
                    self.state = "GAMEOVER"

    def draw(self):
        self.screen.fill(BLACK)

        if self.state == "PLAYING":
            for word in self.words:
                word.draw(self.screen, self.font)

            # HUD
            score_text = self.font.render(f"Score: {self.score}", True, YELLOW)
            lives_text = self.font.render(f"Lives: {self.lives}", True, RED)
            self.screen.blit(score_text, (10, 10))
            self.screen.blit(lives_text, (SCREEN_WIDTH - 150, 10))

        elif self.state == "GAMEOVER":
            text = self.large_font.render("GAME OVER", True, RED)
            rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20))
            self.screen.blit(text, rect)

            score_text = self.font.render(f"Final Score: {self.score}", True, WHITE)
            rect2 = score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30))
            self.screen.blit(score_text, rect2)

            msg = self.font.render("Press ENTER to Restart", True, WHITE)
            rect3 = msg.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 70))
            self.screen.blit(msg, rect3)

        pygame.display.flip()

    def run(self):
        while True:
            self.handle_input()
            self.update()
            self.draw()
            self.clock.tick(FPS)

if __name__ == "__main__":
    game = TypingGame()
    game.run()
