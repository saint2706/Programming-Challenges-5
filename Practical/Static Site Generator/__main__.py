"""Static Site Generator CLI.

Entry point for generating static sites.
"""

from __future__ import annotations

import argparse
import sys
import os
from pathlib import Path

# Hack to support running as a script despite spaces in folder name
sys.path.append(os.path.dirname(__file__))

try:
    from generator import SiteGenerator
except ImportError:
    # Fallback for package mode (unlikely with spaces)
    from .generator import SiteGenerator


def main(argv: list[str] | None = None) -> int:
    """
    Docstring for main.
    """
    parser = argparse.ArgumentParser(description="Static Site Generator")
    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Input directory containing 'content' and 'templates'",
    )
    parser.add_argument(
        "--output", required=True, type=Path, help="Output directory for generated HTML"
    )
    parser.add_argument(
        "--base-url", default="/", help="Base URL for the site (default: /)"
    )

    args = parser.parse_args(argv)

    try:
        generator = SiteGenerator(args.input, args.output, args.base_url)
        generator.build()
        print(f"Site generated successfully at {args.output}")
    except Exception as e:
        print(f"Error: {e}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
