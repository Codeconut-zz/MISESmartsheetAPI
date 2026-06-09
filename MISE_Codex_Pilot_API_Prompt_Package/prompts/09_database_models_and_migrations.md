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
