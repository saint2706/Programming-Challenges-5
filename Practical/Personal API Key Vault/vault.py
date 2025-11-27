"""Core encryption helpers for the Personal API Key Vault."""
from __future__ import annotations

import base64
import binascii
import json
import os
from pathlib import Path
from typing import Dict

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

DEFAULT_ITERATIONS = 390_000
SALT_BYTES = 16


class VaultError(Exception):
    """Raised when vault operations fail."""


def derive_key(password: str, salt: bytes, iterations: int = DEFAULT_ITERATIONS) -> bytes:
    """Derive a Fernet key from the provided password and salt."""
    if not password:
        raise ValueError("Master password cannot be empty")

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=iterations,
    )
    key = kdf.derive(password.encode("utf-8"))
    return base64.urlsafe_b64encode(key)


def encrypt_secrets(secrets: Dict[str, str], password: str) -> tuple[bytes, bytes]:
    """Encrypt a secrets dictionary.

    Returns the salt and ciphertext. Salt must be stored alongside the
    ciphertext to allow password-based key derivation during decryption.
    """

    salt = os.urandom(SALT_BYTES)
    key = derive_key(password, salt)
    fernet = Fernet(key)
    plaintext = json.dumps(secrets).encode("utf-8")
    ciphertext = fernet.encrypt(plaintext)
    return salt, ciphertext


def decrypt_secrets(salt: bytes, ciphertext: bytes, password: str) -> Dict[str, str]:
    """Decrypt secrets using the provided password and salt."""
    key = derive_key(password, salt)
    fernet = Fernet(key)
    try:
        plaintext = fernet.decrypt(ciphertext)
    except InvalidToken as exc:  # pragma: no cover - specific failure path
        raise VaultError("Unable to decrypt vault: invalid password or corrupted data") from exc
    data = json.loads(plaintext.decode("utf-8"))
    if not isinstance(data, dict):
        raise VaultError("Vault content is malformed")
    return data


def load_vault(path: Path, password: str) -> Dict[str, str]:
    """Load and decrypt the vault content.

    Returns an empty dict when the file does not exist.
    """
    if not path.exists():
        return {}

    try:
        payload = json.loads(path.read_text())
        salt_b64 = payload["salt"]
        ciphertext_b64 = payload["ciphertext"]
    except (OSError, KeyError, json.JSONDecodeError) as exc:
        raise VaultError("Vault file is unreadable or malformed") from exc

    try:
        salt = base64.b64decode(salt_b64)
        ciphertext = base64.b64decode(ciphertext_b64)
    except (binascii.Error, TypeError) as exc:
        raise VaultError("Vault file contains invalid encoding") from exc
    return decrypt_secrets(salt, ciphertext, password)


def save_vault(path: Path, secrets: Dict[str, str], password: str) -> None:
    """Encrypt and persist the secrets."""
    salt, ciphertext = encrypt_secrets(secrets, password)
    payload = {
        "salt": base64.b64encode(salt).decode("utf-8"),
        "ciphertext": base64.b64encode(ciphertext).decode("utf-8"),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2))
