# Benchmarking Guide

## 1. How to Run Benchmarks

We use a standardized approach for benchmarking algorithmic solutions.

### Python

Use the `pytest-benchmark` plugin or the built-in `timeit` module.

```bash
pytest tests/benchmarks/ --benchmark-only
```

### Rust

Use `criterion`.

```bash
cargo bench
```

### Go

Use the built-in testing package.

```bash
go test -bench=.
```

## 2. Comparing Algorithms

When optimizing an algorithm (e.g., O(n^2) to O(n log n)):

1. Implement both versions.
2. Create a benchmark script that runs both on the same large inputs.
3. Record the execution time and memory usage.
4. Include the results in the challenge's `README.md`.

## 3. Generating Reports

You can generate a JSON report of benchmarks:

```bash
pytest --benchmark-json=output.json
```
