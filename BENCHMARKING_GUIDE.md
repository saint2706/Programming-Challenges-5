# Benchmarking Guide

Several challenges in this repository include performance-sensitive code
(algorithms, data structures, simulations). This guide explains how to run and
add benchmarks.

For general setup and testing, see the [Developer Guide](DEVELOPER_GUIDE.md).

## 1. Tooling

Python benchmarks use [`pytest-benchmark`](https://pytest-benchmark.readthedocs.io/),
which integrates with the existing `pytest` suite. Install it into your
environment:

```bash
pip install -r requirements.txt
pip install pytest-benchmark
```

## 2. Running Benchmarks

Benchmarks live under `tests/benchmarks/` (or are marked with the
`@pytest.mark.benchmark` marker). To run only the benchmarks:

```bash
pytest tests/benchmarks/ --benchmark-only
```

To save the results to a JSON file (as the CI workflow does):

```bash
pytest tests/benchmarks/ --benchmark-only --benchmark-json=benchmark_results.json
```

To run the normal test suite **without** benchmarks, just run `pytest` as usual —
benchmark-only options are opt-in.

### Comparing runs

`pytest-benchmark` can store and compare runs so you can see whether a change
made things faster or slower:

```bash
pytest tests/benchmarks/ --benchmark-only --benchmark-autosave
pytest tests/benchmarks/ --benchmark-only --benchmark-compare
```

## 3. Continuous Integration

A scheduled GitHub Actions workflow (`.github/workflows/benchmarks.yml`) runs
weekly and on manual dispatch. It installs `pytest-benchmark` and runs the
benchmarks if a `tests/benchmarks/` directory is present; otherwise it reports
that no benchmarks were found. This means adding a benchmark under
`tests/benchmarks/` is enough to have it picked up automatically.

## 4. Writing a Benchmark

`pytest-benchmark` provides a `benchmark` fixture. Pass it the callable you want
to measure:

```python
def test_sort_performance(benchmark):
    data = list(range(10_000, 0, -1))
    result = benchmark(sorted, data)
    assert result[0] == 1
```

For code that needs setup that should not be timed, use `benchmark.pedantic`:

```python
def test_query_performance(benchmark):
    structure = build_large_structure()
    benchmark.pedantic(structure.query, args=(42,), rounds=100, iterations=10)
```

## 5. Tips

- Benchmark realistic input sizes; micro-inputs are dominated by overhead.
- Keep setup work out of the timed section (build fixtures beforehand).
- Record notable performance learnings so future work does not regress them.
- Prefer in-place operations and cache-friendly data layouts for hot paths.
