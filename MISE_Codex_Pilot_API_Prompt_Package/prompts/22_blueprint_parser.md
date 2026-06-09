# 22 — Architecture Blueprint Parser

## Objective

Parse ministry-wide architecture instructions from YAML into executable plan operations.

## Prompt to paste into VS Code Codex

```text
Build the architecture blueprint parser.

Requirements:
1. Create `app/domain/blueprint.py`.
2. Create `app/services/blueprint_parser.py`.
3. Support YAML sections:
   - ministry
   - departments
   - divisions
   - standard_folders
   - standard_sheets
   - reporting_outputs
   - folder_rules
   - smartsheet_writeback_rules
4. Validate required fields and reject unknown risky operation types.
5. Convert blueprint into dry-run plan operations.
6. Add sample file `config/architecture/mise_ministry_blueprint.example.yaml` if not already complete.
7. Add tests for valid blueprint, missing required fields, duplicate department codes, and invalid folder rules.
```

## Acceptance criteria

- Blueprint parser validates YAML.
- Invalid blueprints fail clearly.
- Parser feeds dry-run planner.

## Suggested verification commands

```bash
pytest tests/test_blueprint_parser.py
```
