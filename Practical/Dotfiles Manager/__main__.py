"""
Dotfiles Manager

Manages symlinks from a central repository to the home directory.
"""

import os
import argparse
import logging
import shutil

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

def expand_path(path: str) -> str:
    """Expand user and vars in path."""
    return os.path.abspath(os.path.expandvars(os.path.expanduser(path)))

def install_dotfiles(source_dir: str, target_dir: str, backup: bool = True, dry_run: bool = False):
    """
    Link files from source_dir to target_dir (usually $HOME).
    Respects nested structure or mapping can be defined.
    For simplicity, we map source_dir/file -> target_dir/.file
    """
    source_dir = expand_path(source_dir)
    target_dir = expand_path(target_dir)

    if not os.path.exists(source_dir):
        logging.error(f"Source directory {source_dir} does not exist.")
        return

    logging.info(f"Installing dotfiles from {source_dir} to {target_dir}")

    for item in os.listdir(source_dir):
        if item.startswith('.git') or item == 'README.md':
            continue

        source_path = os.path.join(source_dir, item)

        # Convention: source 'vimrc' -> target '.vimrc'
        target_name = f".{item}" if not item.startswith('.') else item
        target_path = os.path.join(target_dir, target_name)

        if os.path.islink(target_path):
            # Check if it points to our source
            current_src = os.readlink(target_path)
            if current_src == source_path:
                logging.info(f"SKIP: {target_name} already linked correctly.")
                continue
            else:
                logging.info(f"UPDATE: {target_name} linked to {current_src}, relinking...")
                if not dry_run:
                    os.unlink(target_path)

        elif os.path.exists(target_path):
            if backup:
                backup_path = f"{target_path}.bak"
                logging.info(f"BACKUP: Moving {target_name} to {backup_path}")
                if not dry_run:
                    shutil.move(target_path, backup_path)
            else:
                logging.warning(f"CONFLICT: {target_name} exists. Skipping (use --backup to move it).")
                continue

        logging.info(f"LINK: {target_name} -> {source_path}")
        if not dry_run:
            try:
                os.symlink(source_path, target_path)
            except OSError as e:
                logging.error(f"Failed to link {target_name}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Dotfiles Manager")
    parser.add_argument("--source", default=".", help="Directory containing dotfiles")
    parser.add_argument("--target", default="~", help="Target directory (usually home)")
    parser.add_argument("--no-backup", action="store_true", help="Do not backup existing files")
    parser.add_argument("--dry-run", action="store_true", help="Show what would happen")

    args = parser.parse_args()

    install_dotfiles(
        args.source,
        args.target,
        backup=not args.no_backup,
        dry_run=args.dry_run
    )

if __name__ == "__main__":
    main()
