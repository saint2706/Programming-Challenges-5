"""Git commit message validator.

This module validates commit messages against common best practices:
- Subject line <= 50 characters
- Subject starts with a capital letter
- Subject does not end with a period
- Blank line between subject and body (if body exists)

Usage:
    python commit_check.py <commit_message_file>
"""
import sys
import re


def validate_commit_message(message_file):
    """Validate a commit message file against best practices.

    Args:
        message_file: Path to file containing the commit message.

    Raises:
        SystemExit: With code 1 if validation fails, 0 if valid.
    """
    with open(message_file, 'r') as f:
        lines = f.readlines()

    if not lines:
        print("Error: Empty commit message.")
        sys.exit(1)

    subject = lines[0].strip()
    
    # Rule 1: Subject line <= 50 chars
    if len(subject) > 50:
        print(f"Error: Subject line is too long ({len(subject)} > 50 characters).")
        sys.exit(1)

    # Rule 2: Subject line starts with Capital letter
    if not subject[0].isupper():
        print("Error: Subject line must start with a capital letter.")
        sys.exit(1)

    # Rule 3: No trailing period in subject
    if subject.endswith('.'):
        print("Error: Subject line must not end with a period.")
        sys.exit(1)

    # Rule 4: Blank line between subject and body
    if len(lines) > 1 and lines[1].strip() != "":
        print("Error: There must be a blank line between the subject and the body.")
        sys.exit(1)

    print("Commit message is valid.")
    sys.exit(0)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python commit_check.py <commit_message_file>")
        sys.exit(1)
    
    validate_commit_message(sys.argv[1])
