# Git Commit Quality Bot

A Git pre-commit hook that enforces commit message standards.

## Features
* Checks subject line length (max 50 characters).
* Checks for proper capitalization of the subject line.
* Ensures there is a blank line between subject and body (if body exists).
* Prevents "WIP" or empty commits (configurable).

## Installation

1. Copy the hook script to your repository's hooks directory:
   ```bash
   cp "Practical/Git Commit Quality Bot/commit_check.py" .git/hooks/commit-msg
   ```
   *Note: The standard hook is `commit-msg`, not `pre-commit`, for message checking.*

2. Make it executable:
   ```bash
   chmod +x .git/hooks/commit-msg
   ```

   **Alternatively**, use the included installer:
   ```bash
   python "Practical/Git Commit Quality Bot/install_hook.py" /path/to/your/repo
   ```

## Usage
Just commit as usual. If your message violates the rules, the commit will be rejected with an error message explaining why.
