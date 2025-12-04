import os
from typing import List, Optional

import imageio
import matplotlib.pyplot as plt
import numpy as np


class SimulationVisualizer:
    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.frames = []

    def save_plot(self, filename: str):
        plt.savefig(os.path.join(self.output_dir, filename))
        plt.close()

    def add_frame(self, fig):
        """Adds current figure to animation frames"""
        # Save figure to a numpy array buffer
        fig.canvas.draw()

        # Modern matplotlib way
        try:
            # Returns RGBA buffer
            buf = fig.canvas.buffer_rgba()
            image = np.asarray(buf)
        except AttributeError:
            # Fallback for older versions or different backends if needed
            image = np.frombuffer(fig.canvas.tostring_rgb(), dtype="uint8")
            image = image.reshape(fig.canvas.get_width_height()[::-1] + (3,))

        self.frames.append(image)

    def save_gif(self, filename: str, fps: int = 10):
        if not self.frames:
            print("No frames to save.")
            return
        path = os.path.join(self.output_dir, filename)
        imageio.mimsave(path, self.frames, fps=fps)
        print(f"Saved GIF to {path}")
        self.frames = []  # clear

    def save_mp4(self, filename: str, fps: int = 24):
        if not self.frames:
            print("No frames to save.")
            return
        path = os.path.join(self.output_dir, filename)
        imageio.mimsave(path, self.frames, fps=fps, format="mp4")
        print(f"Saved MP4 to {path}")
        self.frames = []
