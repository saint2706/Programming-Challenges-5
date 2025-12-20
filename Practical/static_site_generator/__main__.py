"""Static Site Generator CLI.

Entry point for generating static sites.
"""

from __future__ import annotations

import argparse
from pathlib import Path

try:
    from generator import SiteGenerator
except ImportError:
    from .generator import SiteGenerator


def main(argv: list[str] | None = None) -> int:
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
