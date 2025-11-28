"""
Media Library Organizer

Organizes media files (movies) by querying TMDB API and renaming files
to a standard format: "Title (Year)/Title (Year).ext".
"""

import os
import shutil
import argparse
import requests
import re
import logging
from typing import Optional, Dict

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

TMDB_BASE_URL = "https://api.themoviedb.org/3"

def clean_filename(filename: str) -> str:
    """Extract potential movie name and year from filename."""
    # Remove extension
    name = os.path.splitext(filename)[0]
    # Replace dots/underscores with space
    name = name.replace('.', ' ').replace('_', ' ')

    # Simple heuristic: try to find a year (19xx or 20xx)
    match = re.search(r'(.*?)(19\d{2}|20\d{2})', name)
    if match:
        return match.group(1).strip(), match.group(2)

    return name.strip(), None

def search_movie(title: str, year: Optional[str], api_key: str) -> Optional[Dict]:
    """Search TMDB for a movie."""
    url = f"{TMDB_BASE_URL}/search/movie"
    params = {
        'api_key': api_key,
        'query': title,
        'page': 1
    }
    if year:
        params['year'] = year

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        results = response.json().get('results', [])
        if results:
            return results[0] # Return best match
    except Exception as e:
        logging.error(f"Error searching for {title}: {e}")

    return None

def organize_library(source_dir: str, target_dir: str, api_key: str, dry_run: bool = False):
    """Scan source, identify movies, and move to target."""
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    for root, _, files in os.walk(source_dir):
        for file in files:
            if file.lower().endswith(('.mp4', '.mkv', '.avi', '.mov')):
                filepath = os.path.join(root, file)
                title_guess, year_guess = clean_filename(file)

                logging.info(f"Processing: {file} -> Guess: {title_guess} ({year_guess})")

                movie_data = search_movie(title_guess, year_guess, api_key)

                if movie_data:
                    real_title = movie_data['title']
                    release_date = movie_data.get('release_date', '')
                    real_year = release_date.split('-')[0] if release_date else 'Unknown'

                    # Sanitize for filesystem
                    safe_title = "".join([c for c in real_title if c.isalnum() or c in (' ', '-', '_')]).strip()
                    new_folder_name = f"{safe_title} ({real_year})"

                    ext = os.path.splitext(file)[1]
                    new_filename = f"{safe_title} ({real_year}){ext}"

                    dest_folder = os.path.join(target_dir, new_folder_name)
                    dest_path = os.path.join(dest_folder, new_filename)

                    if dry_run:
                        logging.info(f"[DRY RUN] Move {filepath} -> {dest_path}")
                    else:
                        if not os.path.exists(dest_folder):
                            os.makedirs(dest_folder)
                        shutil.move(filepath, dest_path)
                        logging.info(f"Moved to {dest_path}")
                else:
                    logging.warning(f"Could not identify {file}, skipping.")

def main():
    """
    Docstring for main.
    """
    parser = argparse.ArgumentParser(description="Media Library Organizer")
    parser.add_argument("--source", required=True, help="Source directory to scan")
    parser.add_argument("--target", required=True, help="Target directory for organized library")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without moving files")

    args = parser.parse_args()

    api_key = os.environ.get("TMDB_API_KEY")
    if not api_key:
        logging.error("TMDB_API_KEY environment variable not set.")
        exit(1)

    organize_library(args.source, args.target, api_key, args.dry_run)

if __name__ == "__main__":
    main()
