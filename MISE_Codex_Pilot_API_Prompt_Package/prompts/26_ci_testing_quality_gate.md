# 26 — CI, Testing, and Quality Gate

## Objective

Add automated checks so code remains stable as Codex builds more modules.

## Prompt to paste into VS Code Codex

```text
Add CI and quality gate configuration.

Requirements:
1. Add GitHub Actions workflow or generic CI YAML under `.github/workflows/ci.yml`.
2. CI steps:
   - install dependencies
   - run ruff
   - run pytest
   - run coverage
   - compile Python files
3. Add coverage configuration with a realistic initial threshold.
4. Add `mypy` configuration but allow gradual adoption.
5. Add pre-commit configuration for formatting and linting.
6. Add test data fixtures under `tests/fixtures`.
7. Update README with CI status instructions.
```

## Acceptance criteria

- CI file exists.
- pytest and ruff run in CI.
- Pre-commit config exists.

## Suggested verification commands

```bash
pytest
ruff check .
python -m compileall app tests
```
