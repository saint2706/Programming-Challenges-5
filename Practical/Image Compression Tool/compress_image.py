"""Image compression utility using Pillow.

This script can compress a single image with configurable JPEG quality
settings and a lossless optimization flag. It can also batch compress
all supported images in a folder.
"""

from __future__ import annotations

import argparse
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from itertools import islice
from pathlib import Path
from typing import Iterable

from PIL import Image

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def compress_image(
    image_path: Path, output_path: Path, quality: int, optimize: bool
) -> Path:
    """Compress a single image and save it to ``output_path``.

    Args:
        image_path: Path to the image to compress.
        output_path: Destination path for the compressed image.
        quality: JPEG quality (1-95). Ignored for formats that do not
            use a quality setting, but still accepted for Pillow API
            compatibility.
        optimize: Whether to enable Pillow's lossless optimization pass.

    Returns:
        The path to the written compressed image.
    """

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with Image.open(image_path) as img:
        save_kwargs = {"optimize": optimize}

        target_suffix = output_path.suffix.lower()
        image_format = (target_suffix.lstrip(".") or img.format or "JPEG").upper()

        if image_format == "JPEG":
            # JPEG does not support alpha; drop it to avoid errors.
            if img.mode in {"RGBA", "LA", "P"}:
                img = img.convert("RGB")
            save_kwargs["quality"] = max(1, min(quality, 95))

        img.save(output_path, format=image_format, **save_kwargs)

    return output_path


def compress_directory(
    input_dir: Path,
    output_dir: Path,
    quality: int,
    optimize: bool,
    *,
    workers: int | None = None,
    batch_size: int = 8,
    extensions: Iterable[str] = SUPPORTED_EXTENSIONS,
) -> list[Path]:
    """Compress all supported images under ``input_dir`` into ``output_dir``.

    Args:
        input_dir: Directory containing images to compress.
        output_dir: Destination directory for compressed images.
        quality: JPEG quality for lossy compression.
        optimize: Whether to enable lossless optimization.
        workers: Number of threads to use for concurrent compression. Defaults
            to a sensible value based on available CPU cores.
        batch_size: Number of images submitted to the worker pool at a time to
            balance throughput and memory usage.
        extensions: Iterable of file suffixes to include.

    Returns:
        List of paths to the compressed images.
    """

    normalized_exts = {ext.lower() for ext in extensions}
    output_dir.mkdir(parents=True, exist_ok=True)

    def _iter_batches(iterable: Iterable[Path], size: int) -> Iterable[list[Path]]:
        iterator = iter(iterable)
        while True:
            batch = list(islice(iterator, size))
            if not batch:
                return
            yield batch

    supported_files = sorted(
        p
        for p in input_dir.iterdir()
        if p.is_file() and p.suffix.lower() in normalized_exts
    )

    if not supported_files:
        return []

    max_workers = workers or min(32, (os.cpu_count() or 1) + 4)
    compressed_paths: list[Path] = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for batch in _iter_batches(supported_files, batch_size):
            futures = {
                executor.submit(
                    compress_image,
                    image_path,
                    output_dir / image_path.name,
                    quality,
                    optimize,
                ): image_path
                for image_path in batch
            }

            for future in as_completed(futures):
                compressed_paths.append(future.result())

    return compressed_paths


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compress images with Pillow using JPEG quality and optimization options.",
    )
    parser.add_argument(
        "input_path", type=Path, help="Image file or directory to compress."
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output file path for single image compression.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Destination directory for batch compression (defaults to <input>/compressed).",
    )
    parser.add_argument(
        "-q",
        "--quality",
        type=int,
        default=75,
        help="JPEG quality (1-95) for lossy compression.",
    )
    parser.add_argument(
        "--optimize",
        action="store_true",
        help="Enable Pillow's lossless optimization during save.",
    )
    parser.add_argument(
        "-w",
        "--workers",
        type=int,
        default=None,
        help="Number of threads for batch compression (defaults to CPU-based heuristic).",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=8,
        help="Submit this many images at a time to balance throughput and memory usage during batch runs.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not args.input_path.exists():
        raise SystemExit(f"Input path does not exist: {args.input_path}")

    if args.input_path.is_file():
        default_output = args.input_path.with_name(
            f"{args.input_path.stem}_compressed{args.input_path.suffix}"
        )
        output_path = args.output or default_output
        compressed_path = compress_image(
            args.input_path, output_path, args.quality, args.optimize
        )
        print(f"Compressed file written to: {compressed_path}")
        return

    if args.input_path.is_dir():
        output_dir = args.output_dir or args.input_path / "compressed"
        compressed = compress_directory(
            args.input_path,
            output_dir,
            args.quality,
            args.optimize,
            workers=args.workers,
            batch_size=max(1, args.batch_size),
        )
        if not compressed:
            print("No supported image files found to compress.")
        else:
            print(f"Compressed {len(compressed)} images into {output_dir}")
        return

    raise SystemExit("Input path must be a file or directory.")


if __name__ == "__main__":
    main()
