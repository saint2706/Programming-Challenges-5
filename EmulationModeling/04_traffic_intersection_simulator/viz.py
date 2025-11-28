"""
Emulation/Modeling project implementation.
"""

import simpy
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from simulation import TrafficIntersection, car_generator

# We need to modify simulation to expose real-time state for visualization
# A generator that yields state every tick?

class SimVisualizer:
    """
    Docstring for SimVisualizer.
    """
    def __init__(self):
        """
        Docstring for __init__.
        """
        self.env = simpy.Environment()
        self.intersection = TrafficIntersection(self.env)
        self.env.process(car_generator(self.env, self.intersection, "NS", 0.2))
        self.env.process(car_generator(self.env, self.intersection, "EW", 0.15))

        self.time_data = []
        self.q_ns_data = []
        self.q_ew_data = []

        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(8, 8))
        self.line_ns, = self.ax1.plot([], [], label="NS Queue")
        self.line_ew, = self.ax1.plot([], [], label="EW Queue")
        self.ax1.set_xlim(0, 100)
        self.ax1.set_ylim(0, 20)
        self.ax1.legend()
        self.ax1.set_title("Queue Lengths")

        # Traffic light status visualization (Bar chart?)
        self.bars = self.ax2.bar(["NS", "EW"], [0, 0], color=["green", "red"])
        self.ax2.set_ylim(0, 1)
        self.ax2.set_title("Traffic Lights (1=Green, 0.5=Yellow, 0=Red)")

    def update(self, frame):
        # Run simulation for 1 unit of time
        """
        Docstring for update.
        """
        self.env.run(until=self.env.now + 1)

        self.time_data.append(self.env.now)
        self.q_ns_data.append(self.intersection.queue_lengths["NS"])
        self.q_ew_data.append(self.intersection.queue_lengths["EW"])

        # Scroll X axis
        if self.env.now > 100:
            self.ax1.set_xlim(self.env.now - 100, self.env.now)

        self.line_ns.set_data(self.time_data, self.q_ns_data)
        self.line_ew.set_data(self.time_data, self.q_ew_data)

        # Update lights
        colors = []
        heights = []
        for direction in ["NS", "EW"]:
            state = self.intersection.lights[direction]
            if state == "green":
                colors.append("green")
                heights.append(1)
            elif state == "yellow":
                colors.append("yellow")
                heights.append(0.5)
            else:
                colors.append("red")
                heights.append(0.2)

        for bar, color, h in zip(self.bars, colors, heights):
            bar.set_color(color)
            bar.set_height(h)

        return self.line_ns, self.line_ew, *self.bars

    def run(self):
        """
        Docstring for run.
        """
        ani = animation.FuncAnimation(self.fig, self.update, interval=50, blit=False)
        plt.show()

if __name__ == "__main__":
    viz = SimVisualizer()
    viz.run()
