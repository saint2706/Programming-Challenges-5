import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from simulation_core.physics import PhysicsWorld, RigidBody
from simulation_core.visualization import SimulationVisualizer
from .models import RigidBodyConfig

class PhysicsSimulation:
    def __init__(self, config: RigidBodyConfig):
        self.config = config
        self.visualizer = SimulationVisualizer(output_dir=f"EmulationModeling/49_3d_rigid_body_physics_engine/{config.output_dir}")
        self.world = PhysicsWorld(gravity=config.gravity)
        self.setup_scene()

    def setup_scene(self):
        for i in range(self.config.num_bodies):
            pos = np.random.rand(3) * 5 + np.array([0, 5, 0]) # Start high up
            vel = (np.random.rand(3) - 0.5) * 2
            body = RigidBody(position=pos, velocity=vel, mass=1.0, radius=0.5)
            self.world.add_body(body)

    def run(self):
        dt = 0.05
        steps = int(self.config.duration / dt)

        for i in range(steps):
            self.world.step(dt)
            if i % 2 == 0:
                self.snapshot(i * dt)

        self.visualizer.save_gif("rigid_bodies.gif")

    def snapshot(self, t):
        fig = plt.figure(figsize=(8, 8))
        ax = fig.add_subplot(111, projection='3d')

        # Draw floor
        xx, zz = np.meshgrid(np.linspace(-5, 10, 2), np.linspace(-5, 10, 2))
        ax.plot_surface(xx, np.zeros_like(xx), zz, alpha=0.2, color='gray')

        # Draw bodies
        for body in self.world.bodies:
            ax.scatter(body.position[0], body.position[1], body.position[2], s=100, c='red')

        ax.set_xlim(-5, 10)
        ax.set_ylim(0, 15)
        ax.set_zlim(-5, 10)
        ax.set_xlabel('X')
        ax.set_ylabel('Y (Up)')
        ax.set_zlabel('Z')
        ax.set_title(f"Physics Engine (t={t:.2f})")

        self.visualizer.add_frame(fig)
        plt.close(fig)

def run_simulation():
    config = RigidBodyConfig(duration=5.0)
    sim = PhysicsSimulation(config)
    sim.run()

if __name__ == "__main__":
    run_simulation()
