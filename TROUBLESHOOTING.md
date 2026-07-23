# Troubleshooting

Common problems and their fixes when setting up, running, or testing this
repository. If your issue isn't covered here, check the
[Developer Guide](DEVELOPER_GUIDE.md).

## Installation & Environment

### `pip install -r requirements.txt` fails or is very slow

The requirements include heavy packages (e.g. `torch`, `torchvision`). If you
only need a subset of challenges, install the specific packages a challenge's
`README.md` lists instead of the full file. Always work inside a virtual
environment:

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

### Wrong Python version

The project targets **Python 3.10+** and CI tests on **3.10 and 3.11**. Check
your version with `python --version`. Note that some newer standard-library
names (such as `datetime.UTC`) only exist on 3.11+, so prefer 3.10-compatible
equivalents (`datetime.timezone.utc`) in code that runs under the test suite.

## Running Tests

### `ModuleNotFoundError` when running a test

The test suite relies on `tests/conftest.py`, which registers import aliases for
directories whose names contain spaces or special characters. Run tests from the
repository root so this configuration is picked up:

```bash
python -m pytest tests/
```

### AI/ML tests fail or take too long

Tests that require `torch`/`torchvision` (and other large ML dependencies) are
heavier than the core suite. If they are not relevant to your change, run a
targeted subset instead of the whole suite:

```bash
python -m pytest tests/test_randomized_structures.py
```

### A single test file errors during collection

If one module fails to import, pytest reports a collection error for that file.
Read the traceback: it usually points to a missing dependency or a
version-specific API. Fix the import (or install the dependency) rather than
disabling the whole suite.

## Game & GUI Challenges

### `pygame` window doesn't open / no display available

Many `GameDevelopment` challenges use `pygame`, which needs a display. On a
headless machine (CI, remote server) set a dummy video driver:

```bash
SDL_VIDEODRIVER=dummy python main.py
```

Where possible, the challenges keep their core logic (physics, rules, state) in
modules that do **not** import `pygame`, so that logic can be tested without a
display. Prefer running those logic tests headlessly.

### `pygame`/`PyQt6` not installed

These are not required by the default `tests/` suite and may not be installed.
Install them only for the specific challenge you are running:

```bash
pip install pygame      # or: pip install PyQt6
```

## Formatting & Linting

### CI `lint` job fails but the code looks fine

CI enforces **Black**, **isort** (`--profile black`), and **Ruff**. Reproduce
locally before pushing:

```bash
black --check .
isort --check-only --profile black .
ruff check .
```

Run without `--check` (and `ruff check --fix`) to auto-apply fixes. A common
gotcha: isort treats sibling modules imported by name as third-party, so an
extra blank line between them and other third-party imports will fail the check.

### CI `link-check` (Docs CI) fails

The docs workflow validates every Markdown link with `lychee`. A failure means a
link points to a file, path, or anchor that does not exist. Fix the link target
(create the file, correct the path/case, or remove the dead link). Directory
names are case- and space-sensitive.

## Git & Contributions

### My pull request has failing checks

All CI checks (tests, lint, docs) must pass before review. Open the failing
job's logs from the PR's **Checks** tab, reproduce the failure locally with the
commands above, fix it, and push again. See [CONTRIBUTING.md](CONTRIBUTING.md)
for the full review process.
