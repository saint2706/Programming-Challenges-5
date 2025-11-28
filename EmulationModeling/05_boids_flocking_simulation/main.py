"""
Emulation/Modeling project implementation.
"""

import pygame
import numpy as np
from boids import Flock

def main():
    """
    Docstring for main.
    """
    WIDTH, HEIGHT = 800, 600
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Boids Flocking Simulation")
    clock = pygame.time.Clock()

    flock = Flock(50, WIDTH, HEIGHT)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        flock.update()

        screen.fill((20, 20, 30))

        for boid in flock.boids:
            # Draw triangle aligned with velocity
            pos = boid.position.astype(int)
            vel = boid.velocity
            angle = np.arctan2(vel[1], vel[0])

            # Triangle points
            r = 6
            p1 = pos + np.array([np.cos(angle)*r, np.sin(angle)*r])
            p2 = pos + np.array([np.cos(angle + 2.5)*r, np.sin(angle + 2.5)*r])
            p3 = pos + np.array([np.cos(angle - 2.5)*r, np.sin(angle - 2.5)*r])

            pygame.draw.polygon(screen, (200, 200, 255), [p1, p2, p3])

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()
