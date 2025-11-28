"""Educational Math Game using Pygame.

An arithmetic practice game that generates random math problems with
increasing difficulty. Tracks score and adjusts problem complexity
based on player performance.

Controls:
    Number keys: Type answer
    Enter: Submit answer
    Backspace: Delete last digit
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
FPS = 30

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (100, 100, 255)
GREEN = (50, 200, 50)
RED = (255, 100, 100)

# Setup Screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Math Game - Challenge 5")
clock = pygame.time.Clock()
font_large = pygame.font.Font(None, 100)
font_medium = pygame.font.Font(None, 60)
font_small = pygame.font.Font(None, 36)

class MathGame:
    """
    Docstring for MathGame.
    """
    def __init__(self):
        """
        Docstring for __init__.
        """
        self.score = 0
        self.difficulty = 1
        self.question = ""
        self.answer = 0
        self.user_input = ""
        self.feedback = ""
        self.feedback_color = WHITE
        self.generate_question()

    def generate_question(self):
        """
        Docstring for generate_question.
        """
        ops = ['+', '-']
        if self.difficulty > 2:
            ops.append('*')
        
        op = random.choice(ops)
        limit = 10 * self.difficulty
        
        a = random.randint(1, limit)
        b = random.randint(1, limit)
        
        if op == '-':
            if a < b: a, b = b, a # Ensure positive result
        
        self.question = f"{a} {op} {b} = ?"
        if op == '+':
            self.answer = a + b
        elif op == '-':
            self.answer = a - b
        elif op == '*':
            self.answer = a * b
        
        self.user_input = ""

    def check_answer(self):
        """
        Docstring for check_answer.
        """
        try:
            val = int(self.user_input)
            if val == self.answer:
                self.score += 10
                self.difficulty = 1 + (self.score // 50)
                self.feedback = "Correct!"
                self.feedback_color = GREEN
                self.generate_question()
            else:
                self.feedback = f"Wrong! {self.answer}"
                self.feedback_color = RED
                self.score = max(0, self.score - 5)
                self.generate_question()
        except ValueError:
            pass

    def draw(self, surface):
        """
        Docstring for draw.
        """
        surface.fill(BLACK)
        
        # Question
        q_text = font_large.render(self.question, True, WHITE)
        q_rect = q_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/3))
        surface.blit(q_text, q_rect)
        
        # Input
        input_text = font_large.render(self.user_input + "_", True, BLUE)
        input_rect = input_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2))
        surface.blit(input_text, input_rect)
        
        # Feedback
        if self.feedback:
            fb_text = font_medium.render(self.feedback, True, self.feedback_color)
            fb_rect = fb_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + 100))
            surface.blit(fb_text, fb_rect)
            
        # UI
        score_text = font_small.render(f"Score: {self.score}  Level: {self.difficulty}", True, WHITE)
        surface.blit(score_text, (20, 20))
        
        help_text = font_small.render("Type answer and press ENTER", True, (150, 150, 150))
        surface.blit(help_text, (20, SCREEN_HEIGHT - 40))

def main():
    """
    Docstring for main.
    """
    game = MathGame()
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    game.check_answer()
                elif event.key == pygame.K_BACKSPACE:
                    game.user_input = game.user_input[:-1]
                elif event.key == pygame.K_ESCAPE:
                    running = False
                elif event.unicode.isdigit() or (event.unicode == '-' and len(game.user_input) == 0):
                    game.user_input += event.unicode

        game.draw(screen)
        pygame.display.update()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
