"""Download and slice the CC0 art and audio used by :mod:`main`.

Sprites come from Kenney's *Tower Defense (top-down)* pack, which ships a single
64px tilesheet. Rather than commit the whole sheet, this script slices out the
tiles the game actually draws and saves each as its own PNG — the sheet is
23 tiles wide, so a tile's flat index maps to ``(index // 23, index % 23)``.

Sound comes from the Sci-Fi Sounds and UI Audio packs, fonts from Kenney Fonts.
Everything is CC0 (public domain).

    python fetch_assets.py            # skip files that already exist
    python fetch_assets.py --force    # re-download and overwrite

Slicing needs Pillow. Without it the script still fetches the fonts, the audio
and the raw tilesheet, and tells you what it skipped.
"""

from __future__ import annotations

import argparse
import io
import re
import shutil
import sys
import urllib.request
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSETS = HERE / "assets"
CACHE = HERE / ".asset-cache"

TD_PACK = "tower-defense-top-down"
TILESHEET = "Tilesheet/towerDefense_tilesheet.png"
#: Tiles across the Kenney tower-defense tilesheet.
SHEET_COLUMNS = 23
TILE_PIXELS = 64

#: ``destination name -> flat tile index on the tilesheet``.
TILES: dict[str, int] = {
    # Terrain
    "tile_grass.png": 157,
    "tile_dirt.png": 158,
    # Build plot marker and the pedestal drawn under every tower
    "plot_open.png": 41,
    "base_stone.png": 84,
    # Turret heads (all point up, so the renderer can rotate them)
    "turret_cannon.png": 203,
    "turret_frost.png": 227,
    "turret_mortar.png": 206,
    "turret_gatling.png": 226,
    "turret_flak.png": 205,
    # Enemies
    "enemy_grunt.png": 245,
    "enemy_runner.png": 246,
    "enemy_armoured.png": 247,
    "enemy_boss.png": 250,
    "enemy_flyer.png": 271,
    # Projectiles
    "bullet.png": 272,
    "shell.png": 275,
    "frost_bolt.png": 273,
    "rocket.png": 251,
    # Effects and scenery
    "explosion.png": 296,
    "tree.png": 130,
    "bush.png": 131,
    "rock.png": 136,
}

#: ``(pack slug, path inside the ZIP, destination file name)``.
FILES: tuple[tuple[str, str, str], ...] = (
    ("kenney-fonts", "Fonts/Kenney Future.ttf", "kenney_future.ttf"),
    ("kenney-fonts", "Fonts/Kenney Mini Square.ttf", "kenney_mini_square.ttf"),
    ("sci-fi-sounds", "Audio/laserSmall_001.ogg", "sfx_shoot.ogg"),
    ("sci-fi-sounds", "Audio/explosionCrunch_000.ogg", "sfx_explosion.ogg"),
    ("ui-audio", "Audio/click1.ogg", "sfx_build.ogg"),
    ("ui-audio", "Audio/switch2.ogg", "sfx_upgrade.ogg"),
    ("interface-sounds", "Audio/error_006.ogg", "sfx_leak.ogg"),
    ("interface-sounds", "Audio/confirmation_002.ogg", "sfx_wave.ogg"),
)

LICENCES: tuple[tuple[str, str, str], ...] = (
    (TD_PACK, "License.txt", "LICENSE-kenney-tower-defense.txt"),
    ("sci-fi-sounds", "License.txt", "LICENSE-kenney-sci-fi-sounds.txt"),
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


def read_member(archive: zipfile.ZipFile, member: str) -> bytes | None:
    """Read ``member``, tolerating pack revisions that moved it."""
    try:
        return archive.read(member)
    except KeyError:
        candidates = [n for n in archive.namelist() if n.endswith(member)]
        if not candidates:
            return None
        return archive.read(candidates[0])


def slice_tiles(force: bool = False) -> int:
    """Cut the wanted tiles out of the tilesheet into individual PNGs."""
    wanted = {
        name: index
        for name, index in TILES.items()
        if force or not (ASSETS / name).exists()
    }
    if not wanted:
        return 0
    try:
        from PIL import Image
    except ImportError:
        print(
            "  !! Pillow is not installed, so tiles cannot be sliced.\n"
            "     Install it with 'pip install Pillow' and re-run, or copy\n"
            f"     {TILESHEET} out of the pack by hand.",
            file=sys.stderr,
        )
        return 0

    print(f"Pack: {TD_PACK}")
    with zipfile.ZipFile(download_pack(TD_PACK, force=force)) as archive:
        raw = read_member(archive, TILESHEET)
        if raw is None:
            print(f"  !! {TILESHEET} missing from the pack", file=sys.stderr)
            return 0
        sheet = Image.open(io.BytesIO(raw)).convert("RGBA")

    written = 0
    for name, index in wanted.items():
        row, col = divmod(index, SHEET_COLUMNS)
        box = (
            col * TILE_PIXELS,
            row * TILE_PIXELS,
            (col + 1) * TILE_PIXELS,
            (row + 1) * TILE_PIXELS,
        )
        sheet.crop(box).save(ASSETS / name)
        print(f"  {name} (tile {index})")
        written += 1
    return written


def extract_files(force: bool = False) -> int:
    """Copy the fonts, sounds and licence notices out of their packs."""
    wanted = [
        entry
        for entry in list(FILES) + list(LICENCES)
        if force or not (ASSETS / entry[2]).exists()
    ]
    if not wanted:
        return 0
    archives: dict[str, zipfile.ZipFile] = {}
    written = 0
    try:
        for slug in sorted({slug for slug, _, _ in wanted}):
            print(f"Pack: {slug}")
            archives[slug] = zipfile.ZipFile(download_pack(slug, force=force))
        for slug, member, name in wanted:
            data = read_member(archives[slug], member)
            if data is None:
                print(f"  !! {member} not found in {slug}", file=sys.stderr)
                continue
            (ASSETS / name).write_bytes(data)
            print(f"  {name} ({len(data) / 1024:.1f} KiB)")
            written += 1
    finally:
        for archive in archives.values():
            archive.close()
    return written


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
    ASSETS.mkdir(parents=True, exist_ok=True)
    written = slice_tiles(force=args.force) + extract_files(force=args.force)
    if written:
        print(f"\nWrote {written} file(s) to {ASSETS}")
    else:
        print("All assets already present. Use --force to refresh them.")
    if args.clean_cache and CACHE.exists():
        shutil.rmtree(CACHE)
        print(f"Removed {CACHE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
