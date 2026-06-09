# MISE Smartsheet Pilot API Operations Runbook

## System Purpose

The MISE Smartsheet Integration pilot provides read APIs, CLI workflows, reconciliation reports,
dry-run plans, and guarded apply operations for Technical Intake Request records, MISE project
folders, and management reporting.

## Environment Variables

Copy `.env.example` to `.env` on the host and set local values there.

Required production values:

```dotenv
ENVIRONMENT=production
SMARTSHEET_ACCESS_TOKEN=<set-on-host>
SMARTSHEET_TIR_SHEET_ID=<set-on-host>
DATABASE_URL=postgresql+psycopg2://<user>:<password>@<host>:5432/<db>
MISE_PROJECT_ROOT=<approved-project-root>
MISE_REGISTRY_ROOT=<approved-registry-root>
JWT_SECRET=<set-on-host>
AUTH_DISABLED=false
```

Important safety flags:

```dotenv
ENABLE_WRITE_OPERATIONS=false
ENABLE_ATTACHMENT_DOWNLOADS=false
REQUIRE_APPLY_FLAG=true
ENABLE_WEBHOOKS=false
WEBHOOK_SHARED_SECRET=
```

## First-Time Setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
cp .env.example .env
mise-smartsheet db upgrade --pretty
mise-smartsheet org validate-blueprint config/architecture/abed_pilot_blueprint.yaml --pretty
```

Docker option:

```bash
docker compose up --build app
python scripts/smoke_health.py http://localhost:8000
```

## Daily Operations

1. Confirm API health:

```bash
python scripts/smoke_health.py http://localhost:8000
```

2. Confirm database connectivity:

```bash
mise-smartsheet db status --pretty
```

3. Run the read-only polling cycle if needed:

```bash
mise-smartsheet sync poll-once --pretty
```

## Running Read-Only Discovery

Pull current TIR data:

```bash
mise-smartsheet tir pull --sheet-id "$SMARTSHEET_TIR_SHEET_ID" --out data/exports/tir_rows.json --pretty
```

Scan approved filesystem roots without modifying folders:

```bash
mise-smartsheet filesystem scan --root "$MISE_PROJECT_ROOT" --max-depth 4 --out data/exports/folder_inventory.json --pretty
```

## Running Reconciliation

```bash
mise-smartsheet reconcile --tir data/exports/tir_rows.json --folders data/exports/folder_inventory.json --out data/reports/reconciliation.json --pretty
```

Review categories before any apply operation:

```bash
mise-smartsheet data-quality check --tir data/exports/tir_rows.json --out data/reports/data_quality.json --pretty
```

## Exporting Reports

```bash
mise-smartsheet report export --tir data/exports/tir_rows.json --folders data/exports/folder_inventory.json --reconciliation data/reports/reconciliation.json --out data/reports --pretty
```

Expected outputs are written below `data/reports`.

## Dry-Run Planning

Generate a ministry-wide plan:

```bash
mise-smartsheet plan config/architecture/mise_ministry_blueprint.example.yaml --tir data/exports/tir_rows.json --folders data/exports/folder_inventory.json --out data/reports/plan.json --pretty
```

Generate the ABED pilot plan:

```bash
mise-smartsheet plan config/architecture/abed_pilot_blueprint.yaml --tir data/exports/tir_rows.json --folders data/exports/folder_inventory.json --out data/reports/abed_pilot_plan.json --pretty
```

## Applying Approved Folder Creation

Folder creation is blocked unless `ENABLE_WRITE_OPERATIONS=true` and `--apply` are both present.
Use only after the plan has been reviewed and approved.

```bash
mise-smartsheet apply-folder-plan data/reports/abed_pilot_plan.json --apply --root "$MISE_PROJECT_ROOT" --actor mise-it --pretty
```

## Applying Approved Smartsheet Write-Back

Smartsheet write-back is blocked unless `ENABLE_WRITE_OPERATIONS=true`, `--apply` is present, and
the update operation exists in the approved plan file.

```bash
mise-smartsheet apply-smartsheet-plan data/reports/abed_pilot_plan.json --apply --actor mise-it --pretty
```

Protected v1 columns:

- `SECRETARY APPROVAL`
- `CONTACT EMAIL`

## Log Locations

Application logs are emitted to process stdout/stderr. In Docker:

```bash
docker compose logs app
docker compose logs db
```

Generated reports and exports are stored in:

```text
data/exports
data/reports
```

## Audit Checks

Review audit output after guarded apply commands. For local in-memory audit tests:

```bash
pytest tests/test_audit.py tests/test_project_folder_creation.py tests/test_smartsheet_write_back.py
```

Operationally, preserve terminal output and generated plan/report files with the approval record.

## Backup and Restore

Before any pilot run, back up PostgreSQL and generated reports:

```bash
pg_dump "$DATABASE_URL" > backups/mise_smartsheet_$(date +%Y%m%d).sql
tar -czf backups/mise_reports_$(date +%Y%m%d).tar.gz data/reports data/exports
```

Restore database backup:

```bash
psql "$DATABASE_URL" < backups/mise_smartsheet_YYYYMMDD.sql
```

## Troubleshooting

- API returns `401`: confirm `Authorization: Bearer <token>` and `JWT_SECRET`.
- API returns `403`: confirm the token role is one of the allowed roles for the endpoint.
- Smartsheet returns auth errors: rotate/check `SMARTSHEET_ACCESS_TOKEN`.
- Folder scan has warnings: confirm `MISE_PROJECT_ROOT` exists and the service account can read it.
- Apply command refuses to run: confirm the reviewed plan path, `ENABLE_WRITE_OPERATIONS=true`, and `--apply`.
- Attachment download refuses to run: confirm `ENABLE_ATTACHMENT_DOWNLOADS=true`, `--apply-download`, and `ATTACHMENT_DOWNLOAD_ROOT`.

## Incident Response

1. Stop scheduled polling or the API container:

```bash
docker compose stop app
```

2. Preserve the triggering command, plan file, logs, and report exports.
3. Disable writes:

```dotenv
ENABLE_WRITE_OPERATIONS=false
ENABLE_ATTACHMENT_DOWNLOADS=false
```

4. Notify MISE IT lead and the responsible department director.
5. Restore from backup only after approval and root-cause review.

## Do Not Do In V1

- Do not delete, rename, or move project folders.
- Do not overwrite existing folders.
- Do not automatically change `SECRETARY APPROVAL`.
- Do not automatically change `CONTACT EMAIL`.
- Do not download attachment file contents unless the download feature flag and `--apply-download` are explicitly approved.
- Do not run write-back commands from an unreviewed or hand-edited plan.
- Do not enable `AUTH_DISABLED` outside local development.

## Pilot Checklist

Before pilot:

- Confirm `.env` values are set on the host and not committed.
- Run `pytest`, `ruff check .`, and `python -m compileall app tests scripts`.
- Back up database and current report/export folders.
- Validate `config/architecture/abed_pilot_blueprint.yaml`.
- Generate and review the ABED dry-run plan.

During pilot:

- Run TIR pull, filesystem scan, reconciliation, and report export.
- Record operator, timestamp, plan path, and approval reference.
- Keep writes disabled unless an approved apply window is active.

After pilot:

- Export final reports.
- Save plan, reconciliation, data-quality output, and terminal logs.
- Disable write/download flags.
- Document follow-up data-quality and folder remediation items.
