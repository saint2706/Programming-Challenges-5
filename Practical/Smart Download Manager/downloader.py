"""Smart Download Manager with multi-threaded chunk downloading.

This module provides a command-line tool for downloading files with support for:
- Multi-threaded concurrent chunk downloads for faster speeds
- Progress bar visualization
- MD5 checksum verification
- HTTP Range requests for resumable downloads

Usage:
    python downloader.py <url> [-t threads] [-o output] [-c checksum]
"""

import argparse
import hashlib
import os
import threading

import requests
from tqdm import tqdm


def get_file_size(url):
    """Get the size of a remote file via HTTP HEAD request.

    Args:
        url: The URL to check.

    Returns:
        int: The file size in bytes, or 0 if unavailable.
    """
    try:
        response = requests.head(url, allow_redirects=True)
        return int(response.headers.get("content-length", 0))
    except Exception as e:
        print(f"Error getting file size: {e}")
        return 0


def download_chunk(url, start, end, filename, chunk_id, progress_bar=None):
    """Download a specific byte range of a file.

    Args:
        url: The URL to download from.
        start: Start byte position.
        end: End byte position.
        filename: Local file to write to.
        chunk_id: Identifier for this chunk (for logging).
        progress_bar: Optional tqdm progress bar to update.
    """
    headers = {"Range": f"bytes={start}-{end}"}
    try:
        response = requests.get(url, headers=headers, stream=True)
        with open(filename, "r+b") as f:
            f.seek(start)
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
                    if progress_bar:
                        progress_bar.update(len(chunk))
    except Exception as e:
        print(f"Error downloading chunk {chunk_id}: {e}")


def calculate_checksum(filename, algorithm="md5"):
    """Calculate the hash checksum of a file.

    Args:
        filename: Path to the file.
        algorithm: Hash algorithm name (default 'md5').

    Returns:
        str: Hexadecimal digest of the file hash.
    """
    hash_func = getattr(hashlib, algorithm)()
    with open(filename, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)
    return hash_func.hexdigest()


def download_file(url, num_threads=4, output_file=None, checksum=None):
    """Download a file using multiple threads.

    Args:
        url: The URL to download.
        num_threads: Number of concurrent download threads.
        output_file: Output filename (defaults to URL basename).
        checksum: Expected MD5 checksum for verification.
    """
    if not output_file:
        output_file = url.split("/")[-1]

    file_size = get_file_size(url)
    if file_size == 0:
        print("Could not determine file size or file is empty.")
        return

    print(f"Downloading {output_file} ({file_size / (1024*1024):.2f} MB)")

    # Create empty file of appropriate size
    if not os.path.exists(output_file):
        with open(output_file, "wb") as f:
            f.write(b"\0" * file_size)

    chunk_size = file_size // num_threads
    threads = []

    progress_bar = tqdm(total=file_size, unit="B", unit_scale=True, desc=output_file)

    for i in range(num_threads):
        start = i * chunk_size
        end = start + chunk_size - 1 if i < num_threads - 1 else file_size - 1
        t = threading.Thread(
            target=download_chunk, args=(url, start, end, output_file, i, progress_bar)
        )
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    progress_bar.close()
    print("\nDownload complete!")

    if checksum:
        print("Verifying checksum...")
        calculated_checksum = calculate_checksum(output_file)
        if calculated_checksum == checksum:
            print("Checksum verified successfully!")
        else:
            print(
                f"Checksum verification failed! Expected {checksum}, got {calculated_checksum}"
            )


def main():
    """Entry point for the download manager CLI."""
    parser = argparse.ArgumentParser(description="Smart Download Manager")
    parser.add_argument("url", help="URL of the file to download")
    parser.add_argument(
        "-t", "--threads", type=int, default=4, help="Number of threads (default: 4)"
    )
    parser.add_argument("-o", "--output", help="Output filename")
    parser.add_argument(
        "-c", "--checksum", help="Expected MD5 checksum for verification"
    )

    args = parser.parse_args()

    download_file(args.url, args.threads, args.output, args.checksum)


if __name__ == "__main__":
    main()
