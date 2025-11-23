import pygame

class Display:
    def __init__(self, scale=10):
        self.scale = scale
        self.width = 64 * scale
        self.height = 32 * scale

        pygame.init()
        pygame.display.set_caption("CHIP-8 Emulator")
        self.screen = pygame.display.set_mode((self.width, self.height))

        self.COLOR_BG = (0, 0, 0)
        self.COLOR_FG = (255, 255, 255)

    def draw(self, display_buffer):
        self.screen.fill(self.COLOR_BG)

        for i, pixel in enumerate(display_buffer):
            if pixel:
                x = (i % 64) * self.scale
                y = (i // 64) * self.scale
                pygame.draw.rect(self.screen, self.COLOR_FG, (x, y, self.scale, self.scale))

        pygame.display.flip()

    def quit(self):
        pygame.quit()
