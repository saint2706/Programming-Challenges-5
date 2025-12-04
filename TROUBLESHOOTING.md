# Troubleshooting Guide

## 1. Common Issues

### Python Virtual Environment

**Issue**: `ModuleNotFoundError`
**Fix**: Ensure your virtual environment is activated.

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### Import Errors

**Issue**: `ImportError: attempted relative import with no known parent package`
**Fix**: Run the script as a module from the root directory, or ensure `PYTHONPATH` includes the root.

```bash
export PYTHONPATH=$PYTHONPATH:.
python Path/To/Script.py
```

### Rust/Go Toolchains

**Issue**: Compiler errors or missing tools.
**Fix**: Ensure you have the latest stable version.

```bash
rustup update
go version
```

## 2. Reporting Bugs

If you find a bug in a challenge implementation:

1. Check the `Issues` tab on GitHub.
2. Open a new issue with a reproduction script.
3. Tag it with the relevant category (e.g., `bug`, `algorithmic`).
