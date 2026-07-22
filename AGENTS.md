# Agent Safety & Best Practices

This repository is designed to be worked on by both humans and AI coding agents
(Jules, Claude, Copilot, and similar). This document collects the rules and
conventions an agent should follow to make changes that are safe, reviewable,
and consistent with the rest of the project.

If you are a human contributor, see [CONTRIBUTING.md](CONTRIBUTING.md) and the
[Developer Guide](DEVELOPER_GUIDE.md) instead — this file only adds
agent-specific guidance on top of those.

## 1. Scope & Intent

- **Stay within the requested task.** Implement what was asked and avoid
  sweeping, unrelated refactors in the same change.
- **Prefer self-contained challenges.** Each challenge lives in its own
  directory and should not reach into unrelated challenges. Shared helpers live
  in dedicated locations (e.g. `EmulationModeling/simulation_core`).
- **Do not fabricate results.** If tests fail, a step is skipped, or something
  cannot be verified, say so explicitly rather than claiming success.

## 2. Repository Layout

The project is split into categories, each documented in the
[Developer Guide](DEVELOPER_GUIDE.md):

- `Practical/`, `Algorithmic/`, `EmulationModeling/`,
  `ArtificialIntelligence/`, `GameDevelopment/`, `WebDevelopment/`
- `tests/` — the global Python test suite (this is what CI runs).
- `.github/workflows/` — CI pipelines (see below).

## 3. Coding Conventions

- **Python**: PEP 8, formatted with **Black**, imports sorted with **isort**
  (`--profile black`), linted with **Ruff**. Add type hints and docstrings.
- **Rust**: `cargo fmt` + `cargo clippy`.
- **Go**: `go fmt` + `go vet`.
- Match the style, naming, and structure of the surrounding code in the
  directory you are editing.

## 4. Before You Open a Pull Request

Run the same checks CI runs so you don't push red builds:

```bash
# Formatting & linting (Python)
black --check .
isort --check-only --profile black .
ruff check .

# Tests
python -m pytest tests/
```

Notes:

- CI runs the Python test suite on **Python 3.10 and 3.11**. Code that must run
  under the test suite should stay compatible with 3.10 (for example, use
  `datetime.timezone.utc` rather than the 3.11-only `datetime.UTC`).
- Markdown links are validated by a link checker. Any file or anchor you link
  to must exist. Do not add links to files that have not been created.
- Many game and GUI challenges depend on `pygame`, `PyQt6`, or similar. These
  are not exercised by the default `tests/` suite; keep such code importable
  without a display where feasible so its logic can be unit-tested headlessly.

## 5. Commit & PR Hygiene

- Use imperative commit messages ("Add …", "Fix …") as described in
  [CONTRIBUTING.md](CONTRIBUTING.md).
- Keep pull requests focused and describe what changed and how it was verified.
- Ensure all CI checks pass before requesting review.

## 6. Things To Avoid

- Committing secrets, tokens, or credentials.
- Adding large binary blobs unless they are a genuine, necessary asset.
- Introducing new heavy dependencies without updating `requirements.txt` and
  explaining why.
- Deleting or rewriting other contributors' work that is unrelated to your task.

If in doubt, prefer the smaller, more conservative change and surface open
questions in the pull request description.
