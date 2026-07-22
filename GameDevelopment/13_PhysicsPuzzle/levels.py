"""Level loading and win/lose logic for the physics puzzle.

Levels are plain JSON files (see the ``levels/`` directory) describing the
launch ball, the target ball, obstacles, walls, the goal region and optional
hazard regions. Keeping levels as data means new puzzles can be authored without
touching any code.

This module is intentionally free of any rendering/`pygame` code so that the
puzzle rules can be unit-tested headlessly.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from physics import Body, Rect, Vec2, World

LEVELS_DIR = Path(__file__).resolve().parent / "levels"


@dataclass
class BallSpec:
    x: float
    y: float
    radius: float
    mass: float = 1.0
    restitution: float = 0.6
    friction: float = 0.02


@dataclass
class Level:
    """A parsed puzzle level."""

    name: str
    width: int
    height: int
    gravity: Vec2
    launch: BallSpec
    target: BallSpec
    goal: Rect
    max_power: float = 1200.0
    description: str = ""
    walls: list[Rect] = field(default_factory=list)
    obstacles: list[BallSpec] = field(default_factory=list)
    hazards: list[Rect] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Level":
        """Build a :class:`Level` from a decoded JSON dictionary.

        Raises :class:`ValueError` (via :func:`_require`) when required keys are
        missing so that malformed level files fail loudly.
        """

        def ball(spec: dict[str, Any], default_r: float = 15.0) -> BallSpec:
            return BallSpec(
                x=float(_require(spec, "x")),
                y=float(_require(spec, "y")),
                radius=float(spec.get("radius", default_r)),
                mass=float(spec.get("mass", 1.0)),
                restitution=float(spec.get("restitution", 0.6)),
                friction=float(spec.get("friction", 0.02)),
            )

        def rect(spec: dict[str, Any]) -> Rect:
            return Rect(
                x=float(_require(spec, "x")),
                y=float(_require(spec, "y")),
                w=float(_require(spec, "w")),
                h=float(_require(spec, "h")),
                name=str(spec.get("name", "")),
            )

        gravity_raw = data.get("gravity", [0.0, 800.0])
        return cls(
            name=str(data.get("name", "Untitled")),
            description=str(data.get("description", "")),
            width=int(data.get("width", 800)),
            height=int(data.get("height", 600)),
            gravity=Vec2(float(gravity_raw[0]), float(gravity_raw[1])),
            launch=ball(_require(data, "launch")),
            target=ball(_require(data, "target"), default_r=18.0),
            goal=rect(_require(data, "goal")),
            max_power=float(data.get("max_power", 1200.0)),
            walls=[rect(w) for w in data.get("walls", [])],
            obstacles=[ball(o) for o in data.get("obstacles", [])],
            hazards=[rect(h) for h in data.get("hazards", [])],
        )

    @classmethod
    def load(cls, path: str | Path) -> "Level":
        with open(path, "r", encoding="utf-8") as handle:
            return cls.from_dict(json.load(handle))


def _require(data: dict[str, Any], key: str) -> Any:
    if key not in data:
        raise ValueError(f"Level is missing required key: {key!r}")
    return data[key]


def discover_levels(directory: str | Path = LEVELS_DIR) -> list[Path]:
    """Return the level JSON files in ``directory`` sorted by filename."""
    directory = Path(directory)
    if not directory.exists():
        return []
    return sorted(directory.glob("*.json"))


class GameStatus(Enum):
    AIMING = "aiming"
    SIMULATING = "simulating"
    WON = "won"
    LOST = "lost"


class PuzzleGame:
    """Wraps a :class:`Level` with a :class:`World` and win/lose logic.

    Usage::

        game = PuzzleGame(level)
        game.launch(Vec2(600, -300))   # give the ball an initial velocity
        while game.status == GameStatus.SIMULATING:
            game.update(1 / 60)
    """

    def __init__(self, level: Level):
        self.level = level
        self.status = GameStatus.AIMING
        self.attempts = 0
        self.world = World(
            gravity=level.gravity.copy(),
            bounds=Rect(0, 0, level.width, level.height),
        )
        self._build_world()

    def _build_world(self) -> None:
        self.launch_ball = Body(
            position=Vec2(self.level.launch.x, self.level.launch.y),
            radius=self.level.launch.radius,
            mass=self.level.launch.mass,
            restitution=self.level.launch.restitution,
            friction=self.level.launch.friction,
            name="launch",
        )
        self.target_ball = Body(
            position=Vec2(self.level.target.x, self.level.target.y),
            radius=self.level.target.radius,
            mass=self.level.target.mass,
            restitution=self.level.target.restitution,
            friction=self.level.target.friction,
            name="target",
            is_target=True,
        )
        self.world.add_body(self.launch_ball)
        self.world.add_body(self.target_ball)
        for spec in self.level.obstacles:
            self.world.add_body(
                Body(
                    position=Vec2(spec.x, spec.y),
                    radius=spec.radius,
                    mass=spec.mass,
                    restitution=spec.restitution,
                    friction=spec.friction,
                    name="obstacle",
                )
            )
        for wall in self.level.walls:
            self.world.add_wall(wall)

    # ------------------------------------------------------------------
    def aim_velocity(self, drag_start: Vec2, drag_end: Vec2) -> Vec2:
        """Convert a drag gesture into a launch velocity (capped to max power).

        The ball is launched *opposite* to the drag direction, slingshot-style.
        """
        pull = drag_start - drag_end
        speed = pull.length()
        if speed > self.level.max_power:
            pull = pull.normalized() * self.level.max_power
        return pull

    def launch(self, velocity: Vec2) -> None:
        """Fire the launch ball with the given velocity and begin simulating."""
        if self.status not in (GameStatus.AIMING,):
            return
        self.launch_ball.velocity = velocity
        self.attempts += 1
        self.status = GameStatus.SIMULATING

    def reset(self) -> None:
        """Return to the initial state so the level can be retried."""
        attempts = self.attempts
        self.world = World(
            gravity=self.level.gravity.copy(),
            bounds=Rect(0, 0, self.level.width, self.level.height),
        )
        self._build_world()
        self.status = GameStatus.AIMING
        self.attempts = attempts

    # ------------------------------------------------------------------
    def update(self, dt: float) -> GameStatus:
        """Advance the simulation by ``dt`` and evaluate win/lose conditions."""
        if self.status != GameStatus.SIMULATING:
            return self.status
        self.world.step(dt)
        self._check_conditions()
        return self.status

    def _check_conditions(self) -> None:
        center = self.target_ball.position
        if self.level.goal.contains_point(center):
            self.status = GameStatus.WON
            return
        for hazard in self.level.hazards:
            if hazard.contains_point(center):
                self.status = GameStatus.LOST
                return
        # If everything has settled without reaching the goal, the attempt
        # failed and the player can retry.
        if self.world.is_at_rest:
            self.status = GameStatus.LOST

    def simulate(self, dt: float = 1 / 60, max_steps: int = 3000) -> GameStatus:
        """Run the simulation to completion (used by tests and headless demos)."""
        steps = 0
        while self.status == GameStatus.SIMULATING and steps < max_steps:
            self.update(dt)
            steps += 1
        return self.status
