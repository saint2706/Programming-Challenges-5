"""Command-line photo de-duplication utility using perceptual hashes.

The tool scans a directory for image files, computes both average hash (aHash)
 and perceptual hash (pHash) values, and reports exact as well as near
 duplicates using Hamming distance. Optionally, duplicate groups can be moved
 into a review directory for manual inspection.
"""

from __future__ import annotations

import argparse
import itertools
import shutil
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence

import imagehash
from PIL import Image

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".gif",
    ".tiff",
    ".webp",
}


@dataclass
class HashRecord:
    path: Path
    hash_value: imagehash.ImageHash

    @property
    def hex(self) -> str:
        return str(self.hash_value)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Find duplicate and near-duplicate photos using perceptual hashing."
    )
    parser.add_argument(
        "directory", type=Path, help="Root directory to scan for images"
    )
    parser.add_argument(
        "--hash-type",
        choices=["ahash", "phash", "both"],
        default="both",
        help="Hash algorithm(s) to use. Both types increase accuracy at a slight performance cost.",
    )
    parser.add_argument(
        "--hash-size",
        type=int,
        default=16,
        help="Hash size passed to imagehash (higher values improve discrimination at the cost of speed).",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=4,
        help="Hamming distance threshold for near-duplicate detection (0 disables near-duplicate search).",
    )
    parser.add_argument(
        "--review-dir",
        type=Path,
        default=None,
        help="Optional directory where duplicate groups will be moved for review.",
    )
    parser.add_argument(
        "--move",
        action="store_true",
        help="Move duplicate groups into the review directory. Without this flag, groups are only reported.",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        default=True,
        help="Recursively scan nested folders (enabled by default).",
    )
    parser.add_argument(
        "--no-recursive",
        dest="recursive",
        action="store_false",
        help="Disable recursive scanning.",
    )
    return parser.parse_args(argv)


def iter_image_files(root: Path, recursive: bool = True) -> Iterable[Path]:
    if not root.exists():
        raise FileNotFoundError(f"Input directory does not exist: {root}")

    if recursive:
        walker = root.rglob("*")
    else:
        walker = root.glob("*")

    for path in walker:
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS:
            yield path


def compute_hash(path: Path, hash_type: str, hash_size: int) -> imagehash.ImageHash:
    with Image.open(path) as img:
        if hash_type == "ahash":
            return imagehash.average_hash(img, hash_size=hash_size)
        if hash_type == "phash":
            return imagehash.phash(img, hash_size=hash_size)
        raise ValueError(f"Unsupported hash type: {hash_type}")


def collect_hashes(
    directory: Path, hash_type: str, hash_size: int, recursive: bool
) -> Dict[str, List[Path]]:
    hash_buckets: Dict[str, List[Path]] = defaultdict(list)
    for image_path in iter_image_files(directory, recursive=recursive):
        try:
            img_hash = compute_hash(
                image_path, hash_type=hash_type, hash_size=hash_size
            )
        except Exception as exc:  # pylint: disable=broad-exception-caught
            print(f"[warn] Skipping {image_path} ({exc})", file=sys.stderr)
            continue
        hash_buckets[str(img_hash)].append(image_path)
    return hash_buckets


def find_exact_duplicates(hash_buckets: Dict[str, List[Path]]) -> List[List[Path]]:
    return [paths for paths in hash_buckets.values() if len(paths) > 1]


def build_near_duplicate_groups(
    records: List[HashRecord], threshold: int
) -> List[List[Path]]:
    if threshold <= 0 or len(records) < 2:
        return []

    parent: Dict[Path, Path] = {}

    def find(x: Path) -> Path:
        parent.setdefault(x, x)
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]

    def union(x: Path, y: Path) -> None:
        root_x, root_y = find(x), find(y)
        if root_x != root_y:
            parent[root_y] = root_x

    for rec_a, rec_b in itertools.combinations(records, 2):
        distance = rec_a.hash_value - rec_b.hash_value
        if distance <= threshold:
            union(rec_a.path, rec_b.path)

    groups: Dict[Path, List[Path]] = defaultdict(list)
    for record in records:
        groups[find(record.path)].append(record.path)

    return [paths for paths in groups.values() if len(paths) > 1]


def report_groups(groups: List[List[Path]], label: str) -> None:
    if not groups:
        print(f"No {label} duplicates found.")
        return

    print(f"{label.capitalize()} duplicate groups: {len(groups)}")
    for idx, group in enumerate(groups, start=1):
        print(f"  Group {idx}:")
        for path in group:
            print(f"    - {path}")


def move_groups(groups: List[List[Path]], review_dir: Path, label: str) -> None:
    review_dir.mkdir(parents=True, exist_ok=True)
    for idx, group in enumerate(groups, start=1):
        target_group_dir = review_dir / f"{label}_group_{idx}"
        target_group_dir.mkdir(parents=True, exist_ok=True)
        for path in group:
            destination = target_group_dir / path.name
            counter = 1
            while destination.exists():
                destination = (
                    target_group_dir
                    / f"{destination.stem}_{counter}{destination.suffix}"
                )
                counter += 1
            shutil.move(str(path), destination)
    print(f"Moved {sum(len(g) for g in groups)} files into {review_dir}")


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)

    hash_types: List[str]
    if args.hash_type == "both":
        hash_types = ["ahash", "phash"]
    else:
        hash_types = [args.hash_type]

    all_exact_groups: List[List[Path]] = []
    all_near_groups: List[List[Path]] = []

    for htype in hash_types:
        print(
            f"Scanning {args.directory} using {htype} (hash size={args.hash_size})..."
        )
        hash_buckets = collect_hashes(
            args.directory,
            hash_type=htype,
            hash_size=args.hash_size,
            recursive=args.recursive,
        )
        records = [
            HashRecord(path=path, hash_value=imagehash.hex_to_hash(hash_hex))
            for hash_hex, paths in hash_buckets.items()
            for path in paths
        ]

        exact_groups = find_exact_duplicates(hash_buckets)
        near_groups = build_near_duplicate_groups(records, threshold=args.threshold)

        if exact_groups:
            print(
                f"[exact {htype}] {sum(len(g) for g in exact_groups)} files in {len(exact_groups)} groups"
            )
        if near_groups:
            print(
                f"[near  {htype}] {sum(len(g) for g in near_groups)} files in {len(near_groups)} groups (threshold={args.threshold})"
            )

        report_groups(exact_groups, label=f"exact {htype}")
        report_groups(near_groups, label=f"near {htype}")

        all_exact_groups.extend(exact_groups)
        all_near_groups.extend(near_groups)

        if args.review_dir and args.move:
            move_groups(
                exact_groups + near_groups, args.review_dir / htype, label=htype
            )

    if not all_exact_groups and not all_near_groups:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
