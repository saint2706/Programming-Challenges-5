"""CLI for managing personal API secrets stored in an encrypted vault."""

from __future__ import annotations

import argparse
import os
import sys
from getpass import getpass
from pathlib import Path

# Support running as a script despite spaces in folder name
sys.path.append(os.path.dirname(__file__))
try:  # pragma: no cover - best effort import resolution
    from vault import VaultError, load_vault, save_vault
except ImportError:  # pragma: no cover
    from .vault import VaultError, load_vault, save_vault

DEFAULT_VAULT_PATH = Path(
    os.environ.get("API_KEY_VAULT_PATH", Path.home() / ".personal_api_keys.vault")
)


class ValidationError(ValueError):
    """Raised when user input is invalid."""


def prompt_password(prompt: str = "Master password: ") -> str:
    password = getpass(prompt)
    if not password:
        raise ValidationError("A master password is required")
    return password


def prompt_secret(prompt: str = "Secret value: ") -> str:
    secret = getpass(prompt)
    if not secret:
        raise ValidationError("Secret value cannot be empty")
    return secret


def load_secrets(path: Path, password: str) -> dict[str, str]:
    secrets = load_vault(path, password)
    return secrets


def persist_secrets(path: Path, secrets: dict[str, str], password: str) -> None:
    save_vault(path, secrets, password)


def cmd_add(args: argparse.Namespace) -> str:
    password = prompt_password()
    secret_value = prompt_secret()
    secrets = load_secrets(args.vault, password)
    secrets[args.name] = secret_value
    persist_secrets(args.vault, secrets, password)
    secrets.clear()
    return f"Stored secret for '{args.name}'."


def cmd_get(args: argparse.Namespace) -> str:
    password = prompt_password()
    secrets = load_secrets(args.vault, password)
    try:
        value = secrets[args.name]
    except KeyError as exc:
        secrets.clear()
        raise ValidationError(f"No secret found for '{args.name}'.") from exc
    message = value
    secrets.clear()
    return message


def cmd_delete(args: argparse.Namespace) -> str:
    password = prompt_password()
    secrets = load_secrets(args.vault, password)
    if args.name not in secrets:
        secrets.clear()
        raise ValidationError(f"No secret found for '{args.name}'.")
    del secrets[args.name]
    persist_secrets(args.vault, secrets, password)
    secrets.clear()
    return f"Deleted secret '{args.name}'."


def cmd_list(args: argparse.Namespace) -> str:
    password = prompt_password()
    secrets = load_secrets(args.vault, password)
    names = sorted(secrets)
    secrets.clear()
    if not names:
        return "Vault is empty."
    return "\n".join(names)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Personal API Key Vault")
    parser.add_argument(
        "--vault",
        type=Path,
        default=DEFAULT_VAULT_PATH,
        help=f"Path to the encrypted vault file (default: {DEFAULT_VAULT_PATH})",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="Add or update a secret")
    add_parser.add_argument("name", help="Label for the secret")
    add_parser.set_defaults(func=cmd_add)

    get_parser = subparsers.add_parser("get", help="Retrieve a secret")
    get_parser.add_argument("name", help="Label for the secret")
    get_parser.set_defaults(func=cmd_get)

    delete_parser = subparsers.add_parser("delete", help="Remove a secret")
    delete_parser.add_argument("name", help="Label for the secret")
    delete_parser.set_defaults(func=cmd_delete)

    list_parser = subparsers.add_parser("list", help="List stored secret names")
    list_parser.set_defaults(func=cmd_list)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        message = args.func(args)
    except ValidationError as exc:
        parser.error(str(exc))
    except VaultError as exc:
        parser.error(str(exc))
    print(message)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
