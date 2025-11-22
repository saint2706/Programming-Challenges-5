# Encrypted Notes Vault

A secure, offline application to store text notes, encrypted with symmetric encryption (Fernet/AES).

## Requirements
* Python 3+
* `cryptography` library
* `tkinter` (usually included with Python, but may need separate installation on Linux, e.g., `sudo apt install python3-tk`)

## Installation
```bash
pip install -r requirements.txt
```

## Usage
Run the application:
```bash
python "Practical/Encrypted Notes Vault/vault.py"
```

## Features
* **Create Account**: Set a master password to generate your encryption key.
* **Login**: Access your notes with your password.
* **Encryption**: Notes are stored in `vault.json` in encrypted form. The key is derived from your password using PBKDF2.
* **CRUD**: Create, Read, Update, and Delete notes.
