"""Download the CC0 art and audio used by :mod:`gui_client`.

Everything comes from Kenney's asset packs (https://kenney.nl/assets), which are
released under Creative Commons Zero. The script resolves each pack's current
download URL from its asset page, pulls the ZIP into a cache directory, and
extracts only the handful of files the game needs — the packs themselves are
tens of megabytes, so nothing but the extracted subset is kept.

The extracted files are committed to ``assets/``, so you only need to run this
to refresh them::

    python fetch_assets.py            # skip files that already exist
    python fetch_assets.py --force    # re-download and overwrite
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
import urllib.request
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSETS = HERE / "assets"
CACHE = HERE / ".asset-cache"

#: Kenney asset-page slugs, each resolved to a ZIP URL at run time.
PACKS = ("game-icons", "input-prompts", "boardgame-pack", "kenney-fonts", "ui-audio")

#: ``(pack slug, path inside the ZIP, destination file name)``.
FILES: tuple[tuple[str, str, str], ...] = (
    # Tic-Tac-Toe marks. Both are white so the client can tint them per player.
    ("game-icons", "PNG/White/2x/cross.png", "mark_x.png"),
    ("input-prompts", "Flairs/Double/flair_circle_8.png", "mark_o.png"),
    # Connect Four discs.
    ("boardgame-pack", "PNG/Chips/chipRedWhite_border.png", "chip_red.png"),
    ("boardgame-pack", "PNG/Chips/chipBlue_border.png", "chip_blue.png"),
    # UI chrome.
    ("kenney-fonts", "Fonts/Kenney Future.ttf", "kenney_future.ttf"),
    ("kenney-fonts", "Fonts/Kenney Mini Square.ttf", "kenney_mini_square.ttf"),
    # Sound effects.
    ("boardgame-pack", "Bonus/chipsCollide1.ogg", "sfx_place.ogg"),
    ("ui-audio", "Audio/click1.ogg", "sfx_click.ogg"),
    ("ui-audio", "Audio/switch2.ogg", "sfx_win.ogg"),
    ("ui-audio", "Audio/rollover1.ogg", "sfx_hover.ogg"),
)

#: Licence files copied alongside the assets as provenance.
LICENCES: tuple[tuple[str, str, str], ...] = (
    ("game-icons", "license.txt", "LICENSE-kenney-game-icons.txt"),
    ("boardgame-pack", "license.txt", "LICENSE-kenney-boardgame-pack.txt"),
)

ZIP_PATTERN = re.compile(r"href='(https://kenney\.nl/media/[^']*\.zip)'")


def resolve_pack_url(slug: str) -> str:
    """Find the current ZIP download URL on a Kenney asset page."""
    page = f"https://kenney.nl/assets/{slug}"
    with urllib.request.urlopen(page, timeout=60) as response:
        html = response.read().decode("utf-8", "replace")
    matches = ZIP_PATTERN.findall(html)
    if not matches:
        raise RuntimeError(f"no download link found on {page}")
    return matches[0]


def download_pack(slug: str, force: bool = False) -> Path:
    """Fetch a pack ZIP into the cache, returning its path."""
    CACHE.mkdir(parents=True, exist_ok=True)
    target = CACHE / f"{slug}.zip"
    if target.exists() and not force:
        return target
    url = resolve_pack_url(slug)
    print(f"  downloading {slug} <- {url}")
    urllib.request.urlretrieve(url, target)
    return target


def extract(force: bool = False) -> int:
    """Extract every entry in :data:`FILES` and :data:`LICENCES`."""
    ASSETS.mkdir(parents=True, exist_ok=True)
    wanted = list(FILES) + list(LICENCES)
    missing = [entry for entry in wanted if force or not (ASSETS / entry[2]).exists()]
    if not missing:
        print("All assets already present. Use --force to refresh them.")
        return 0

    needed_packs = sorted({slug for slug, _, _ in missing})
    archives: dict[str, zipfile.ZipFile] = {}
    try:
        for slug in needed_packs:
            print(f"Pack: {slug}")
            archives[slug] = zipfile.ZipFile(download_pack(slug, force=force))
        written = 0
        for slug, member, name in missing:
            archive = archives[slug]
            try:
                data = archive.read(member)
            except KeyError:
                # Kenney occasionally renames files between pack revisions.
                candidates = [n for n in archive.namelist() if n.endswith(member)]
                if not candidates:
                    print(f"  !! {member} not found in {slug}", file=sys.stderr)
                    continue
                data = archive.read(candidates[0])
            (ASSETS / name).write_bytes(data)
            print(f"  {name} ({len(data) / 1024:.1f} KiB)")
            written += 1
    finally:
        for archive in archives.values():
            archive.close()
    print(f"\nWrote {written} file(s) to {ASSETS}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--force", action="store_true", help="re-download and overwrite everything"
    )
    parser.add_argument(
        "--clean-cache",
        action="store_true",
        help="delete the downloaded ZIPs when finished",
    )
    args = parser.parse_args(argv)
    status = extract(force=args.force)
    if args.clean_cache and CACHE.exists():
        shutil.rmtree(CACHE)
        print(f"Removed {CACHE}")
    return status


if __name__ == "__main__":
    raise SystemExit(main())
