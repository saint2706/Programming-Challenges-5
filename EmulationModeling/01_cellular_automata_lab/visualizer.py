"""Pygame-based visualizer for the Cellular Automata Engine.

Provides interactive visualization with controls for stepping, running,
resetting, and drawing cells manually.
"""

import numpy as np
import pygame


class Visualizer:
    def __init__(self, engine, cell_size=10):
        self.engine = engine
        self.cell_size = cell_size
        self.width = engine.width * cell_size
        self.height = engine.height * cell_size

        pygame.init()
        pygame.display.set_caption("Cellular Automata Lab")
        self.screen = pygame.display.set_mode((self.width, self.height))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 16)

        self.running = True
        self.paused = True
        self.fps = 10
        self.mouse_pressed = False
        self.draw_mode = 1  # 1 for drawing alive, 0 for erasing

        # Colors
        self.COLOR_BG = (10, 10, 10)
        self.COLOR_GRID = (30, 30, 30)
        self.COLOR_ALIVE = (0, 255, 128)
        self.COLOR_TEXT = (255, 255, 255)

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                elif event.key == pygame.K_c:
                    self.engine.clear()
                elif event.key == pygame.K_r:
                    self.engine.randomize()
                elif event.key == pygame.K_1:
                    # Conway's Life
                    self.engine.set_rules((3,), (2, 3))
                    print("Switched to Conway's Life (B3/S23)")
                elif event.key == pygame.K_2:
                    # HighLife
                    self.engine.set_rules((3, 6), (2, 3))
                    print("Switched to HighLife (B36/S23)")
                elif event.key == pygame.K_UP:
                    self.fps = min(60, self.fps + 5)
                elif event.key == pygame.K_DOWN:
                    self.fps = max(1, self.fps - 5)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    self.mouse_pressed = True
                    x, y = event.pos
                    grid_x, grid_y = x // self.cell_size, y // self.cell_size
                    # Determine draw mode based on first clicked cell
                    current = self.engine.grid[grid_y, grid_x]
                    self.draw_mode = 1 - current
                    self.engine.set_cell(grid_x, grid_y, self.draw_mode)

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.mouse_pressed = False

            elif event.type == pygame.MOUSEMOTION:
                if self.mouse_pressed:
                    x, y = event.pos
                    grid_x, grid_y = x // self.cell_size, y // self.cell_size
                    self.engine.set_cell(grid_x, grid_y, self.draw_mode)

    def draw(self):
        self.screen.fill(self.COLOR_BG)

        # Draw alive cells
        # Get coordinates of alive cells
        ys, xs = np.where(self.engine.grid == 1)
        for x, y in zip(xs, ys):
            rect = (
                x * self.cell_size,
                y * self.cell_size,
                self.cell_size - 1,
                self.cell_size - 1,
            )
            pygame.draw.rect(self.screen, self.COLOR_ALIVE, rect)

        # Draw UI overlay
        status = "PAUSED" if self.paused else "RUNNING"
        rules = f"B{list(self.engine.rule_b)}/S{list(self.engine.rule_s)}"
        info_text = f"Gen: {self.engine.generation} | FPS: {self.fps} | {status} | Rule: {rules}"
        help_text = (
            "Space: Pause | R: Random | C: Clear | 1: Life | 2: HighLife | Click: Draw"
        )

        surf_info = self.font.render(info_text, True, self.COLOR_TEXT)
        surf_help = self.font.render(help_text, True, (150, 150, 150))

        self.screen.blit(surf_info, (10, 10))
        self.screen.blit(surf_help, (10, 30))

        pygame.display.flip()

    def run(self):
        while self.running:
            self.handle_input()

            if not self.paused:
                self.engine.step()

            self.draw()
            self.clock.tick(self.fps)

        pygame.quit()
