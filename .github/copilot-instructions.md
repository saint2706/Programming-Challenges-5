# Copilot Instructions for Programming-Challenges-5

This repository contains programming challenges across five categories: Practical, Algorithmic, Emulation/Modeling, Artificial Intelligence, and Game Development. Currently, four categories have implementations.

## Repository Structure

- `Practical/` - Python implementations of practical utility applications
- `Algorithmic/` - Algorithm implementations in Python, Rust, and Go
- `EmulationModeling/` - Emulators and simulations in Python and C++
- `GameDevelopment/` - Game implementations in Python using pygame
- `tests/` - Test files for the implementations

Note: Artificial Intelligence challenges are planned but not yet implemented.

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
