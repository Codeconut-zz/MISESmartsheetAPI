# AGENTS.md — MISE Smartsheet Integration Service

## Mission
Build the MISE-hosted pilot API and integration service for Smartsheet data extraction, project-folder reconciliation, reporting, and controlled future automation.

## Non-negotiable rules

- Never hard-code API tokens, passwords, private keys, server credentials, or production folder paths.
- Use `.env` locally and `.env.example` in source control.
- Never commit `.env`, database files, exported reports with personal data, or logs containing tokens.
- All production-changing actions must require both dry-run review and an explicit `--apply` flag.
- Folder deletion, Smartsheet sheet deletion, row deletion, and permission removal are prohibited in v1.
- Read-only operations must be the default mode.
- Write operations must log an audit record before and after execution.
- Every prompt must update tests where relevant.
- Every prompt must leave the repository in a runnable state.
- Prefer small, reviewable commits.

## Application stack

- Python 3.11+
- FastAPI
- Typer CLI
- Pydantic v2
- SQLAlchemy 2.x
- Alembic
- PostgreSQL
- httpx
- pandas / openpyxl
- pytest
- Docker / Docker Compose

## Repository name

`mise-smartsheet-integration`

## Core commands expected by the end of the build

```bash
mise-smartsheet health
mise-smartsheet smartsheet whoami
mise-smartsheet smartsheet inventory --out data/exports/smartsheet_inventory.json
mise-smartsheet tir pull --sheet-id $SMARTSHEET_TIR_SHEET_ID --out data/exports/tir_rows.json
mise-smartsheet filesystem scan --root "$MISE_PROJECT_ROOT" --out data/exports/folder_inventory.json
mise-smartsheet reconcile --tir data/exports/tir_rows.json --folders data/exports/folder_inventory.json --out data/reports/reconciliation.xlsx
mise-smartsheet plan config/architecture/mise_ministry_blueprint.example.yaml
mise-smartsheet apply config/architecture/mise_ministry_blueprint.example.yaml --apply
uvicorn app.main:app --reload
pytest
```

## Domain context

The MISE hierarchy includes Minister, Secretary, Director General Engineering Services, Corporate Services, ABED, CED, EPD, and WSED. ABED contains four divisions: Architectural Design Division, Cost Planning Division, Quality Control & Inspection Division, and Building Maintenance Division.

The initial workflow is the Technical Intake Request process. A client submits a Smartsheet form, the request enters the Registry Database, the Secretary approves, pends, or declines the request, and the Registry/officers/client receive the correct downstream information.

## Data-handling posture

Treat project data, contact names, phone numbers, email addresses, file references, project background, funding source, and development partner data as sensitive operational data. Minimize outputs and apply clear logging boundaries.
