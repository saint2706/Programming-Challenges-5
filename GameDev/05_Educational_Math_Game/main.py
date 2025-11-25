import pygame
import sys
import random

# Configuration
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 30

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (50, 200, 50)
RED = (200, 50, 50)
BLUE = (50, 50, 200)
GRAY = (100, 100, 100)

class MathGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Math Game - Challenge #05")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 48)
        self.small_font = pygame.font.SysFont("Arial", 24)

        self.score = 0
        self.difficulty = 1
        self.question = ""
        self.answer = 0
        self.user_input = ""
        self.feedback = ""
        self.feedback_color = WHITE
        self.feedback_timer = 0

        self.generate_question()

    def generate_question(self):
        # Scale difficulty
        max_val = 10 * self.difficulty

        ops = ['+', '-', '*']
        op = random.choice(ops)

        a = random.randint(1, max_val)
        b = random.randint(1, max_val)

        # Simplify subtraction to avoid negatives for kids
        if op == '-':
            if a < b: a, b = b, a

        self.question = f"{a} {op} {b} = ?"

        if op == '+': self.answer = a + b
        elif op == '-': self.answer = a - b
        elif op == '*': self.answer = a * b

    def check_answer(self):
        try:
            val = int(self.user_input)
            if val == self.answer:
                self.score += 1
                self.feedback = "CORRECT!"
                self.feedback_color = GREEN
                if self.score % 5 == 0:
                    self.difficulty += 1
                self.generate_question()
            else:
                self.feedback = f"WRONG! Answer was {self.answer}"
                self.feedback_color = RED
                # Reset difficulty or just continue?
                self.generate_question()
        except ValueError:
            self.feedback = "Invalid Input"
            self.feedback_color = RED

        self.user_input = ""
        self.feedback_timer = 60 # Show feedback for 2 seconds (30fps)

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                elif event.key == pygame.K_RETURN:
                    if self.user_input:
                        self.check_answer()
                elif event.key == pygame.K_BACKSPACE:
                    self.user_input = self.user_input[:-1]
                else:
                    # Filter for numbers and negative sign
                    if event.unicode.isnumeric() or (event.unicode == '-' and len(self.user_input) == 0):
                        self.user_input += event.unicode

    def draw(self):
        self.screen.fill(BLACK)

        # Draw Score
        score_surf = self.small_font.render(f"Score: {self.score}  Level: {self.difficulty}", True, WHITE)
        self.screen.blit(score_surf, (10, 10))

        # Draw Question
        q_surf = self.font.render(self.question, True, BLUE)
        q_rect = q_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3))
        self.screen.blit(q_surf, q_rect)

        # Draw Input
        input_text = self.user_input + "_"
        inp_surf = self.font.render(input_text, True, WHITE)
        inp_rect = inp_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        pygame.draw.rect(self.screen, GRAY, inp_rect.inflate(20, 10), 2)
        self.screen.blit(inp_surf, inp_rect)

        # Draw Feedback
        if self.feedback_timer > 0:
            fb_surf = self.font.render(self.feedback, True, self.feedback_color)
            fb_rect = fb_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT * 2 // 3))
            self.screen.blit(fb_surf, fb_rect)
            self.feedback_timer -= 1

        pygame.display.flip()

    def run(self):
        while True:
            self.handle_input()
            self.draw()
            self.clock.tick(FPS)

if __name__ == "__main__":
    game = MathGame()
    game.run()
