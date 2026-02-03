"""Command-line demo for the weather pattern cellular model."""

from __future__ import annotations

import argparse

try:  # Allow running via `python demo.py` without a package import error.
    from .weather_model import WeatherGrid
except ImportError:  # pragma: no cover - fallback for direct execution
    import pathlib
    import sys

    current_dir = pathlib.Path(__file__).resolve().parent
    sys.path.append(str(current_dir))
    from weather_model import WeatherGrid


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--width", type=int, default=64, help="Grid width")
    parser.add_argument("--height", type=int, default=64, help="Grid height")
    parser.add_argument(
        "--steps", type=int, default=50, help="Number of simulation steps"
    )
    parser.add_argument(
        "--diffusion-rate",
        type=float,
        default=0.15,
        help="Pressure diffusion coefficient",
    )
    parser.add_argument(
        "--moisture-transport-rate",
        type=float,
        default=0.1,
        help="Humidity advection rate scaled by wind",
    )
    parser.add_argument("--dt", type=float, default=1.0, help="Time step")
    parser.add_argument(
        "--seed", type=int, default=7, help="Random seed for reproducibility"
    )
    parser.add_argument(
        "--summary",
        type=str,
        default="pressure_summary.txt",
        help="Where to save the final pressure summary",
    )
    return parser.parse_args()


def main() -> None:
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

    pressure = grid.pressure
    summary = "\n".join(
        [
            f"min={pressure.min():.3f}",
            f"max={pressure.max():.3f}",
            f"mean={pressure.mean():.3f}",
            f"std={pressure.std():.3f}",
        ]
    )
    with open(args.summary, "w", encoding="utf-8") as handle:
        handle.write(summary)
    print(f"Saved pressure summary to {args.summary}")


if __name__ == "__main__":
    main()
