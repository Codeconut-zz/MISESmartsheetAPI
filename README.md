# MISE Smartsheet Integration

Python service scaffold for the MISE Smartsheet Integration pilot.

## Setup

Requirements:

- Python 3.11 or newer
- A local virtual environment

Create and activate a virtual environment, then install the project:

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Run the local API:

```bash
uvicorn app.main:app --reload
```

Run the CLI health command:

```bash
python -m app.cli.main health
```

## Configuration

The application reads configuration from environment variables with optional local `.env` support.
Start from the checked-in placeholder file:

```bash
Copy-Item .env.example .env
```

Example development values:

```dotenv
ENVIRONMENT=development
LOG_LEVEL=INFO
SMARTSHEET_BASE_URL=https://api.smartsheet.com/2.0
SMARTSHEET_ACCESS_TOKEN=
SMARTSHEET_TIR_SHEET_ID=
DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/mise_smartsheet
MISE_PROJECT_ROOT=
MISE_REGISTRY_ROOT=
REPORT_EXPORT_ROOT=data/reports
ENABLE_WRITE_OPERATIONS=false
REQUIRE_APPLY_FLAG=true
```

Production mode validates that Smartsheet access, the TIR sheet ID, database URL, and MISE
filesystem roots are present. Write operations remain disabled unless explicitly enabled and guarded
by the apply flag.

## Verification

```bash
pytest
ruff check .
python -m compileall app tests
```

## Safety Notes

- Do not commit Smartsheet API tokens, `.env` files, credentials, or production paths.
- Copy `.env.example` to a local `.env` only on your workstation or deployment host, then fill it with real values there.
- Keep real Smartsheet tokens, database passwords, email addresses, sheet IDs, and filesystem roots out of commits, logs, screenshots, and tickets.
- Generated exports, generated reports, logs, caches, virtual environments, and local database files are ignored by Git.
- This scaffold intentionally contains no Smartsheet credentials or production filesystem locations.
