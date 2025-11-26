# Image Compression Tool

A lightweight Pillow-based utility to compress images with configurable JPEG quality and an optional lossless optimization pass. The script supports compressing a single image or batch processing a folder.

## Requirements
- Python 3.9+
- [Pillow](https://python-pillow.org/)

Install dependencies:

```bash
pip install pillow
```

## Usage

Compress a single image (writes `<name>_compressed.ext` next to the source by default):

```bash
python compress_image.py path/to/photo.jpg --quality 70 --optimize
```

Specify an explicit output path:

```bash
python compress_image.py path/to/photo.jpg --output compressed/photo.jpg --quality 60
```

Enable lossless optimization only (keeps default JPEG quality 75):

```bash
python compress_image.py path/to/photo.jpg --optimize
```

## Batch compress a folder of images

To compress every supported image in a folder (jpg, jpeg, png, webp) into a `compressed/` subfolder using concurrent workers and batched scheduling (defaults to 8 images per batch):

```bash
python compress_image.py path/to/images_directory --quality 65 --optimize --workers 8 --batch-size 8
```

Choose a custom output directory for the batch job:

```bash
python compress_image.py path/to/images_directory --output-dir path/to/output --quality 80 --workers 6
```

- `--workers` controls how many threads concurrently compress images (defaults to a CPU-based heuristic).
- `--batch-size` controls how many files are submitted to the worker pool at once to balance throughput and memory usage.

Each output image preserves the original filename and format while applying the desired compression settings.
