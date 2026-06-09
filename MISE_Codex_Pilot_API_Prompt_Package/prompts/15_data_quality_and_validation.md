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
