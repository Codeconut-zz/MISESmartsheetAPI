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
