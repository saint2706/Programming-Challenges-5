import numpy as np
from simulation_core.physics import PhysicsWorld, RigidBody

from .models import RigidBodyConfig


class PhysicsSimulation:
    def __init__(self, config: RigidBodyConfig):
        self.config = config
        self.world = PhysicsWorld(gravity=config.gravity)
        self.setup_scene()

    def setup_scene(self):
        for i in range(self.config.num_bodies):
            pos = np.random.rand(3) * 5 + np.array([0, 5, 0])  # Start high up
            vel = (np.random.rand(3) - 0.5) * 2
            body = RigidBody(position=pos, velocity=vel, mass=1.0, radius=0.5)
            self.world.add_body(body)

    def run(self):
        dt = 0.05
        steps = int(self.config.duration / dt)

        for i in range(steps):
            self.world.step(dt)
        final_positions = [body.position for body in self.world.bodies]
        print("Final body positions:", final_positions)


def run_simulation():
    config = RigidBodyConfig(duration=5.0)
    sim = PhysicsSimulation(config)
    sim.run()


if __name__ == "__main__":
    run_simulation()
