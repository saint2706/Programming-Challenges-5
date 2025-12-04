# Agent Safety & Usage Guide

This repository is designed to be friendly to both human developers and AI agents (LLMs).

## 1. Agent Roles

Agents can be used for:

- **Adding new challenges**: Generating boilerplate, implementing logic, and writing tests.
- **Optimizing code**: Refactoring for performance or readability.
- **Updating documentation**: Ensuring READMEs are up-to-date.
- **Managing benchmarks**: Running and analyzing performance tests.

## 2. Safety Rules for Agents

1. **Do NOT Overwrite User Code Without Verification**: Always check if a file exists and has content before overwriting. Use `read_file` first.
2. **Respect Existing Structure**: Do not arbitrarily move files or rename directories unless explicitly tasked to refactor.
3. **Run Tests**: After making changes, ALWAYS run the relevant tests to ensure no regressions.
4. **Update Documentation**: If you change code, update the corresponding `README.md` and docstrings.
5. **No Hallucinated Dependencies**: Do not import libraries that are not in `requirements.txt` without adding them (and verifying they exist).

## 3. Workflow for Agents

1. **Plan**: Analyze the request and the codebase.
2. **Edit**: Make changes incrementally.
3. **Verify**: Run tests/linters.
4. **Document**: Update docs.

## 4. Known Issues

- Some directories have inconsistent naming (Spaces vs CamelCase). Prefer the existing pattern in the specific category until a full refactor is authorized.
