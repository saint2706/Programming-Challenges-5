# Password Data Breach Checker

Securely checks if your password has appeared in a data breach using the [Have I Been Pwned](https://haveibeenpwned.com/) API.

## Security (k-Anonymity)
This tool **never** sends your password to the server.
1. It hashes your password using SHA-1.
2. It sends only the **first 5 characters** of the hash to the API.
3. The API returns a list of all breached hash suffixes that match those 5 characters.
4. The tool checks locally if your full hash matches any in the list.

## Requirements
* Python 3.8+
* `requests`

## Installation
```bash
pip install -r requirements.txt
```

## Usage
**Argument Mode (Visible in history - use with caution):**
```bash
python -m Practical.PasswordDataBreachChecker "mypassword123"
```

**Interactive Mode (Hidden input - Recommended):**
```bash
python -m Practical.PasswordDataBreachChecker
```
