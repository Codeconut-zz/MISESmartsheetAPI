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
