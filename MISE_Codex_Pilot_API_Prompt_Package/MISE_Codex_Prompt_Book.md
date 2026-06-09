# MISE VS Code Codex Prompt Book

# MISE Codex Prompt Package — Pilot API Development

Prepared for: Ministry of Infrastructure and Sustainable Energy (MISE)  
Purpose: VS Code Codex prompt package for building the MISE-hosted Smartsheet pilot API and integration service.  
Date: 09 June 2026

## How to use this package

1. Create a private Git repository named `mise-smartsheet-integration`.
2. Open the repository in VS Code.
3. Install and sign in to the Codex IDE extension.
4. Copy `codex/AGENTS.md` into the root of the repository before running the prompts.
5. Work through `prompts/` in numerical order.
6. After each prompt, run tests, review the diff, and commit the working state.
7. Keep the first build read-only until the discovery and reconciliation reports are proven.
8. Do not add production credentials to prompts, commits, screenshots, or issue tickets.

## Application target

Build a MISE-hosted integration and execution service that connects to the Smartsheet API, reads the current Technical Intake Request register, scans MISE project folders, reconciles project records, exports reporting datasets, and later performs controlled write-back operations only after dry-run approval.

## Safety rule

The first production-facing milestone is read-only. Folder creation, Smartsheet row updates, webhook processing, and write-back operations are introduced only after the dry-run planner, audit logging, and explicit `--apply` controls are implemented.

## Main deliverables produced by the prompts

- Python + FastAPI application.
- Typer-based administrative CLI.
- Smartsheet API client.
- MISE filesystem discovery module.
- TIR column mapping and validation layer.
- PostgreSQL persistence layer.
- Reconciliation engine.
- CSV, JSON, and Excel report exporters.
- Dry-run deployment planner.
- Optional webhook or polling service.
- Docker deployment assets.
- Test suite and pilot runbook.

## Recommended execution order

Start with `00_MASTER_SEQUENCE.md`, then run prompts `01` through `29` in order.


---

# AGENTS.md

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


---

# Master Build Sequence

Run these prompts in VS Code Codex in the order listed below. Each prompt is written to be copied as a standalone instruction into Codex.

1. `01_repository_scaffold.md`
2. `02_environment_security_baseline.md`
3. `03_project_configuration_and_settings.md`
4. `04_logging_and_audit_foundation.md`
5. `05_smartsheet_client_read_only.md`
6. `06_cli_foundation.md`
7. `07_mise_organization_domain_model.md`
8. `08_tir_schema_and_column_mapping.md`
9. `09_database_models_and_migrations.md`
10. `10_smartsheet_tir_pull.md`
11. `11_filesystem_discovery.md`
12. `12_reconciliation_engine.md`
13. `13_export_reporting_outputs.md`
14. `14_fastapi_read_api.md`
15. `15_data_quality_and_validation.md`
16. `16_scheduler_polling_service.md`
17. `17_webhook_receiver_optional.md`
18. `18_dry_run_planner.md`
19. `19_safe_project_folder_creation.md`
20. `20_smartsheet_write_back_safe.md`
21. `21_attachment_handling.md`
22. `22_blueprint_parser.md`
23. `23_department_reporting_tables.md`
24. `24_authentication_authorization.md`
25. `25_docker_and_local_deployment.md`
26. `26_ci_testing_quality_gate.md`
27. `27_pilot_rollout_abed.md`
28. `28_operational_runbook.md`
29. `29_final_hardening_and_handover.md`
30. `99_common_follow_up_prompts.md`

## Working method

After each prompt:

```bash
pytest
ruff check .
python -m compileall app tests
```

Then review the diff and commit:

```bash
git status
git add .
git commit -m "step XX: short description"
```

Do not continue to the next prompt until the previous step is runnable.


---

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


---

# 02 — Environment and Security Baseline

## Objective

Add environment handling, secret boundaries, and secure configuration practices before API connectivity is introduced.

## Prompt to paste into VS Code Codex

```text
Add the environment and security baseline.

Requirements:
1. Create `.env.example` with placeholders only:
   - ENVIRONMENT=development
   - LOG_LEVEL=INFO
   - SMARTSHEET_BASE_URL=https://api.smartsheet.com/2.0
   - SMARTSHEET_ACCESS_TOKEN=
   - SMARTSHEET_TIR_SHEET_ID=
   - DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/mise_smartsheet
   - MISE_PROJECT_ROOT=
   - MISE_REGISTRY_ROOT=
   - REPORT_EXPORT_ROOT=data/reports
   - ENABLE_WRITE_OPERATIONS=false
   - REQUIRE_APPLY_FLAG=true
2. Create `app/config.py` using pydantic-settings.
3. Add validation that production mode cannot start without required variables.
4. Add a secrets redaction utility that masks tokens, passwords, emails, and long IDs in logs.
5. Add tests for settings loading and redaction.
6. Add README notes explaining that real secrets must never be committed.
7. Do not create any real `.env` file.
```

## Acceptance criteria

- `.env.example` exists and contains placeholders only.
- Settings load in test mode.
- Redaction utility masks sensitive values.

## Suggested verification commands

```bash
pytest tests/test_config.py
ruff check app tests
```


---

# 03 — Project Configuration and Settings

## Objective

Harden application configuration, local paths, feature flags, and application constants.

## Prompt to paste into VS Code Codex

```text
Improve project configuration and settings.

Requirements:
1. Extend `app/config.py` with typed settings grouped by:
   - AppSettings
   - SmartsheetSettings
   - DatabaseSettings
   - FilesystemSettings
   - SecuritySettings
   - FeatureFlags
2. Add a `settings = get_settings()` factory with caching.
3. Add clear validation errors for missing required variables.
4. Add constants for default report folders and allowed export formats.
5. Add test cases for development, test, and production-like configurations.
6. Update README with configuration examples.

Do not make any network calls.
```

## Acceptance criteria

- Typed settings exist.
- Test configuration works without secrets.
- Production validation fails safely when required variables are absent.

## Suggested verification commands

```bash
pytest tests/test_config.py
mypy app || true
```


---

# 04 — Logging and Audit Foundation

## Objective

Add structured logging and an audit event model before any external integration is implemented.

## Prompt to paste into VS Code Codex

```text
Add structured logging and audit event support.

Requirements:
1. Configure structured logging using `structlog`.
2. Create `app/utils/logging.py` with a setup function.
3. Create `app/domain/audit.py` with an AuditEvent model.
4. Audit events must include:
   - timestamp
   - actor
   - action
   - target_type
   - target_id
   - environment
   - dry_run boolean
   - status
   - message
   - metadata dictionary
5. Create `app/services/audit_service.py` with an in-memory sink for now.
6. Ensure secrets are redacted before logs and audit metadata are emitted.
7. Add tests that verify audit events are created and redacted.
```

## Acceptance criteria

- Audit model exists.
- Structured logging is configured.
- Sensitive values are redacted from audit metadata.

## Suggested verification commands

```bash
pytest tests/test_audit.py
ruff check app tests
```


---

# 05 — Smartsheet Client: Read-Only Connectivity

## Objective

Build the first safe Smartsheet API client with only read operations.

## Prompt to paste into VS Code Codex

```text
Build a read-only Smartsheet API client.

Requirements:
1. Create `app/connectors/smartsheet_client.py`.
2. Use `httpx.Client` or `httpx.AsyncClient` with:
   - base URL from settings
   - Authorization header using `SMARTSHEET_ACCESS_TOKEN`
   - JSON accept headers
   - request timeout
   - retry/backoff for 429 and transient 5xx responses
3. Implement read-only methods:
   - `whoami()` using `/users/me`
   - `list_workspaces()` using `/workspaces`
   - `list_sheets()` using `/sheets`
   - `get_sheet(sheet_id, include=None, page_size=None, page=None)`
4. Add pagination helper logic.
5. Add a custom exception class for Smartsheet errors.
6. Add tests using `respx` mocks.
7. Do not implement POST, PUT, PATCH, or DELETE yet.
8. Ensure logs never expose the token.
```

## Acceptance criteria

- Client supports only read operations.
- Mock tests cover successful calls, 401, 403, 429, and 500.
- Token is never logged.

## Suggested verification commands

```bash
pytest tests/test_smartsheet_client.py
ruff check app tests
```


---

# 06 — CLI Foundation

## Objective

Create the administrative CLI that MISE IT can use to run discovery, inventory, reconciliation, and future deployments.

## Prompt to paste into VS Code Codex

```text
Build the Typer CLI foundation.

Requirements:
1. Create a root command group named `mise-smartsheet`.
2. Add command groups:
   - `smartsheet`
   - `tir`
   - `filesystem`
   - `reconcile`
   - `report`
   - `plan`
   - `apply`
3. Implement:
   - `mise-smartsheet health`
   - `mise-smartsheet smartsheet whoami`
   - `mise-smartsheet smartsheet list-workspaces`
   - `mise-smartsheet smartsheet list-sheets`
4. Commands must output JSON by default and support `--pretty`.
5. Add graceful error messages for missing token or failed authentication.
6. Add CLI tests using Typer CliRunner and mocked Smartsheet client.
7. Update README with CLI usage.
```

## Acceptance criteria

- CLI groups exist.
- Read-only commands work with mocked client.
- JSON output is valid.

## Suggested verification commands

```bash
pytest tests/test_cli.py
python -m app.cli.main health
```


---

# 07 — MISE Organization Domain Model

## Objective

Encode the Ministry hierarchy and department/division ownership model used by the Smartsheet architecture.

## Prompt to paste into VS Code Codex

```text
Create the MISE organization domain model.

Use this hierarchy:
- Minister MISE
- Secretary
- Director General Engineering Services
- Corporate Services
- Director Architectural Building & Engineering Department (ABED)
- Director Civil Engineering Department (CED)
- Director Energy Planning Department (EPD)
- Director Water Sanitation Engineering Department (WSED)
- ABED divisions:
  - Architectural Design Division (ADD)
  - Cost Planning Division (CPD)
  - Quality Control & Inspection Division (QCID)
  - Building Maintenance Division (BMD)

Requirements:
1. Create `app/domain/organization.py`.
2. Define Department, Division, Role, and ReportingLine models using Pydantic.
3. Create `config/architecture/mise_ministry_blueprint.example.yaml` reflecting the hierarchy.
4. Create a loader service that validates the YAML blueprint.
5. Add tests that validate ABED has exactly four divisions and that all departments have codes and names.
6. Add a command `mise-smartsheet org validate-blueprint <path>`.
```

## Acceptance criteria

- Blueprint YAML exists.
- Pydantic models validate the hierarchy.
- CLI validates blueprint files.

## Suggested verification commands

```bash
pytest tests/test_organization.py
python -m app.cli.main org validate-blueprint config/architecture/mise_ministry_blueprint.example.yaml
```


---

# 08 — TIR Schema and Column Mapping

## Objective

Map the current Technical Intake Request database fields into typed application models.

## Prompt to paste into VS Code Codex

```text
Create the Technical Intake Request schema and column mapping.

Use these TIR fields:
- Created
- SECRETARY APPROVAL
- MISE HOD
- REGISTRY (Confirmation)
- REGISTRY (MISE File Ref)
- CLIENT (File Ref)
- ORGANISATION
- PROJECT NAME (Subject)
- SERVICE REQUEST
- PROJECT LOCATION
- PROJECT STATUS
- CONTACT PERSON
- CONTACT PERSON POSITION
- CONTACT NUMBER
- CONTACT EMAIL
- PROJECT BACKGROUND INFORMATION
- FUNDING SOURCE

Requirements:
1. Create `app/domain/tir.py` with a `TechnicalIntakeRequest` Pydantic model.
2. Create `config/mappings/tir_column_map.yaml` that maps Smartsheet display column names to internal snake_case fields.
3. Include validation for:
   - email format
   - phone as string, not integer
   - status values: NEW, PENDING, APPROVED, DECLINED, IN_PROGRESS, COMPLETED, ARCHIVED
   - boolean fields for secretary approval and registry confirmation
4. Add a mapper service that converts Smartsheet rows and cells into `TechnicalIntakeRequest` objects.
5. Add sample fixture data using the example rows in the current TIR database.
6. Add tests for mapping, validation, missing columns, unknown status, and multiline service request values.
```

## Acceptance criteria

- TIR model contains all listed fields.
- Column map uses exact display names.
- Tests include valid and invalid examples.

## Suggested verification commands

```bash
pytest tests/test_tir_mapping.py
ruff check app tests
```


---

# 09 — Database Models and Migrations

## Objective

Add PostgreSQL persistence with SQLAlchemy and Alembic for project, TIR, folder inventory, audit, and reporting records.

## Prompt to paste into VS Code Codex

```text
Implement database models and migrations.

Requirements:
1. Configure SQLAlchemy 2.x and Alembic.
2. Create ORM models for:
   - tir_records
   - project_folder_inventory
   - reconciliation_results
   - audit_events
   - department_reporting_snapshots
3. Use UUID primary keys where appropriate.
4. Store Smartsheet row IDs and sheet IDs as strings.
5. Add indexes for registry_file_ref, project_name, contact_email, project_status, department_code, funding_source.
6. Add created_at and updated_at fields.
7. Add a repository layer under `app/storage/repositories.py`.
8. Add tests using SQLite for unit tests, while preserving PostgreSQL production compatibility.
9. Add commands:
   - `mise-smartsheet db init`
   - `mise-smartsheet db upgrade`
   - `mise-smartsheet db status`
```

## Acceptance criteria

- Alembic is configured.
- Models include required indexes.
- Repository tests pass using SQLite.

## Suggested verification commands

```bash
pytest tests/test_database.py
alembic heads
```


---

# 10 — Pull TIR Rows from Smartsheet

## Objective

Build the read-only import path from the current Smartsheet TIR sheet into validated TIR records.

## Prompt to paste into VS Code Codex

```text
Implement read-only TIR pulling from Smartsheet.

Requirements:
1. Add `app/services/tir_pull_service.py`.
2. Use `SMARTSHEET_TIR_SHEET_ID` from settings unless a CLI `--sheet-id` is provided.
3. Read the sheet using the Smartsheet client.
4. Map columns by title using `config/mappings/tir_column_map.yaml`.
5. Convert rows into `TechnicalIntakeRequest` models.
6. Persist valid records to the database if `--persist` is passed.
7. Export raw and normalized JSON when `--out` is passed.
8. Add CLI command:
   `mise-smartsheet tir pull --sheet-id <id> --out data/exports/tir_rows.json --pretty`
9. Include a summary output:
   - rows read
   - rows valid
   - rows invalid
   - missing columns
   - warnings
10. Add tests with mocked Smartsheet sheet responses.
```

## Acceptance criteria

- TIR rows can be read and normalized.
- Invalid rows are reported, not silently discarded.
- No write operations are performed.

## Suggested verification commands

```bash
pytest tests/test_tir_pull_service.py
```


---

# 11 — MISE Filesystem Discovery

## Objective

Scan current MISE project and registry folders without changing files.

## Prompt to paste into VS Code Codex

```text
Implement read-only MISE filesystem discovery.

Requirements:
1. Create `app/connectors/mise_filesystem.py`.
2. Create `app/services/filesystem_discovery_service.py`.
3. Read roots from:
   - MISE_PROJECT_ROOT
   - MISE_REGISTRY_ROOT
4. Support Windows UNC paths and Linux-mounted paths.
5. Recursively scan folders up to configurable depth.
6. Extract candidate registry file references from folder names using safe regex patterns.
7. Capture:
   - folder path
   - folder name
   - parent path
   - modified time
   - inferred registry reference
   - inferred project name
   - file count if cheap to compute
8. Never create, rename, move, or delete any file or folder.
9. Add CLI command:
   `mise-smartsheet filesystem scan --root <path> --max-depth 4 --out data/exports/folder_inventory.json`
10. Add tests using temporary folders only.
```

## Acceptance criteria

- Filesystem scan is read-only.
- Works with temp directories in tests.
- Exports JSON and CSV inventories.

## Suggested verification commands

```bash
pytest tests/test_filesystem_discovery.py
```


---

# 12 — Reconciliation Engine

## Objective

Match TIR records to existing MISE project folders and identify gaps, duplicates, and manual-review cases.

## Prompt to paste into VS Code Codex

```text
Build the reconciliation engine.

Requirements:
1. Create `app/services/reconciliation_service.py`.
2. Inputs:
   - normalized TIR records
   - folder inventory
3. Match priority:
   - exact registry_file_ref match
   - normalized project name match
   - contact email and project name combination
   - fuzzy fallback only as manual-review candidate
4. Output categories:
   - MATCHED
   - MISSING_FOLDER
   - DUPLICATE_REGISTRY_REFERENCE
   - MISSING_REGISTRY_REFERENCE
   - POSSIBLE_MATCH
   - MANUAL_REVIEW_REQUIRED
5. Add confidence score from 0 to 100.
6. Add reasons array explaining each result.
7. Add CLI command:
   `mise-smartsheet reconcile --tir data/exports/tir_rows.json --folders data/exports/folder_inventory.json --out data/reports/reconciliation.xlsx`
8. Add tests for exact match, duplicate, missing reference, missing folder, and possible match.
```

## Acceptance criteria

- Reconciliation categories are implemented.
- Results explain the reason for each category.
- Tests cover all categories.

## Suggested verification commands

```bash
pytest tests/test_reconciliation_service.py
```


---

# 13 — Export Reporting Outputs

## Objective

Generate files suitable for management, development partner reporting, and government reporting.

## Prompt to paste into VS Code Codex

```text
Implement reporting exports.

Requirements:
1. Create `app/services/report_export_service.py`.
2. Support export formats:
   - JSON
   - CSV
   - Excel XLSX
3. Excel workbook should include sheets:
   - Summary
   - TIR Records
   - Folder Inventory
   - Reconciliation Results
   - Data Quality Issues
4. Summary must include counts by:
   - project status
   - funding source
   - department/HOD
   - service request
   - project location
   - reconciliation category
5. Add timestamped output names.
6. Add CLI command:
   `mise-smartsheet report export --tir <path> --folders <path> --reconciliation <path> --out data/reports`
7. Add tests that verify generated workbook sheets and summary values.
```

## Acceptance criteria

- Excel, CSV, and JSON exports work.
- Workbook includes required tabs.
- Summary counts are tested.

## Suggested verification commands

```bash
pytest tests/test_report_export_service.py
```


---

# 14 — FastAPI Read API

## Objective

Expose read-only project, TIR, reconciliation, and reporting endpoints for internal consumption.

## Prompt to paste into VS Code Codex

```text
Build the initial FastAPI read API.

Requirements:
1. Add routers:
   - `app/api/health.py`
   - `app/api/tir.py`
   - `app/api/projects.py`
   - `app/api/reconciliation.py`
   - `app/api/reports.py`
2. Endpoints:
   - GET `/health`
   - GET `/api/v1/tir`
   - GET `/api/v1/tir/{record_id}`
   - GET `/api/v1/projects`
   - GET `/api/v1/reconciliation`
   - GET `/api/v1/reports/summary`
3. Add pagination, filtering, and sorting.
4. Filters must include project_status, funding_source, department_code, location, registry_file_ref, contact_email.
5. Use repository layer; do not call Smartsheet directly from API handlers.
6. Add OpenAPI tags and clear response models.
7. Add tests using FastAPI TestClient.
```

## Acceptance criteria

- Read-only API endpoints are implemented.
- Filtering and pagination work.
- API handlers use service/repository layers.

## Suggested verification commands

```bash
pytest tests/test_api_read.py
uvicorn app.main:app --reload
```


---

# 15 — Data Quality and Validation

## Objective

Add explicit data-quality checks so MISE can identify incomplete records before reporting to Government or development partners.

## Prompt to paste into VS Code Codex

```text
Add a data quality service.

Requirements:
1. Create `app/services/data_quality_service.py`.
2. Validate each TIR record for:
   - missing project name
   - missing contact email
   - missing registry file reference
   - missing funding source
   - invalid project status
   - missing service request
   - missing project location
   - missing secretary approval value
   - missing registry confirmation value
3. Return issue severity: INFO, WARNING, ERROR.
4. Provide a record-level completeness score.
5. Add summary counts by issue type.
6. Integrate data quality output into Excel report exports.
7. Add CLI command:
   `mise-smartsheet data-quality check --tir data/exports/tir_rows.json --out data/reports/data_quality.xlsx`
8. Add tests for every issue type.
```

## Acceptance criteria

- Data quality service exists.
- Completeness scores are computed.
- Excel export includes data quality issues.

## Suggested verification commands

```bash
pytest tests/test_data_quality_service.py
```


---

# 16 — Scheduler / Polling Service

## Objective

Add a safe polling path for environments where inbound webhooks are not yet approved.

## Prompt to paste into VS Code Codex

```text
Implement a polling service for scheduled read-only synchronization.

Requirements:
1. Create `app/services/polling_service.py`.
2. The polling service should:
   - pull the TIR sheet
   - normalize rows
   - persist new or changed rows
   - update last sync timestamp
   - write audit events
3. Add idempotency using Smartsheet row ID and modified timestamp if available.
4. Add CLI command:
   `mise-smartsheet sync poll-once`
5. Add a loop command for development only:
   `mise-smartsheet sync poll --interval-seconds 300`
6. Make polling read-only against Smartsheet.
7. Add tests for idempotent repeat polling.
```

## Acceptance criteria

- Polling does not create duplicate DB rows.
- Polling remains read-only against Smartsheet.
- Audit events are created.

## Suggested verification commands

```bash
pytest tests/test_polling_service.py
```


---

# 17 — Optional Webhook Receiver

## Objective

Prepare a webhook receiver for future event-driven integration if MICT/MISE approve inbound HTTPS routing.

## Prompt to paste into VS Code Codex

```text
Add an optional Smartsheet webhook receiver.

Requirements:
1. Create `app/api/webhooks.py`.
2. Add endpoint POST `/api/v1/webhooks/smartsheet`.
3. Validate a shared secret header from settings.
4. Accept webhook callback payloads and store events in an event table or audit table.
5. Do not process writes in the webhook handler directly.
6. Queue or mark events for background processing.
7. Add tests for accepted payloads, missing secret, invalid secret, and idempotent duplicate event handling.
8. The webhook feature must be disabled unless `ENABLE_WEBHOOKS=true`.
```

## Acceptance criteria

- Webhook endpoint is feature-flagged.
- Shared secret is required.
- Handler is idempotent and does not perform write operations directly.

## Suggested verification commands

```bash
pytest tests/test_webhooks.py
```


---

# 18 — Dry-Run Planner

## Objective

Build the safety layer that previews all proposed write operations before applying them.

## Prompt to paste into VS Code Codex

```text
Implement the dry-run planner.

Requirements:
1. Create `app/domain/plan.py` with models:
   - Plan
   - PlanOperation
   - OperationType
   - OperationRiskLevel
2. Supported operation types:
   - CREATE_PROJECT_FOLDER
   - CREATE_REPORT_FOLDER
   - UPDATE_SMARTSHEET_ROW
   - ADD_SMARTSHEET_ATTACHMENT_LINK
   - CREATE_DATABASE_RECORD
3. Each operation must include:
   - operation_id
   - target
   - reason
   - before_state summary
   - after_state summary
   - risk level
   - dry_run result
4. Create `app/services/dry_run_planner.py`.
5. Add CLI command:
   `mise-smartsheet plan <blueprint_path> --out data/reports/plan.json`
6. The planner must not change any external system.
7. Add tests verifying no write connectors are called during planning.
```

## Acceptance criteria

- Dry-run plan models exist.
- Plan command produces JSON.
- Tests prove no writes occur.

## Suggested verification commands

```bash
pytest tests/test_dry_run_planner.py
```


---

# 19 — Safe Project Folder Creation

## Objective

Introduce project folder creation only behind dry-run and explicit apply controls.

## Prompt to paste into VS Code Codex

```text
Implement safe project folder creation.

Requirements:
1. Create `app/services/project_folder_creation_service.py`.
2. Folder creation must require:
   - ENABLE_WRITE_OPERATIONS=true
   - explicit CLI `--apply`
   - a previously generated plan file
3. The service must never overwrite an existing folder.
4. Folder naming pattern:
   `{registry_file_ref_sanitized} - {project_name_sanitized}`
5. Sanitize invalid path characters.
6. Detect duplicate target folders and stop with a clear error.
7. Write audit events before and after folder creation.
8. Add CLI command:
   `mise-smartsheet apply-folder-plan data/reports/plan.json --apply`
9. Add tests using temporary directories only.
10. Do not add deletion, renaming, or move operations.
```

## Acceptance criteria

- Folder creation requires explicit apply.
- Existing folders are not overwritten.
- Tests use temporary directories only.

## Suggested verification commands

```bash
pytest tests/test_project_folder_creation.py
```


---

# 20 — Safe Smartsheet Write-Back

## Objective

Add the first controlled write-back functions to update project metadata in Smartsheet after approval.

## Prompt to paste into VS Code Codex

```text
Implement safe Smartsheet write-back functions.

Requirements:
1. Extend Smartsheet client with write methods only after safety controls exist.
2. Add method `update_row_cells(sheet_id, row_id, cells)`.
3. This method must require a safety context object confirming:
   - dry_run was completed
   - ENABLE_WRITE_OPERATIONS=true
   - `--apply` was provided
   - operation is present in approved plan file
4. Add write-back service to update fields such as:
   - project folder path/link
   - reconciliation status
   - data quality status
   - integration last sync timestamp
5. Never update Secretary approval values automatically in v1.
6. Never change contact email values automatically in v1.
7. Add audit events before and after the API call.
8. Add tests with mocked Smartsheet responses.
9. Add CLI command:
   `mise-smartsheet apply-smartsheet-plan data/reports/plan.json --apply`
```

## Acceptance criteria

- Write-back requires explicit approved plan and apply flag.
- Secretary approval and contact email are protected.
- Smartsheet writes are mocked in tests.

## Suggested verification commands

```bash
pytest tests/test_smartsheet_write_back.py
```


---

# 21 — Attachment Handling

## Objective

Add read-only attachment metadata retrieval and prepare safe handling for official request letters.

## Prompt to paste into VS Code Codex

```text
Implement attachment handling.

Requirements:
1. Add read-only Smartsheet client methods to list row attachments and download attachment metadata.
2. Do not download attachment file contents by default.
3. Add CLI command:
   `mise-smartsheet tir attachments --sheet-id <id> --row-id <id> --metadata-only`
4. Add an optional download command that requires:
   - ENABLE_ATTACHMENT_DOWNLOADS=true
   - explicit `--apply-download`
   - target folder under configured safe root
5. Store only metadata in the database by default:
   - attachment ID
   - name
   - size
   - content type
   - source URL if available
   - linked TIR record
6. Add tests for metadata-only behavior.
7. Ensure filenames are sanitized before any future download.
```

## Acceptance criteria

- Metadata-only is the default.
- File download is feature-flagged and explicit.
- Tests verify safe filename handling.

## Suggested verification commands

```bash
pytest tests/test_attachment_handling.py
```


---

# 22 — Architecture Blueprint Parser

## Objective

Parse ministry-wide architecture instructions from YAML into executable plan operations.

## Prompt to paste into VS Code Codex

```text
Build the architecture blueprint parser.

Requirements:
1. Create `app/domain/blueprint.py`.
2. Create `app/services/blueprint_parser.py`.
3. Support YAML sections:
   - ministry
   - departments
   - divisions
   - standard_folders
   - standard_sheets
   - reporting_outputs
   - folder_rules
   - smartsheet_writeback_rules
4. Validate required fields and reject unknown risky operation types.
5. Convert blueprint into dry-run plan operations.
6. Add sample file `config/architecture/mise_ministry_blueprint.example.yaml` if not already complete.
7. Add tests for valid blueprint, missing required fields, duplicate department codes, and invalid folder rules.
```

## Acceptance criteria

- Blueprint parser validates YAML.
- Invalid blueprints fail clearly.
- Parser feeds dry-run planner.

## Suggested verification commands

```bash
pytest tests/test_blueprint_parser.py
```


---

# 23 — Department Reporting Tables

## Objective

Create reporting snapshots that can serve Minister, Secretary, DG, departments, and development partner reporting needs.

## Prompt to paste into VS Code Codex

```text
Implement department reporting tables and snapshots.

Requirements:
1. Create `app/services/reporting_snapshot_service.py`.
2. Generate summaries for:
   - Ministry-wide portfolio
   - Secretary view
   - Director General technical delivery view
   - ABED view
   - CED view
   - EPD view
   - WSED view
   - ABED division views: ADD, CPD, QCID, BMD
3. Metrics must include:
   - number of projects
   - status breakdown
   - funding source breakdown
   - pending approvals
   - approved projects
   - declined projects
   - missing data count
   - missing folder count
   - service request breakdown
4. Store snapshots in the database.
5. Expose snapshots in API endpoint GET `/api/v1/reports/department-snapshots`.
6. Include snapshots in Excel exports.
7. Add tests using sample TIR data.
```

## Acceptance criteria

- Snapshots cover ministry, departments, and ABED divisions.
- API and Excel exports include snapshots.
- Metrics are tested.

## Suggested verification commands

```bash
pytest tests/test_reporting_snapshot_service.py
```


---

# 24 — API Authentication and Authorization

## Objective

Protect the internal read API using a simple, production-ready authentication pattern.

## Prompt to paste into VS Code Codex

```text
Add authentication and authorization for the FastAPI service.

Requirements:
1. Implement JWT bearer authentication for internal API access.
2. Support roles:
   - admin
   - reporting
   - read_only
   - integration_service
3. Add dependency functions under `app/security/auth.py`.
4. Protect all `/api/v1/*` endpoints except health.
5. Add local development bypass only when `ENVIRONMENT=development` and `AUTH_DISABLED=true`.
6. Do not enable bypass in production.
7. Add tests for authorized, unauthorized, and insufficient-role requests.
8. Update README with auth configuration and examples.
```

## Acceptance criteria

- API endpoints require auth by default.
- Development bypass is impossible in production.
- Role checks are tested.

## Suggested verification commands

```bash
pytest tests/test_auth.py
```


---

# 25 — Docker and Local Deployment

## Objective

Containerize the application so it can run consistently on the MISE server or local development machines.

## Prompt to paste into VS Code Codex

```text
Add Docker and local deployment assets.

Requirements:
1. Create `Dockerfile` for the FastAPI app.
2. Create `docker-compose.yml` with:
   - app
   - PostgreSQL
   - optional adminer or pgadmin disabled by default
3. Add healthcheck.
4. Mount `data/exports` and `data/reports` as volumes.
5. Use environment variables, not hard-coded secrets.
6. Add `scripts/run_local.sh` and `scripts/test_local.sh`.
7. Update README with local development deployment steps.
8. Add a simple smoke test script that calls `/health`.
```

## Acceptance criteria

- Docker build succeeds.
- Compose starts app and database.
- No secrets are embedded in Docker files.

## Suggested verification commands

```bash
docker compose config
pytest
```


---

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


---

# 27 — ABED Pilot Rollout

## Objective

Prepare a controlled ABED pilot scenario before full Ministry rollout.

## Prompt to paste into VS Code Codex

```text
Create the ABED pilot rollout configuration.

Requirements:
1. Create `config/architecture/abed_pilot_blueprint.yaml`.
2. Include ABED and four divisions:
   - ADD
   - CPD
   - QCID
   - BMD
3. Include pilot folders:
   - 01 - Intake
   - 02 - Active Projects
   - 03 - Project Files
   - 04 - Reports
   - 05 - Archive
4. Include pilot reporting snapshots for Director ABED and division heads.
5. Include dry-run rules only; no write operations by default.
6. Add CLI examples:
   - validate blueprint
   - generate plan
   - export dry-run report
7. Add tests that validate the ABED pilot blueprint.
```

## Acceptance criteria

- ABED pilot blueprint exists.
- Blueprint validates.
- No writes are enabled by default.

## Suggested verification commands

```bash
pytest tests/test_abed_pilot_blueprint.py
```


---

# 28 — Operational Runbook

## Objective

Generate the technical runbook for MISE IT to operate the pilot API.

## Prompt to paste into VS Code Codex

```text
Create an operational runbook.

Requirements:
1. Create `docs/OPERATIONS_RUNBOOK.md`.
2. Include sections:
   - system purpose
   - environment variables
   - first-time setup
   - daily operations
   - running read-only discovery
   - running reconciliation
   - exporting reports
   - dry-run planning
   - applying approved folder creation
   - applying approved Smartsheet write-back
   - log locations
   - audit checks
   - backup and restore
   - troubleshooting
   - incident response
3. Add exact command examples.
4. Include a “do not do” section listing prohibited v1 operations.
5. Add a checklist for before, during, and after pilot run.
```

## Acceptance criteria

- Runbook exists.
- Runbook contains operational command examples.
- Prohibited operations are explicit.

## Suggested verification commands

```bash
test -f docs/OPERATIONS_RUNBOOK.md
```


---

# 29 — Final Hardening and Handover

## Objective

Perform final hardening before the application is handed over for pilot execution.

## Prompt to paste into VS Code Codex

```text
Perform final hardening and handover preparation.

Requirements:
1. Review the whole repository for secrets and unsafe defaults.
2. Add `docs/SECURITY_REVIEW_CHECKLIST.md`.
3. Add `docs/PILOT_ACCEPTANCE_TEST_PLAN.md`.
4. Add `docs/HANDOVER_NOTES.md`.
5. Ensure README has a clean quickstart.
6. Confirm all write operations require:
   - feature flag
   - plan file
   - explicit apply flag
   - audit logging
7. Confirm deletion operations do not exist.
8. Confirm production mode does not allow auth bypass.
9. Confirm tests pass.
10. Produce a final summary of what was hardened and what remains intentionally out of scope.
```

## Acceptance criteria

- Security checklist exists.
- Pilot acceptance test plan exists.
- All tests pass.
- No deletion operations are implemented.

## Suggested verification commands

```bash
pytest
ruff check .
python -m compileall app tests
git grep -n "DELETE\|remove\|rmtree\|unlink" -- app tests || true
```


---

# 99 — Common Follow-Up Prompts for VS Code Codex

Use these when Codex needs correction, debugging, or refinement.

## Fix failing tests

```text
Review the failing tests and fix the implementation, not the tests, unless the tests clearly contradict the documented requirements. Explain the root cause, update only the necessary files, and keep all safety controls intact.
```

## Add missing tests

```text
Inspect the last feature you implemented and add tests for the main success path, at least two failure paths, and one edge case. Do not reduce existing coverage. Do not weaken safety checks.
```

## Security review

```text
Review the repository for unsafe secret handling, hard-coded credentials, logging of tokens, production auth bypass, and write operations that do not require `--apply`. Patch any issues found and add regression tests.
```

## Refactor without changing behavior

```text
Refactor the selected module for readability and maintainability without changing behavior. Preserve public APIs, CLI commands, tests, and safety controls. Add or update tests only if needed.
```

## Improve error messages

```text
Improve user-facing CLI and API error messages for the selected module. Errors must explain what failed, what input was affected, and what action the operator should take. Do not expose secrets or full tokens.
```

## Add documentation for a command

```text
Document the selected CLI command in README and the operations runbook. Include purpose, required environment variables, example command, expected output, and common errors.
```

## Verify no production writes

```text
Trace all code paths that can write to Smartsheet, create folders, or update the database. Confirm that production-impacting operations require feature flag, plan file, explicit `--apply`, and audit logging. Patch any gaps.
```

## Prepare commit summary

```text
Summarize the changes in this branch as a commit message and a short reviewer note. Include tests run and any known limitations.
```
