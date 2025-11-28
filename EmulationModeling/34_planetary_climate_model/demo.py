"""CLI demo for the planetary climate toy models."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt

try:  # pragma: no cover - allow running as a script
    from .climate_model import LatitudinalEnergyBalanceModel, ZeroDEnergyBalanceModel
except ImportError:  # pragma: no cover - fallback for direct execution
    import pathlib
    import sys

    current_dir = pathlib.Path(__file__).resolve().parent
    sys.path.append(str(current_dir))
    from climate_model import LatitudinalEnergyBalanceModel, ZeroDEnergyBalanceModel


def run_zero_d(args: argparse.Namespace) -> None:
    model = ZeroDEnergyBalanceModel(
        solar_constant=args.solar_constant,
        albedo=args.albedo,
        greenhouse_factor=args.greenhouse,
        emissivity=args.emissivity,
        heat_capacity=args.heat_capacity,
        dt=args.timestep,
        initial_temperature=args.initial_temperature,
    )
    result = model.run_to_equilibrium(max_steps=args.steps, tolerance=args.tolerance)
    final_temp = result.temperatures[-1]
    print("Zero-dimensional model:")
    print(f"  Converged: {result.converged} in {result.steps} steps")
    print(f"  Equilibrium temperature: {final_temp:.2f} K")


def run_latitudinal(args: argparse.Namespace) -> None:
    model = LatitudinalEnergyBalanceModel(
        n_zones=args.zones,
        solar_constant=args.solar_constant,
        albedo=args.albedo,
        greenhouse_factor=args.greenhouse,
        emissivity=args.emissivity,
        heat_capacity=args.heat_capacity,
        meridional_diffusivity=args.diffusivity,
        dt=args.timestep,
        initial_temperature=args.initial_temperature,
    )
    result = model.run_to_equilibrium(max_steps=args.steps, tolerance=args.tolerance)
    final_profile = result.temperatures[-1]
    print("\nLatitudinal model:")
    print(f"  Converged: {result.converged} in {result.steps} steps")
    print(
        f"  Final temperature range: {final_profile.min():.2f} – {final_profile.max():.2f} K"
    )

    if args.plot:
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(model.latitudes, final_profile, marker="o")
        ax.set_xlabel("Latitude (deg)")
        ax.set_ylabel("Temperature (K)")
        ax.set_title("Latitudinal energy balance equilibrium")
        ax.grid(True, linestyle=":", alpha=0.5)
        output = Path(args.output)
        fig.tight_layout()
        fig.savefig(output)
        print(f"  Saved profile plot to {output}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--solar-constant",
        type=float,
        default=1361.0,
        help="Top-of-atmosphere solar irradiance (W/m^2)",
    )
    parser.add_argument(
        "--albedo", type=float, default=0.3, help="Planetary Bond albedo (0-1)"
    )
    parser.add_argument(
        "--greenhouse",
        type=float,
        default=0.2,
        help="Fraction of outgoing IR retained by greenhouse gases",
    )
    parser.add_argument(
        "--emissivity",
        type=float,
        default=0.99,
        help="Thermal infrared emissivity (0-1)",
    )
    parser.add_argument(
        "--heat-capacity",
        type=float,
        default=4.2e8,
        help="Effective areal heat capacity (J/m^2/K)",
    )
    parser.add_argument(
        "--timestep",
        type=float,
        default=86_400.0,
        help="Integration timestep (seconds)",
    )
    parser.add_argument(
        "--initial-temperature",
        type=float,
        default=288.0,
        help="Initial temperature guess (K)",
    )
    parser.add_argument(
        "--steps", type=int, default=5000, help="Maximum integration steps"
    )
    parser.add_argument(
        "--tolerance", type=float, default=1e-3, help="Equilibrium tolerance in Kelvin"
    )
    parser.add_argument(
        "--zones",
        type=int,
        default=18,
        help="Number of latitude bands for the 1D model",
    )
    parser.add_argument(
        "--diffusivity",
        type=float,
        default=0.5,
        help="Meridional thermal diffusivity (arbitrary units)",
    )
    parser.add_argument(
        "--plot",
        action="store_true",
        help="Save a plot of the latitudinal equilibrium profile",
    )
    parser.add_argument(
        "--output",
        default="latitudinal_profile.png",
        help="Output path for the profile plot",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_zero_d(args)
    run_latitudinal(args)


if __name__ == "__main__":
    main()
