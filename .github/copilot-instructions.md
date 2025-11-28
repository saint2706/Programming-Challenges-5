# Copilot Instructions for Programming-Challenges-5

This repository contains programming challenges across five categories: Practical, Algorithmic, Emulation/Modeling, Artificial Intelligence, and Game Development.

## Repository Structure

- `Practical/` - Python implementations of practical utility applications
- `Algorithmic/` - Algorithm implementations in Python, Rust, and Go
- `EmulationModeling/` - Emulators and simulations in Python and C++
- `GameDevelopment/` - Game implementations in Python using pygame
- `ArtificialIntelligence/` - AI and ML implementations in Python
- `tests/` - Test files for the implementations

## Languages Used

- **Python** - Primary language for Practical, Game Development, and some Algorithmic/Emulation challenges
- **Rust** - Used for performance-critical Algorithmic challenges
- **Go** - Used for some Algorithmic challenges
- **C++** - Used for Emulation/Modeling challenges
- **JavaScript** - Used for web-based implementations (e.g., DP Visualizer) and testing (Vitest)

## Code Style and Conventions

### Python

- Use type hints for function parameters and return types
- Include docstrings for modules, classes, and functions following Google-style format
- Use `from __future__ import annotations` for forward references
- Organize imports: standard library, third-party, local imports
- Follow PEP 8 style guidelines

### Documentation

- Each challenge directory should contain a `README.md` explaining the challenge
- Include implementation notes and usage examples in documentation
- Document algorithm complexity where applicable

### Testing

- Tests are located in the `tests/` directory
- Use pytest for Python tests
- Use Vitest for JavaScript tests (run with `npm run test`)
- Test files should be named `test_<module_name>.py`

## Building and Testing

```bash
# Install JavaScript dependencies
npm install

# Run JavaScript tests
npm run test

# Run Python tests (from project root)
python -m pytest tests/
```

## Challenge Implementation Guidelines

1. Create a dedicated directory for each challenge within the appropriate category
2. Include an `__init__.py` for Python packages
3. Separate concerns: business logic, storage/persistence, and CLI/UI
4. Provide clear error handling with informative messages
5. Use dependency injection for testability (e.g., time functions, storage backends)

## Additional Language Conventions

### Rust

- Use idiomatic Rust patterns (Result/Option for error handling, iterators over manual loops)
- Follow Rust naming conventions (snake_case for functions/variables, CamelCase for types)
- Include `Cargo.toml` with appropriate dependencies and metadata
- Write unit tests using `#[cfg(test)]` module pattern
- Use `clippy` lints and format with `rustfmt`

### Go

- Follow standard Go project layout conventions
- Use `go.mod` for dependency management
- Write tests in `*_test.go` files
- Use `gofmt` for formatting
- Handle errors explicitly rather than ignoring them
- Use meaningful package names (avoid generic names like `util`)

### C++

- Use modern C++ features (C++17 or later when possible)
- Include header guards or `#pragma once`
- Use smart pointers over raw pointers for memory management
- Prefer `const` correctness
- Include CMakeLists.txt or Makefile for build configuration

## CI/CD and Local Testing

This repository uses GitHub Actions for continuous integration with separate workflows for each language:

- **Python** (`python-tests.yml`): Runs pytest on Python 3.10 and 3.11
- **Node.js** (`node-tests.yml`): Runs Vitest for JavaScript tests
- **Go** (`go-tests.yml`): Runs `go test` for each Go module
- **Rust** (`rust-tests.yml`): Runs `cargo test` for each Rust crate

### Running Tests Locally

```bash
# Python tests
python -m pip install -r requirements.txt
python -m pytest tests/

# JavaScript tests
npm install
npm run test

# Go tests (from module directory)
go test ./...

# Rust tests (from crate directory)
cargo test
```

## Error Handling Patterns

- Use specific exception types rather than generic exceptions
- Include context in error messages (what failed, why, and how to fix)
- Log errors appropriately before re-raising or returning
- For API endpoints, return structured error responses with appropriate HTTP status codes

## Security Considerations

- Never commit secrets, API keys, or credentials to the repository
- Use environment variables for sensitive configuration
- Validate and sanitize user inputs
- Use parameterized queries for database operations
- Keep dependencies updated to patch security vulnerabilities

## Preferred Libraries

### Python

- Web frameworks: FastAPI, Flask
- Data processing: pandas, numpy
- Testing: pytest
- Database: SQLAlchemy, SQLite
- Cryptography: cryptography (Fernet)
- Image processing: Pillow, imagehash

### JavaScript

- Testing: Vitest
- Build tools: npm scripts

### Rust

- Error handling: thiserror, anyhow
- Serialization: serde
- CLI: clap

### Go

- Testing: built-in testing package
- HTTP: net/http (standard library)
