import torch
import torch.nn as nn

from .models import NCAConfig


class CAModel(nn.Module):
    def __init__(self, channel_n, hidden_n):
        super().__init__()
        self.channel_n = channel_n
        self.fc0 = nn.Linear(
            channel_n * 3, hidden_n
        )  # Sobel filters (3x3 input context)
        self.fc1 = nn.Linear(hidden_n, channel_n, bias=False)
        with torch.no_grad():
            self.fc1.weight.zero_()

    def forward(self, x):
        # x: [Batch, Channel, H, W]
        # Perception (Sobel filters fixed)
        sobel_x = torch.tensor(
            [[-1.0, 0.0, 1.0], [-2.0, 0.0, 2.0], [-1.0, 0.0, 1.0]], device=x.device
        ).view(1, 1, 3, 3)
        sobel_y = sobel_x.transpose(2, 3)

        # Per-channel convolution
        def depthwise(filt):
            return torch.nn.functional.conv2d(
                x,
                filt.repeat(self.channel_n, 1, 1, 1),
                groups=self.channel_n,
                padding=1,
            )

        grad_x = depthwise(sobel_x)
        grad_y = depthwise(sobel_y)

        # Concatenate state + gradients
        y = torch.cat([x, grad_x, grad_y], dim=1)  # [B, 3*C, H, W]
        y = y.permute(0, 2, 3, 1)  # [B, H, W, 3*C]

        y = torch.relu(self.fc0(y))
        update = self.fc1(y)  # [B, H, W, C]
        update = update.permute(0, 3, 1, 2)  # [B, C, H, W]

        # Stochastic update mask (similar to Growing NCA paper)
        mask = (torch.rand_like(update[:, :1, :, :]) > 0.5).float()
        return x + update * mask


class NCASimulation:
    def __init__(self, config: NCAConfig):
        self.config = config
        self.device = torch.device("cpu")  # Keep it simple
        self.model = CAModel(config.channels, config.hidden_size).to(self.device)

        # Initial State: Seed in center
        self.state = torch.zeros(
            1, config.channels, config.grid_size, config.grid_size, device=self.device
        )
        center = config.grid_size // 2
        self.state[:, 3:, center, center] = 1.0  # Hidden channels seed

    def run(self):
        # We are not training here, just simulating an untrained (or random) NCA.
        # A full task would involve training to match an image, but that requires optimization loop.
        # We will simulate "evolution" from random weights to show the mechanics.

        for i in range(self.config.steps):
            with torch.no_grad():
                self.state = self.model(self.state)

                # Clip to [0, 1] for stability (usually sigmoid is used but this is simplified)
                self.state = torch.clamp(self.state, -10.0, 10.0)

        summary = {
            "min": float(self.state.min().item()),
            "max": float(self.state.max().item()),
            "mean": float(self.state.mean().item()),
        }
        print(f"Final NCA state summary: {summary}")


def run_simulation():
    config = NCAConfig(duration=10)  # Duration unused in steps logic
    sim = NCASimulation(config)
    sim.run()


if __name__ == "__main__":
    run_simulation()
