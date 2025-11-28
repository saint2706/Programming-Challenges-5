"""
Password Data Breach Checker

Checks if a password has been exposed in data breaches using the
Have I Been Pwned (HIBP) k-Anonymity API.
"""

import argparse
import getpass
import hashlib
import sys

import requests

HIBP_API_URL = "https://api.pwnedpasswords.com/range/"


def check_password(password: str) -> int:
    """
    Check a password against HIBP API.
    Returns the number of times the password has been exposed.
    """
    # 1. Hash the password using SHA-1
    sha1_password = hashlib.sha1(password.encode("utf-8")).hexdigest().upper()

    # 2. Split hash into prefix (first 5 chars) and suffix
    prefix = sha1_password[:5]
    suffix = sha1_password[5:]

    # 3. Query API with prefix
    try:
        response = requests.get(f"{HIBP_API_URL}{prefix}")
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error connecting to API: {e}")
        return -1

    # 4. Check if suffix exists in response
    # Response format: SUFFIX:COUNT (one per line)
    hashes = (line.split(":") for line in response.text.splitlines())
    for h, count in hashes:
        if h == suffix:
            return int(count)

    return 0


def main():
    parser = argparse.ArgumentParser(description="Password Data Breach Checker")
    parser.add_argument(
        "password", nargs="?", help="Password to check (leave empty for secure input)"
    )

    args = parser.parse_args()

    password = args.password
    if not password:
        try:
            password = getpass.getpass("Enter password to check: ")
        except KeyboardInterrupt:
            sys.exit(0)

    if not password:
        print("No password provided.")
        sys.exit(1)

    count = check_password(password)

    if count > 0:
        print(
            f"\n❌ DANGER: This password has been seen {count:,} times in data breaches."
        )
        print("You should change it immediately!")
    elif count == 0:
        print("\n✅ Good news! This password was not found in any known breaches.")
    else:
        print("\nCould not verify password due to API error.")


if __name__ == "__main__":
    main()
