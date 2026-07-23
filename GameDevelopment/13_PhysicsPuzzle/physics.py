"""A small, dependency-free 2D physics engine.

The engine is deliberately compact — enough to drive a physics *puzzle* rather
than a full rigid-body simulation. It supports:

* dynamic circular bodies affected by gravity,
* static axis-aligned rectangles (walls / obstacles),
* circle-vs-rectangle and circle-vs-circle collision resolution with
  restitution (bounciness) and friction, and
* a fixed-timestep integrator for deterministic, testable behaviour.

Coordinates use screen conventions: ``x`` grows to the right and ``y`` grows
*downward*, so positive-``y`` gravity pulls bodies down.

Everything here is pure Python with no external dependencies, which keeps the
simulation fully unit-testable without a display or game window.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Vec2:
    """A tiny 2D vector with the handful of operations the engine needs."""

    x: float = 0.0
    y: float = 0.0

    def __add__(self, other: "Vec2") -> "Vec2":
        return Vec2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: "Vec2") -> "Vec2":
        return Vec2(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> "Vec2":
        return Vec2(self.x * scalar, self.y * scalar)

    __rmul__ = __mul__

    def dot(self, other: "Vec2") -> float:
        return self.x * other.x + self.y * other.y

    def length(self) -> float:
        return math.hypot(self.x, self.y)

    def length_squared(self) -> float:
        return self.x * self.x + self.y * self.y

    def normalized(self) -> "Vec2":
        length = self.length()
        if length == 0:
            return Vec2(0.0, 0.0)
        return Vec2(self.x / length, self.y / length)

    def copy(self) -> "Vec2":
        return Vec2(self.x, self.y)


@dataclass
class Rect:
    """An axis-aligned rectangle defined by its top-left corner and size."""

    x: float
    y: float
    w: float
    h: float
    name: str = ""

    @property
    def left(self) -> float:
        return self.x

    @property
    def right(self) -> float:
        return self.x + self.w

    @property
    def top(self) -> float:
        return self.y

    @property
    def bottom(self) -> float:
        return self.y + self.h

    def contains_point(self, point: Vec2) -> bool:
        return self.left <= point.x <= self.right and self.top <= point.y <= self.bottom

    def closest_point(self, point: Vec2) -> Vec2:
        """The point on (or inside) the rectangle nearest to ``point``."""
        cx = min(max(point.x, self.left), self.right)
        cy = min(max(point.y, self.top), self.bottom)
        return Vec2(cx, cy)


@dataclass
class Body:
    """A dynamic circular body."""

    position: Vec2
    radius: float
    velocity: Vec2 = field(default_factory=Vec2)
    mass: float = 1.0
    restitution: float = 0.6  # 0 = no bounce, 1 = perfectly elastic
    friction: float = 0.02  # fraction of tangential speed lost per contact
    name: str = ""
    is_target: bool = False  # the ball that must reach the goal

    @property
    def inv_mass(self) -> float:
        return 0.0 if self.mass == 0 else 1.0 / self.mass


class World:
    """Holds bodies and static geometry and advances the simulation."""

    def __init__(
        self,
        gravity: Vec2 | None = None,
        bounds: Optional[Rect] = None,
        linear_damping: float = 0.01,
        sleep_speed: float = 3.0,
    ):
        self.gravity = gravity if gravity is not None else Vec2(0.0, 800.0)
        self.bounds = bounds
        self.linear_damping = linear_damping
        self.sleep_speed = sleep_speed
        self.bodies: list[Body] = []
        self.walls: list[Rect] = []

    # ------------------------------------------------------------------
    def add_body(self, body: Body) -> Body:
        self.bodies.append(body)
        return body

    def add_wall(self, wall: Rect) -> Rect:
        self.walls.append(wall)
        return wall

    @property
    def is_at_rest(self) -> bool:
        """True when every body has settled below the sleep threshold."""
        return all(b.velocity.length() < self.sleep_speed for b in self.bodies)

    # ------------------------------------------------------------------
    # Integration
    # ------------------------------------------------------------------
    def step(self, dt: float, substeps: int = 4) -> None:
        """Advance the world by ``dt`` seconds using ``substeps`` sub-steps.

        Sub-stepping keeps fast-moving bodies from tunnelling through thin
        walls and makes collisions more stable.
        """
        sub_dt = dt / substeps
        for _ in range(substeps):
            self._integrate(sub_dt)
            self._resolve_wall_collisions()
            self._resolve_body_collisions()
            if self.bounds is not None:
                self._clamp_to_bounds()

    def _integrate(self, dt: float) -> None:
        damping = max(0.0, 1.0 - self.linear_damping * dt)
        for body in self.bodies:
            if body.inv_mass == 0:
                continue
            body.velocity = body.velocity + self.gravity * dt
            body.velocity = body.velocity * damping
            body.position = body.position + body.velocity * dt

    # ------------------------------------------------------------------
    # Collision resolution
    # ------------------------------------------------------------------
    def _resolve_wall_collisions(self) -> None:
        for body in self.bodies:
            for wall in self.walls:
                self._resolve_circle_rect(body, wall)

    def _resolve_circle_rect(self, body: Body, wall: Rect) -> None:
        closest = wall.closest_point(body.position)
        delta = body.position - closest
        dist_sq = delta.length_squared()

        if dist_sq > body.radius * body.radius:
            return  # no overlap

        if dist_sq == 0.0:
            # Center is inside the rectangle: push out along the axis of least
            # penetration.
            overlaps = {
                "left": body.position.x - wall.left,
                "right": wall.right - body.position.x,
                "top": body.position.y - wall.top,
                "bottom": wall.bottom - body.position.y,
            }
            side = min(overlaps, key=lambda k: overlaps[k])
            normals = {
                "left": Vec2(-1, 0),
                "right": Vec2(1, 0),
                "top": Vec2(0, -1),
                "bottom": Vec2(0, 1),
            }
            normal = normals[side]
            penetration = overlaps[side] + body.radius
        else:
            dist = math.sqrt(dist_sq)
            normal = Vec2(delta.x / dist, delta.y / dist)
            penetration = body.radius - dist

        # Positional correction: move the body out of the wall.
        body.position = body.position + normal * penetration

        # Velocity response: reflect the normal component, damp the tangent.
        vn = body.velocity.dot(normal)
        if vn < 0:
            body.velocity = body.velocity - normal * ((1 + body.restitution) * vn)
            # Friction on the tangential component.
            tangent = Vec2(-normal.y, normal.x)
            vt = body.velocity.dot(tangent)
            body.velocity = body.velocity - tangent * (vt * body.friction)

    def _resolve_body_collisions(self) -> None:
        count = len(self.bodies)
        for i in range(count):
            for j in range(i + 1, count):
                self._resolve_circle_circle(self.bodies[i], self.bodies[j])

    def _resolve_circle_circle(self, a: Body, b: Body) -> None:
        delta = b.position - a.position
        dist_sq = delta.length_squared()
        radius_sum = a.radius + b.radius
        if dist_sq >= radius_sum * radius_sum:
            return

        if dist_sq == 0.0:
            # Perfectly overlapping: nudge apart along an arbitrary axis.
            normal = Vec2(1.0, 0.0)
            dist = 0.0
        else:
            dist = math.sqrt(dist_sq)
            normal = Vec2(delta.x / dist, delta.y / dist)

        penetration = radius_sum - dist
        inv_mass_sum = a.inv_mass + b.inv_mass
        if inv_mass_sum == 0:
            return

        # Positional correction proportional to inverse mass.
        correction = normal * (penetration / inv_mass_sum)
        a.position = a.position - correction * a.inv_mass
        b.position = b.position + correction * b.inv_mass

        # Impulse response along the collision normal.
        relative_velocity = b.velocity - a.velocity
        vn = relative_velocity.dot(normal)
        if vn > 0:
            return  # already separating
        restitution = min(a.restitution, b.restitution)
        impulse = -(1 + restitution) * vn / inv_mass_sum
        impulse_vec = normal * impulse
        a.velocity = a.velocity - impulse_vec * a.inv_mass
        b.velocity = b.velocity + impulse_vec * b.inv_mass

    def _clamp_to_bounds(self) -> None:
        """Bounce bodies off the world boundary so nothing escapes the level."""
        assert self.bounds is not None
        b = self.bounds
        for body in self.bodies:
            r = body.radius
            if body.position.x - r < b.left:
                body.position.x = b.left + r
                if body.velocity.x < 0:
                    body.velocity.x = -body.velocity.x * body.restitution
            elif body.position.x + r > b.right:
                body.position.x = b.right - r
                if body.velocity.x > 0:
                    body.velocity.x = -body.velocity.x * body.restitution
            if body.position.y - r < b.top:
                body.position.y = b.top + r
                if body.velocity.y < 0:
                    body.velocity.y = -body.velocity.y * body.restitution
            elif body.position.y + r > b.bottom:
                body.position.y = b.bottom - r
                if body.velocity.y > 0:
                    body.velocity.y = -body.velocity.y * body.restitution
