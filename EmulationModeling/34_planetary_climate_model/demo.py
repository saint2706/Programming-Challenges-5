"""CLI demo for the planetary climate toy models."""

from __future__ import annotations

import argparse

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

    mid_idx = len(final_profile) // 2
    print(f"  Equator temperature: {final_profile[mid_idx]:.2f} K")


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
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_zero_d(args)
    run_latitudinal(args)


if __name__ == "__main__":
    main()
