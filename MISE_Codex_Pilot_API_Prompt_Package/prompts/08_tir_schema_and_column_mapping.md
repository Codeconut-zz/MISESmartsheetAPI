# 08 — TIR Schema and Column Mapping

## Objective

Map the current Technical Intake Request database fields into typed application models.

## Prompt to paste into VS Code Codex

```text
Create the Technical Intake Request schema and column mapping.

Use these TIR fields:
- Created
- SECRETARY APPROVAL
- MISE HOD
- REGISTRY (Confirmation)
- REGISTRY (MISE File Ref)
- CLIENT (File Ref)
- ORGANISATION
- PROJECT NAME (Subject)
- SERVICE REQUEST
- PROJECT LOCATION
- PROJECT STATUS
- CONTACT PERSON
- CONTACT PERSON POSITION
- CONTACT NUMBER
- CONTACT EMAIL
- PROJECT BACKGROUND INFORMATION
- FUNDING SOURCE

Requirements:
1. Create `app/domain/tir.py` with a `TechnicalIntakeRequest` Pydantic model.
2. Create `config/mappings/tir_column_map.yaml` that maps Smartsheet display column names to internal snake_case fields.
3. Include validation for:
   - email format
   - phone as string, not integer
   - status values: NEW, PENDING, APPROVED, DECLINED, IN_PROGRESS, COMPLETED, ARCHIVED
   - boolean fields for secretary approval and registry confirmation
4. Add a mapper service that converts Smartsheet rows and cells into `TechnicalIntakeRequest` objects.
5. Add sample fixture data using the example rows in the current TIR database.
6. Add tests for mapping, validation, missing columns, unknown status, and multiline service request values.
```

## Acceptance criteria

- TIR model contains all listed fields.
- Column map uses exact display names.
- Tests include valid and invalid examples.

## Suggested verification commands

```bash
pytest tests/test_tir_mapping.py
ruff check app tests
```
