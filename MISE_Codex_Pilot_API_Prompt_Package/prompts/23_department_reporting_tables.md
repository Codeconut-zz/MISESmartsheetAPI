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
