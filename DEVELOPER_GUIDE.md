# Developer Guide

Welcome to the **Programming-Challenges-5** repository! This guide is designed to help you navigate the codebase, run challenges, and contribute effectively.

## 1. Project Structure

The repository is organized into five main categories, each containing specific challenges:

- **`Practical/`**: Real-world applications and tools (e.g., CLI tools, automation scripts).
- **`Algorithmic/`**: Implementations of algorithms and data structures.
- **`EmulationModeling/`**: Simulations of systems, physics, and emulators.
- **`ArtificialIntelligence/`**: AI models, machine learning, and search algorithms.
- **`GameDevelopment/`**: Game prototypes and engines.

Additionally:

- **`tests/`**: Global test suite.
- **`.github/`**: CI/CD workflows and GitHub-specific configurations.
- **`simulation_core/`**: (If present) Shared utilities for simulation challenges.

## 2. Setting Up Your Environment

### Prerequisites

- **Python 3.10+**
- **Rust** (optional, for Rust implementations)
- **Go** (optional, for Go implementations)
- **Node.js** (optional, for JS/Web implementations)

### Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/saint2706/Programming-Challenges-5.git
   cd Programming-Challenges-5
   ```

2. **Create a Python virtual environment:**

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

## 3. Running Challenges

Most challenges are self-contained. Navigate to the challenge directory and run the main script.

**Example (Python):**

```bash
cd Practical/Personal\ Time\ Tracker
python time_tracker.py
```

**Example (Rust):**

```bash
cd Algorithmic/HyperLogLog\ Implementation
cargo run
```

Refer to the `README.md` within each challenge folder for specific instructions.

## 4. Running Tests

We use `pytest` for Python tests. The test configuration is in `pyproject.toml`.

- **Run all tests:**

  ```bash
  python -m pytest
  ```

- **Run tests with verbose output:**

  ```bash
  python -m pytest -v
  ```

- **Run tests for a specific module:**

  ```bash
  python -m pytest tests/test_randomized_structures.py
  ```

- **Run EmulationModeling tests:**

  ```bash
  python -m pytest tests/EmulationModeling/
  ```

- **Run tests including dependency-heavy AI tests** (requires torch, torchvision):

  ```bash
  python -m pytest --ignore-glob="" tests/
  ```

### Test Categories

- **Core tests** (~90 tests): Run by default, covering Practical, Algorithmic, and EmulationModeling challenges.
- **AI/ML tests** (6 tests): Skipped by default due to heavy dependencies (PyTorch, TensorFlow). Enable by removing `--ignore` flags from `pyproject.toml`.
- **Platform-specific tests**: Some tests (e.g., symlink tests) are skipped on Windows.

## 5. Running Benchmarks

See [BENCHMARKING_GUIDE.md](BENCHMARKING_GUIDE.md) for detailed instructions on running performance benchmarks.

## 6. Contributing

We welcome contributions! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on coding style, commit messages, and the review process.

## 7. Using Agents

If you are using AI agents (like Jules, Copilot, etc.) to work on this repo, please refer to [AGENTS.md](AGENTS.md) for safety rules and best practices.
