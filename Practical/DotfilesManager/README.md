# Dotfiles Manager

A tool to manage your configuration files by symlinking them from a central repository to your home directory.

## Installation
```bash
# No dependencies required, just Python standard library
```

## Usage
Store your config files in a directory (e.g., `~/dotfiles`).
The tool assumes files in the source directory should be prefixed with a dot `.` in the target directory.

Example:
* `~/dotfiles/vimrc` -> `~/.vimrc`
* `~/dotfiles/zshrc` -> `~/.zshrc`

```bash
python -m Practical.DotfilesManager --source ~/dotfiles --target ~
```

## Options
* `--dry-run`: See what changes would be made without applying them.
* `--no-backup`: Do not backup existing files (will skip if conflict exists). By default, it moves existing files to `.bak`.
