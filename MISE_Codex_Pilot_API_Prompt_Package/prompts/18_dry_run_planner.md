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
