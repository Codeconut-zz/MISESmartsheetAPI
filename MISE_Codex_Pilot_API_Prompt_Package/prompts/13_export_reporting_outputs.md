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
