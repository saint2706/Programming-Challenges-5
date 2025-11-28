# Agent Instructions for Programming-Challenges-5

This file provides instructions for AI agents working on this repository.

## Quick Start

Before making changes, ensure you can build and test the code:

```bash
# Python
python -m pip install -r requirements.txt
python -m pytest tests/

# JavaScript
npm install
npm run test

# Go (from module directory)
go test ./...

# Rust (from crate directory)
cargo test
```

## Repository Overview

This repository contains programming challenges in five categories:

| Category                | Path                      | Languages                    |
| ----------------------- | ------------------------- | ---------------------------- |
| Practical               | `Practical/`              | Python, JavaScript           |
| Algorithmic             | `Algorithmic/`            | Python, Rust, Go, JavaScript |
| Emulation/Modeling      | `EmulationModeling/`      | Python, C++                  |
| Game Development        | `GameDevelopment/`        | Python (pygame)              |
| Artificial Intelligence | `ArtificialIntelligence/` | Python                       |

JavaScript is used for web-based implementations (e.g., DP Visualizer) and Vitest testing.

## Making Changes

### Adding New Challenges

1. Create a new directory under the appropriate category
2. Include a `README.md` explaining the challenge
3. For Python: include `__init__.py` for package structure
4. Add tests in `tests/test_<module_name>.py`

### Code Style Requirements

**Python:**

- Type hints on all functions
- Google-style docstrings
- PEP 8 compliance
- `from __future__ import annotations` for forward references

**Rust:**

- Use `Result`/`Option` for error handling
- Run `cargo clippy` and `cargo fmt`
- Include tests in `#[cfg(test)]` module

**Go:**

- Use `gofmt` for formatting
- Handle all errors explicitly
- Tests in `*_test.go` files

**C++:**

- C++17 or later
- Use smart pointers
- `#pragma once` for header guards

**JavaScript:**

- Use Vitest for testing
- Follow npm scripts for build commands

## CI Workflows

The repository has four CI workflows:

- `python-tests.yml` - Runs on Python 3.10 and 3.11
- `node-tests.yml` - Runs Vitest
- `go-tests.yml` - Runs `go test` for each module
- `rust-tests.yml` - Runs `cargo test` for each crate

Always verify your changes pass CI before submitting.

## Testing Guidelines

- Write tests for all new functionality
- Place Python tests in `tests/` directory
- Use descriptive test names that explain what is being tested
- Test edge cases and error conditions

## Common Pitfalls

- **Dependencies**: Check `requirements.txt` for Python, `package.json` for Node.js
- **Module imports**: Use relative imports within packages
- **File paths**: Use `pathlib` for cross-platform compatibility in Python
- **Database**: SQLite is preferred for persistence; use SQLAlchemy for ORM

## Security

- Never commit secrets or API keys
- Use environment variables for sensitive configuration
- Validate all user inputs
- Use parameterized database queries
