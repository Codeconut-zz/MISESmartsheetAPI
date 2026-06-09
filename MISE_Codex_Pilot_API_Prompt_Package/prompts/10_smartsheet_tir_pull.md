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
