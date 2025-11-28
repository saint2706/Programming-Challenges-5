"""Command-line demo for the weather pattern cellular model."""
from __future__ import annotations

import argparse
import matplotlib

# Use a non-interactive backend for environments without display servers.
matplotlib.use("Agg")
import matplotlib.pyplot as plt

try:  # Allow running via `python demo.py` without a package import error.
    from .weather_model import WeatherGrid
except ImportError:  # pragma: no cover - fallback for direct execution
    import pathlib
    import sys

    current_dir = pathlib.Path(__file__).resolve().parent
    sys.path.append(str(current_dir))
    from weather_model import WeatherGrid


def parse_args() -> argparse.Namespace:
    """
    Docstring for parse_args.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--width", type=int, default=64, help="Grid width")
    parser.add_argument("--height", type=int, default=64, help="Grid height")
    parser.add_argument("--steps", type=int, default=50, help="Number of simulation steps")
    parser.add_argument("--diffusion-rate", type=float, default=0.15, help="Pressure diffusion coefficient")
    parser.add_argument(
        "--moisture-transport-rate",
        type=float,
        default=0.1,
        help="Humidity advection rate scaled by wind",
    )
    parser.add_argument("--dt", type=float, default=1.0, help="Time step")
    parser.add_argument("--seed", type=int, default=7, help="Random seed for reproducibility")
    parser.add_argument(
        "--output",
        type=str,
        default="pressure_heatmap.png",
        help="Where to save the final pressure heatmap",
    )
    return parser.parse_args()


def render_pressure(grid: WeatherGrid, output_path: str) -> None:
    """
    Docstring for render_pressure.
    """
    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(grid.pressure, cmap="coolwarm")
    fig.colorbar(im, ax=ax, shrink=0.75, label="Pressure (hPa)")
    ax.set_title("Cellular Weather Pressure")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def main() -> None:
    """
    Docstring for main.
    """
    args = parse_args()
    grid = WeatherGrid(
        width=args.width,
        height=args.height,
        diffusion_rate=args.diffusion_rate,
        moisture_transport_rate=args.moisture_transport_rate,
        dt=args.dt,
        seed=args.seed,
    )

    for _ in range(args.steps):
        grid.step()

    render_pressure(grid, args.output)
    print(f"Saved pressure heatmap to {args.output}")


if __name__ == "__main__":
    main()
