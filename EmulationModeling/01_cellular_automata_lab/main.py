"""Cellular Automata Lab entry point.

Launches the cellular automata visualization with configurable grid dimensions
and cell rendering size. Uses Conway's Game of Life rules (B3/S23) by default.
"""

import argparse

from ca_engine import CAEngine
from visualizer import Visualizer


def main():
    parser = argparse.ArgumentParser(description="Cellular Automata Lab")
    parser.add_argument("--width", type=int, default=80, help="Grid width")
    parser.add_argument("--height", type=int, default=60, help="Grid height")
    parser.add_argument(
        "--cell_size", type=int, default=10, help="Pixel size of each cell"
    )

    args = parser.parse_args()

    # Initialize engine with Conway's Game of Life rules (B3/S23)
    engine = CAEngine(args.width, args.height, rule_b=(3,), rule_s=(2, 3))
    engine.randomize(0.2)

    viz = Visualizer(engine, cell_size=args.cell_size)
    viz.run()


if __name__ == "__main__":
    main()
