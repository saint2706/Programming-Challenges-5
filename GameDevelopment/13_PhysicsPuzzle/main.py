"""Physics Puzzle Game - a slingshot puzzle rendered with Pygame.

Launch the blue ball slingshot-style (click and drag, then release) to knock the
orange target ball into the green goal. Some levels have walls to arc over or
pits to avoid. Levels are defined as JSON files in the ``levels/`` directory and
loaded through :mod:`levels`; the physics itself lives in :mod:`physics`. Both of
those modules are pure Python and unit-tested independently of this renderer.

Controls:
    Click + drag on the blue ball, release to launch (pull back to aim).
    R      : reset / retry the current level
    N / P  : next / previous level
    ESC    : quit
"""

from __future__ import annotations

import sys

import pygame
from levels import GameStatus, Level, PuzzleGame, discover_levels
from physics import Body, Rect, Vec2

FPS = 60

# Colors
BACKGROUND = (24, 26, 38)
FLOOR_COLOR = (70, 74, 96)
LAUNCH_COLOR = (80, 150, 240)
TARGET_COLOR = (240, 150, 60)
OBSTACLE_COLOR = (150, 150, 160)
GOAL_COLOR = (70, 200, 120)
GOAL_FILL = (70, 200, 120, 60)
HAZARD_COLOR = (220, 70, 80)
HAZARD_FILL = (220, 70, 80, 70)
TEXT_COLOR = (230, 230, 240)
DIM_TEXT = (150, 155, 170)
AIM_COLOR = (240, 240, 120)


class PhysicsPuzzleApp:
    """Pygame front-end that drives :class:`PuzzleGame` for a set of levels."""

    def __init__(self, level_paths: list):
        pygame.init()
        self.level_paths = level_paths
        self.level_index = 0
        self._load_level(0)
        self.screen = pygame.display.set_mode(
            (self.game.level.width, self.game.level.height)
        )
        pygame.display.set_caption("Physics Puzzle - Challenge 13")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 28)
        self.big_font = pygame.font.Font(None, 56)

        # Aiming state.
        self.dragging = False
        self.drag_start = Vec2()
        self.drag_current = Vec2()

    def _load_level(self, index: int) -> None:
        self.level_index = index % len(self.level_paths)
        level = Level.load(self.level_paths[self.level_index])
        self.game = PuzzleGame(level)

    # ------------------------------------------------------------------
    # Event handling
    # ------------------------------------------------------------------
    def handle_events(self) -> bool:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                if event.key == pygame.K_r:
                    self.game.reset()
                    self.dragging = False
                elif event.key == pygame.K_n:
                    self._load_level(self.level_index + 1)
                    self._resize()
                elif event.key == pygame.K_p:
                    self._load_level(self.level_index - 1)
                    self._resize()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._start_drag(event.pos)
            elif event.type == pygame.MOUSEMOTION and self.dragging:
                self.drag_current = Vec2(*event.pos)
            elif (
                event.type == pygame.MOUSEBUTTONUP
                and event.button == 1
                and self.dragging
            ):
                self._release_drag(event.pos)
        return True

    def _resize(self) -> None:
        self.screen = pygame.display.set_mode(
            (self.game.level.width, self.game.level.height)
        )
        self.dragging = False

    def _start_drag(self, pos) -> None:
        if self.game.status != GameStatus.AIMING:
            return
        ball = self.game.launch_ball
        mouse = Vec2(*pos)
        if (mouse - ball.position).length() <= ball.radius + 12:
            self.dragging = True
            self.drag_start = ball.position.copy()
            self.drag_current = mouse

    def _release_drag(self, pos) -> None:
        self.dragging = False
        velocity = self.game.aim_velocity(self.drag_start, Vec2(*pos))
        if velocity.length() > 5:
            self.game.launch(velocity)

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------
    def update(self, dt: float) -> None:
        if self.game.status == GameStatus.SIMULATING:
            self.game.update(dt)

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------
    def draw(self) -> None:
        self.screen.fill(BACKGROUND)
        self._draw_region(self.game.level.goal, GOAL_COLOR, GOAL_FILL)
        for hazard in self.game.level.hazards:
            self._draw_region(hazard, HAZARD_COLOR, HAZARD_FILL)
        for wall in self.game.world.walls:
            pygame.draw.rect(
                self.screen, FLOOR_COLOR, self._rect(wall), border_radius=4
            )
        for body in self.game.world.bodies:
            self._draw_body(body)
        if self.dragging:
            self._draw_aim()
        self._draw_hud()
        pygame.display.flip()

    def _rect(self, r: Rect) -> pygame.Rect:
        return pygame.Rect(int(r.x), int(r.y), int(r.w), int(r.h))

    def _draw_region(self, r: Rect, border, fill) -> None:
        surface = pygame.Surface((int(r.w), int(r.h)), pygame.SRCALPHA)
        surface.fill(fill)
        self.screen.blit(surface, (int(r.x), int(r.y)))
        pygame.draw.rect(self.screen, border, self._rect(r), width=3, border_radius=4)

    def _draw_body(self, body: Body) -> None:
        if body.name == "launch":
            color = LAUNCH_COLOR
        elif body.is_target:
            color = TARGET_COLOR
        else:
            color = OBSTACLE_COLOR
        pos = (int(body.position.x), int(body.position.y))
        pygame.draw.circle(self.screen, color, pos, int(body.radius))
        pygame.draw.circle(self.screen, BACKGROUND, pos, int(body.radius), width=2)

    def _draw_aim(self) -> None:
        ball = self.game.launch_ball
        start = (int(ball.position.x), int(ball.position.y))
        end = (int(self.drag_current.x), int(self.drag_current.y))
        pygame.draw.line(self.screen, DIM_TEXT, start, end, 2)
        # Preview the launch trajectory.
        velocity = self.game.aim_velocity(self.drag_start, self.drag_current)
        self._draw_trajectory(ball.position.copy(), velocity)

    def _draw_trajectory(self, position: Vec2, velocity: Vec2) -> None:
        gravity = self.game.level.gravity
        dt = 1 / 30
        for i in range(30):
            velocity = velocity + gravity * dt
            position = position + velocity * dt
            if i % 2 == 0:
                pygame.draw.circle(
                    self.screen, AIM_COLOR, (int(position.x), int(position.y)), 3
                )

    def _draw_hud(self) -> None:
        level = self.game.level
        title = self.font.render(
            f"Level {self.level_index + 1}/{len(self.level_paths)}: {level.name}",
            True,
            TEXT_COLOR,
        )
        self.screen.blit(title, (16, 12))
        attempts = self.font.render(f"Attempts: {self.game.attempts}", True, DIM_TEXT)
        self.screen.blit(attempts, (16, 40))
        hint = self.font.render(
            "Drag the blue ball to aim - R: retry  N/P: level  ESC: quit",
            True,
            DIM_TEXT,
        )
        self.screen.blit(hint, (16, level.height - 32))

        if self.game.status == GameStatus.WON:
            self._banner("SOLVED!  Press N for next level", GOAL_COLOR)
        elif self.game.status == GameStatus.LOST:
            self._banner("Missed!  Press R to retry", HAZARD_COLOR)

    def _banner(self, text: str, color) -> None:
        surface = self.big_font.render(text, True, color)
        rect = surface.get_rect(
            center=(self.game.level.width // 2, self.game.level.height // 2)
        )
        backdrop = pygame.Surface((rect.width + 40, rect.height + 24), pygame.SRCALPHA)
        backdrop.fill((0, 0, 0, 170))
        self.screen.blit(backdrop, (rect.x - 20, rect.y - 12))
        self.screen.blit(surface, rect)

    # ------------------------------------------------------------------
    def run(self) -> None:
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            running = self.handle_events()
            self.update(min(dt, 1 / 30))  # clamp dt to keep physics stable
            self.draw()
        pygame.quit()
        sys.exit()


def main() -> None:
    level_paths = [str(p) for p in discover_levels()]
    if not level_paths:
        print("No level files found in the 'levels/' directory.")
        sys.exit(1)
    PhysicsPuzzleApp(level_paths).run()


if __name__ == "__main__":
    main()
