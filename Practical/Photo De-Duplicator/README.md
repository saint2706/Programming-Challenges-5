# Photo De-Duplicator

A command-line helper for surfacing duplicate and near-duplicate photos using perceptual hashing. It scans a directory of images, computes both aHash and pHash fingerprints, groups identical hashes, and surfaces near matches using a configurable Hamming-distance threshold. Optionally, duplicate groups can be moved into a review directory for manual inspection.

## Features

- aHash and pHash via [Pillow](https://python-pillow.org) + [ImageHash](https://pypi.org/project/ImageHash/)
- Exact duplicate grouping keyed by hash value
- Near-duplicate grouping using Hamming distance with union-find clustering
- Optional move step to stage duplicates into a review folder
- Recursive or flat directory traversal

## Usage

```bash
# Basic scan using both hash types
python Practical/Photo\ De-Duplicator/deduplicator.py /path/to/images

# Use only pHash with a stricter distance threshold
python Practical/Photo\ De-Duplicator/deduplicator.py /path/to/images \
    --hash-type phash \
    --threshold 2

# Move exact + near duplicates into a review directory
python Practical/Photo\ De-Duplicator/deduplicator.py /path/to/images \
    --review-dir /tmp/photo-review \
    --move
```

Exit status is `0` when duplicate groups are found and `1` when no duplicates are detected. Warnings about unreadable or unsupported images are printed to stderr but the scan continues.

## Performance notes

- **Hash size**: Raising `--hash-size` (default `16`) makes hashes more discriminative but increases CPU cost. For tens of thousands of files, consider `--hash-size 8` to reduce runtime.
- **Near-duplicate search**: Hamming-distance grouping is `O(n^2)` in the number of images per hash type. For very large collections, start with `--threshold 0` to find only exact duplicates, or pre-filter by date/album to limit the working set.
- **Disk I/O**: The scanner streams files from disk; placing the review directory on the same disk avoids extra copies when moving matches.
