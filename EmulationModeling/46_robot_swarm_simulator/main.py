import numpy as np
from scipy.spatial import KDTree

from .models import RobotSwarmConfig


class RobotSwarmSimulation:
    def __init__(self, config: RobotSwarmConfig):
        self.config = config
        self.time = 0.0

        # State: [x, y, vx, vy]
        self.positions = np.random.rand(config.num_robots, 2) * [
            config.width,
            config.height,
        ]
        self.velocities = (
            np.random.rand(config.num_robots, 2) - 0.5
        ) * config.max_speed

    def step(self, dt: float = 0.1):
        self.time += dt

        # Boids-like logic using KDTree for efficiency
        tree = KDTree(self.positions)

        # Compute forces
        new_velocities = self.velocities.copy()

        for i in range(self.config.num_robots):
            # Find neighbors
            indices = tree.query_ball_point(
                self.positions[i], self.config.perception_radius
            )
            if len(indices) <= 1:
                continue

            neighbors_pos = self.positions[indices]
            neighbors_vel = self.velocities[indices]

            # 1. Alignment: steer towards average velocity of neighbors
            avg_vel = np.mean(neighbors_vel, axis=0)
            force_align = avg_vel - self.velocities[i]

            # 2. Cohesion: steer towards average position (center of mass)
            center_mass = np.mean(neighbors_pos, axis=0)
            force_cohere = center_mass - self.positions[i]

            # 3. Separation: steer away from neighbors
            force_separate = np.zeros(2)
            for idx in indices:
                if idx == i:
                    continue
                diff = self.positions[i] - self.positions[idx]
                dist_sq = np.dot(diff, diff)
                if dist_sq > 0:
                    force_separate += diff / dist_sq

            total_force = (
                force_align * self.config.alignment_weight
                + force_cohere * self.config.cohesion_weight
                + force_separate * self.config.separation_weight
            )

            new_velocities[i] += total_force * dt

        # Apply Speed Limit
        speeds = np.linalg.norm(new_velocities, axis=1)
        mask = speeds > self.config.max_speed
        new_velocities[mask] = (
            new_velocities[mask] / speeds[mask, None]
        ) * self.config.max_speed

        # Update Position
        self.positions += new_velocities * dt
        self.velocities = new_velocities

        # Wrap around world (Toroidal)
        self.positions[:, 0] %= self.config.width
        self.positions[:, 1] %= self.config.height

    def run(self):
        steps = int(self.config.duration / 0.1)
        for i in range(steps):
            self.step()
            if i % 5 == 0:
                centroid = np.mean(self.positions, axis=0)
                print(f"t={self.time:.1f}s centroid={centroid}")


def run_simulation():
    config = RobotSwarmConfig(duration=20.0)
    sim = RobotSwarmSimulation(config)
    sim.run()


if __name__ == "__main__":
    run_simulation()
