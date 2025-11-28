"""Typing Game using Pygame.

A word-typing game where words fall from the top of the screen and the
player must type them before they reach the bottom. Features progressive
difficulty and score tracking.

Controls:
    Type letters: Match falling words
    ESC: Quit game
"""
import pygame
import sys
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
RED = (255, 50, 50)
GREEN = (50, 255, 50)
YELLOW = (255, 255, 50)

# Setup Screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Typing Game - Challenge 6")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 48)
font_small = pygame.font.Font(None, 32)

WORD_LIST = [
    "python", "code", "game", "challenge", "program", "variable", "function",
    "loop", "class", "object", "string", "integer", "boolean", "list",
    "tuple", "dictionary", "import", "module", "package", "library",
    "framework", "algorithm", "structure", "database", "network", "server",
    "client", "interface", "design", "pattern", "debug", "error", "exception",
    "syntax", "compiler", "interpreter", "memory", "processor", "storage",
    "keyboard", "mouse", "monitor", "screen", "pixel", "graphic", "audio",
    "video", "input", "output", "system", "control", "logic", "math"
]

class FallingWord:
    """
    Docstring for FallingWord.
    """
    def __init__(self, text, speed):
        """
        Docstring for __init__.
        """
        self.text = text
        self.speed = speed
        self.x = random.randint(50, SCREEN_WIDTH - 150)
        self.y = -50
        self.color = WHITE
        self.matched_len = 0 # How many chars matched so far

    def update(self):
        """
        Docstring for update.
        """
        self.y += self.speed
        return self.y > SCREEN_HEIGHT

    def draw(self, surface):
        # Draw matched part in Green, rest in White
        """
        Docstring for draw.
        """
        matched = self.text[:self.matched_len]
        rest = self.text[self.matched_len:]
        
        m_surf = font.render(matched, True, GREEN)
        r_surf = font.render(rest, True, self.color)
        
        surface.blit(m_surf, (self.x, self.y))
        surface.blit(r_surf, (self.x + m_surf.get_width(), self.y))

class TypingGame:
    """
    Docstring for TypingGame.
    """
    def __init__(self):
        """
        Docstring for __init__.
        """
        self.words = []
        self.score = 0
        self.lives = 5
        self.spawn_timer = 0
        self.spawn_rate = 120 # Frames
        self.difficulty = 1
        self.active_word_index = -1 # Index of word being typed, -1 if none

    def spawn_word(self):
        """
        Docstring for spawn_word.
        """
        text = random.choice(WORD_LIST)
        speed = random.uniform(1, 2) + (self.difficulty * 0.1)
        self.words.append(FallingWord(text, speed))

    def handle_input(self, char):
        # If we have an active word, check against it
        """
        Docstring for handle_input.
        """
        if self.active_word_index != -1:
            word = self.words[self.active_word_index]
            target_char = word.text[word.matched_len]
            if char == target_char:
                word.matched_len += 1
                if word.matched_len == len(word.text):
                    # Word completed
                    self.score += 10
                    self.words.pop(self.active_word_index)
                    self.active_word_index = -1
                    self.difficulty = 1 + (self.score // 50)
            # Else ignore or penalty? Let's ignore for now
        else:
            # Find a word starting with this char
            # Prioritize lowest (closest to bottom)
            # Sort by Y descending
            sorted_indices = sorted(range(len(self.words)), key=lambda i: self.words[i].y, reverse=True)
            
            for i in sorted_indices:
                word = self.words[i]
                if word.text.startswith(char):
                    self.active_word_index = i
                    word.matched_len = 1
                    if word.matched_len == len(word.text): # Single letter word?
                         self.score += 10
                         self.words.pop(i)
                         self.active_word_index = -1
                    break

    def update(self):
        """
        Docstring for update.
        """
        self.spawn_timer += 1
        if self.spawn_timer >= max(30, self.spawn_rate - (self.difficulty * 5)):
            self.spawn_word()
            self.spawn_timer = 0

        # Update words
        missed = []
        for i, word in enumerate(self.words):
            if word.update():
                missed.append(i)
        
        # Remove missed words (reverse order to keep indices valid)
        for i in sorted(missed, reverse=True):
            self.lives -= 1
            if self.active_word_index == i:
                self.active_word_index = -1
            elif self.active_word_index > i:
                self.active_word_index -= 1
            self.words.pop(i)

        return self.lives > 0

    def draw(self, surface):
        """
        Docstring for draw.
        """
        surface.fill(BLACK)
        for word in self.words:
            word.draw(surface)
            
        # UI
        score_text = font_small.render(f"Score: {self.score}", True, WHITE)
        lives_text = font_small.render(f"Lives: {self.lives}", True, RED)
        surface.blit(score_text, (10, 10))
        surface.blit(lives_text, (SCREEN_WIDTH - 120, 10))
        
        # Target indicator
        if self.active_word_index != -1:
            target_text = font_small.render(f"Target: {self.words[self.active_word_index].text}", True, YELLOW)
            surface.blit(target_text, (SCREEN_WIDTH // 2 - 50, 10))

def main():
    """
    Docstring for main.
    """
    game = TypingGame()
    
    running = True
    game_over = False
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif game_over:
                    if event.key == pygame.K_SPACE:
                        game = TypingGame()
                        game_over = False
                elif event.unicode.isalpha():
                    game.handle_input(event.unicode.lower())

        if not game_over:
            if not game.update():
                game_over = True

        game.draw(screen)
        
        if game_over:
            msg = font.render("Game Over! Press SPACE", True, WHITE)
            rect = msg.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2))
            screen.blit(msg, rect)

        pygame.display.update()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
