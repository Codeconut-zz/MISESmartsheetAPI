# 01 — Repository Scaffold

## Objective

Create the baseline Python project structure for the MISE Smartsheet Integration Service.

## Prompt to paste into VS Code Codex

```text
You are working in a new private repository named `mise-smartsheet-integration`.

Create the full repository scaffold for a Python 3.11+ application called `mise-smartsheet-integration`.

Requirements:
1. Create a clean `src` layout with the package name `app`.
2. Add directories:
   - `app/api`
   - `app/cli`
   - `app/connectors`
   - `app/domain`
   - `app/services`
   - `app/storage`
   - `app/utils`
   - `tests`
   - `config/architecture`
   - `config/mappings`
   - `data/exports`
   - `data/reports`
   - `scripts`
3. Create `pyproject.toml` using Python 3.11+.
4. Add dependencies: fastapi, uvicorn, typer, pydantic, pydantic-settings, httpx, sqlalchemy, alembic, psycopg2-binary, pandas, openpyxl, python-dotenv, tenacity, structlog, pytest, pytest-cov, respx, ruff, mypy.
5. Add `README.md` with setup and safety notes.
6. Add `.gitignore` that excludes `.env`, `data/exports/*`, `data/reports/*`, logs, `.venv`, caches, and local database files.
7. Add `app/main.py` with a FastAPI health endpoint at `/health`.
8. Add `app/cli/main.py` with a Typer command called `health`.
9. Add simple tests for the health endpoint and CLI import.
10. Do not add any Smartsheet credentials or production paths.

Return the files changed and the commands to run locally.
```

## Acceptance criteria

- Repository has the required directories.
- FastAPI app imports without error.
- Typer CLI imports without error.
- No secrets are present.

## Suggested verification commands

```bash
pytest
ruff check .
python -m compileall app tests
```
