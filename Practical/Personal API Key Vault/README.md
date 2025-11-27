# Personal API Key Vault

A password-based encrypted vault for storing API keys and other secrets locally. It provides
an interactive CLI for adding, retrieving, deleting, and listing secret labels.

## Features
- Secrets encrypted with [Fernet](https://cryptography.io/en/latest/fernet/) using a key derived from a master password via PBKDF2-HMAC (SHA-256, 390k iterations).
- Salt stored alongside ciphertext so vault files remain portable across machines.
- Secure prompts using `getpass` to avoid echoing secrets or the master password.
- CLI commands for add/get/delete/list secrets with minimal time in-memory for decrypted data.

## Usage
Run the CLI with Python:

```bash
python -m Practical.PersonalAPIKeyVault add my-service
python -m Practical.PersonalAPIKeyVault get my-service
python -m Practical.PersonalAPIKeyVault delete my-service
python -m Practical.PersonalAPIKeyVault list
```

The vault location defaults to `~/.personal_api_keys.vault`. Override it with the `--vault`
flag or the `API_KEY_VAULT_PATH` environment variable.

## Rotating the master password
To rotate the master password without exposing plaintext secrets on disk:

1. Decrypt with the old password into memory using `list` (ensures the password is correct).
2. Re-encrypt using a short Python snippet that keeps secrets in-memory only:
   ```bash
   python - <<'PY'
   from getpass import getpass
   from pathlib import Path
   from Practical.PersonalAPIKeyVault.vault import load_vault, save_vault

   vault_path = Path("/path/to/vault")
   old_password = getpass("Old password: ")
   new_password = getpass("New password: ")
   secrets = load_vault(vault_path, old_password)
   save_vault(vault_path, secrets, new_password)
   secrets.clear()
   print("Re-encrypted with new password.")
   PY
   ```
3. Confirm the new password works with `list`.

Secrets are only decrypted in-memory and cleared after use, reducing exposure while refreshing the
derived encryption key.
