import matplotlib.pyplot as plt
import matplotlib.animation as animation
from model import SIRModel

class SIRVisualizer:
    def __init__(self):
        self.model = SIRModel(num_agents=200, width=100, height=100, infection_prob=0.3)

        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(6, 10))

        self.scatter = self.ax1.scatter([], [])
        self.ax1.set_xlim(0, 100)
        self.ax1.set_ylim(0, 100)
        self.ax1.set_title("Agent Positions")

        self.time_data = []
        self.s_data = []
        self.i_data = []
        self.r_data = []

        self.stack = self.ax2.stackplot([], [], [], [], labels=["S", "I", "R"], colors=["blue", "red", "green"])
        self.ax2.set_xlim(0, 200)
        self.ax2.set_ylim(0, 200)
        self.ax2.legend(loc='upper left')
        self.ax2.set_title("SIR Counts")

    def update(self, frame):
        self.model.step()

        # Update Scatter
        positions = [a.pos for a in self.model.agents]
        colors = []
        for a in self.model.agents:
            if a.state == "S": colors.append("blue")
            elif a.state == "I": colors.append("red")
            else: colors.append("green")

        self.scatter.set_offsets(positions)
        self.scatter.set_color(colors)

        # Update Stackplot
        stats = self.model.get_stats()
        self.time_data.append(frame)
        self.s_data.append(stats["S"])
        self.i_data.append(stats["I"])
        self.r_data.append(stats["R"])

        if frame > 200:
            self.ax2.set_xlim(frame - 200, frame)

        self.ax2.clear()
        self.ax2.stackplot(self.time_data, self.s_data, self.i_data, self.r_data,
                           labels=["S", "I", "R"], colors=["blue", "red", "green"])
        self.ax2.legend(loc='upper left')
        self.ax2.set_title("SIR Counts")

        return self.scatter,

    def run(self):
        ani = animation.FuncAnimation(self.fig, self.update, frames=range(1000), interval=50, blit=False)
        plt.show()

if __name__ == "__main__":
    viz = SIRVisualizer()
    viz.run()
