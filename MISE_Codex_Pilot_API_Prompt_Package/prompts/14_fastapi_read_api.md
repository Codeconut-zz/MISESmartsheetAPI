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
