from pathlib import Path

import pytest
from Practical.PersonalAPIKeyVault.__main__ import main
from Practical.PersonalAPIKeyVault.vault import (
    VaultError,
    decrypt_secrets,
    encrypt_secrets,
)


def test_encrypt_decrypt_roundtrip():
    secrets = {"service": "token-123"}
    salt, ciphertext = encrypt_secrets(secrets, "correct horse")
    recovered = decrypt_secrets(salt, ciphertext, "correct horse")
    assert recovered == secrets


def test_decrypt_with_wrong_password():
    secrets = {"service": "token-123"}
    salt, ciphertext = encrypt_secrets(secrets, "password-one")
    with pytest.raises(VaultError):
        decrypt_secrets(salt, ciphertext, "password-two")


def run_cli(
    tmp_path: Path,
    capsys,
    monkeypatch,
    *args,
    password="master-pass",
    secret="secret-value",
):
    prompts = [password]
    if secret is not None:
        prompts.append(secret)

    def fake_getpass(prompt: str):
        return prompts.pop(0)

    monkeypatch.setattr("Practical.PersonalAPIKeyVault.__main__.getpass", fake_getpass)

    argv = ["--vault", str(tmp_path / "vault.json"), *args]
    result = main(argv)
    captured = capsys.readouterr()
    return result, captured.out.strip()


def test_cli_add_get_delete(tmp_path, capsys, monkeypatch):
    code, out = run_cli(tmp_path, capsys, monkeypatch, "add", "service-a")
    assert code == 0
    assert "Stored secret" in out

    code, out = run_cli(tmp_path, capsys, monkeypatch, "get", "service-a", secret=None)
    assert code == 0
    assert out == "secret-value"

    code, out = run_cli(tmp_path, capsys, monkeypatch, "list", secret=None)
    assert code == 0
    assert "service-a" in out

    code, out = run_cli(
        tmp_path, capsys, monkeypatch, "delete", "service-a", secret=None
    )
    assert code == 0
    assert "Deleted secret" in out

    code, out = run_cli(tmp_path, capsys, monkeypatch, "list", secret=None)
    assert code == 0
    assert out == "Vault is empty."
