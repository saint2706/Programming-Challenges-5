from dataclasses import dataclass
from typing import List

import numpy as np


@dataclass
class RigidBody:
    position: np.ndarray  # [x, y, z]
    velocity: np.ndarray  # [vx, vy, vz]
    mass: float
    radius: float = 1.0

    def __post_init__(self):
        self.force = np.zeros(3)


class PhysicsWorld:
    def __init__(self, gravity: float = -9.81):
        self.bodies: List[RigidBody] = []
        self.gravity = np.array([0, gravity, 0])

    def add_body(self, body: RigidBody):
        self.bodies.append(body)

    def step(self, dt: float):
        # Symplectic Euler for stability
        for body in self.bodies:
            # F = ma => a = F/m
            acc = (body.force / body.mass) + self.gravity
            body.velocity += acc * dt
            body.position += body.velocity * dt

            # Reset forces
            body.force = np.zeros(3)

            # Simple floor collision
            if body.position[1] < 0:
                body.position[1] = 0
                body.velocity[1] *= -0.5  # restitution
