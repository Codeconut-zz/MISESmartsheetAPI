# Pilot Acceptance Test Plan

## Scope

This plan verifies the ABED pilot rollout before any full Ministry rollout. It covers read-only
Smartsheet access, filesystem discovery, reconciliation, report export, dry-run planning, guarded
apply controls, API auth, and operational handover.

## Preconditions

- `.env` exists on the pilot host with real operational values.
- `ENABLE_WRITE_OPERATIONS=false` before testing begins.
- `ENABLE_ATTACHMENT_DOWNLOADS=false` before testing begins.
- Database migrations have run with `mise-smartsheet db upgrade --pretty`.
- ABED pilot blueprint validates.

## Test Cases

### 1. Health And Auth

```bash
python scripts/smoke_health.py http://localhost:8000
curl http://localhost:8000/api/v1/reports/summary
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/reports/summary
```

Expected:

- `/health` returns `{"status":"ok"}`.
- Unauthenticated `/api/v1/*` request returns `401`.
- Authorized reporting/admin token returns `200`.

### 2. Blueprint Validation

```bash
mise-smartsheet org validate-blueprint config/architecture/abed_pilot_blueprint.yaml --pretty
mise-smartsheet plan config/architecture/abed_pilot_blueprint.yaml --out data/reports/abed_pilot_plan.json --pretty
```

Expected:

- Blueprint is valid.
- Plan is generated.
- No write action is applied.

### 3. Read-Only Smartsheet Pull

```bash
mise-smartsheet tir pull --sheet-id "$SMARTSHEET_TIR_SHEET_ID" --out data/exports/tir_rows.json --pretty
```

Expected:

- Rows are read.
- Invalid rows are reported without stopping valid row processing.
- No Smartsheet writes occur.

### 4. Filesystem Discovery

```bash
mise-smartsheet filesystem scan --root "$MISE_PROJECT_ROOT" --max-depth 4 --out data/exports/folder_inventory.json --pretty
```

Expected:

- Folder inventory is exported.
- Filesystem is not modified.

### 5. Reconciliation And Reporting

```bash
mise-smartsheet reconcile --tir data/exports/tir_rows.json --folders data/exports/folder_inventory.json --out data/reports/reconciliation.json --pretty
mise-smartsheet report export --tir data/exports/tir_rows.json --folders data/exports/folder_inventory.json --reconciliation data/reports/reconciliation.json --out data/reports --pretty
```

Expected:

- Reconciliation categories are generated.
- Excel report includes Department Snapshots.
- Data-quality issues are visible.

### 6. Guarded Folder Apply Refusal

```bash
mise-smartsheet apply-folder-plan data/reports/abed_pilot_plan.json --root "$MISE_PROJECT_ROOT" --pretty
```

Expected:

- Command refuses to run without `--apply`.

### 7. Guarded Smartsheet Apply Refusal

```bash
mise-smartsheet apply-smartsheet-plan data/reports/abed_pilot_plan.json --pretty
```

Expected:

- Command refuses to run without `--apply`.

## Acceptance Criteria

- All automated tests pass.
- ABED blueprint validates.
- Read-only workflows produce expected exports.
- Report workbook is generated.
- Writes remain disabled unless explicitly approved.
- No prohibited v1 operation is available.
