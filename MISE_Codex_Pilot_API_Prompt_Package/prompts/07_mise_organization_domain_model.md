# 07 — MISE Organization Domain Model

## Objective

Encode the Ministry hierarchy and department/division ownership model used by the Smartsheet architecture.

## Prompt to paste into VS Code Codex

```text
Create the MISE organization domain model.

Use this hierarchy:
- Minister MISE
- Secretary
- Director General Engineering Services
- Corporate Services
- Director Architectural Building & Engineering Department (ABED)
- Director Civil Engineering Department (CED)
- Director Energy Planning Department (EPD)
- Director Water Sanitation Engineering Department (WSED)
- ABED divisions:
  - Architectural Design Division (ADD)
  - Cost Planning Division (CPD)
  - Quality Control & Inspection Division (QCID)
  - Building Maintenance Division (BMD)

Requirements:
1. Create `app/domain/organization.py`.
2. Define Department, Division, Role, and ReportingLine models using Pydantic.
3. Create `config/architecture/mise_ministry_blueprint.example.yaml` reflecting the hierarchy.
4. Create a loader service that validates the YAML blueprint.
5. Add tests that validate ABED has exactly four divisions and that all departments have codes and names.
6. Add a command `mise-smartsheet org validate-blueprint <path>`.
```

## Acceptance criteria

- Blueprint YAML exists.
- Pydantic models validate the hierarchy.
- CLI validates blueprint files.

## Suggested verification commands

```bash
pytest tests/test_organization.py
python -m app.cli.main org validate-blueprint config/architecture/mise_ministry_blueprint.example.yaml
```
