# Contributing to Programming-Challenges-5

Thank you for your interest in contributing! We want to make this repository a high-quality resource for programming challenges.

## 1. Code of Conduct

Be respectful and constructive. This is a learning environment.

## 2. How to Contribute

1. **Fork the repository**.
2. **Create a branch** for your feature or fix: `git checkout -b feature/my-new-challenge`.
3. **Implement your changes**.
4. **Run tests** to ensure nothing is broken.
5. **Submit a Pull Request (PR)**.

## 3. Coding Style

### Python

- Follow **PEP 8**.
- Use **Black** for formatting.
- Use **Ruff** or **Flake8** for linting.
- Add type hints (`typing`) where possible.
- Include docstrings for all functions and classes.

### Rust

- Follow standard Rust conventions.
- Use `cargo fmt` and `cargo clippy`.

### Go

- Use `go fmt` and `go vet`.

## 4. Adding a New Challenge

1. **Choose a Category**: Practical, Algorithmic, EmulationModeling, ArtificialIntelligence, or GameDevelopment.
2. **Create a Directory**: Use a descriptive name (e.g., `My New Challenge`).
3. **Add a README.md**: Follow the template in `DEVELOPER_GUIDE.md`.
4. **Implement the Solution**: Provide a clean, reference implementation.
5. **Add Tests**: Include unit tests in a `tests/` subfolder or within the challenge folder.

## 5. Commit Messages

- Use the imperative mood ("Add feature" not "Added feature").
- Reference issue numbers if applicable.
- Example: `feat: add implementation for Snake game`

## 6. Review Process

- CI checks must pass (tests, linting).
- A maintainer will review your code for clarity, correctness, and style.
