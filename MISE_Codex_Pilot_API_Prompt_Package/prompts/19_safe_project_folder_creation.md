# 19 — Safe Project Folder Creation

## Objective

Introduce project folder creation only behind dry-run and explicit apply controls.

## Prompt to paste into VS Code Codex

```text
Implement safe project folder creation.

Requirements:
1. Create `app/services/project_folder_creation_service.py`.
2. Folder creation must require:
   - ENABLE_WRITE_OPERATIONS=true
   - explicit CLI `--apply`
   - a previously generated plan file
3. The service must never overwrite an existing folder.
4. Folder naming pattern:
   `{registry_file_ref_sanitized} - {project_name_sanitized}`
5. Sanitize invalid path characters.
6. Detect duplicate target folders and stop with a clear error.
7. Write audit events before and after folder creation.
8. Add CLI command:
   `mise-smartsheet apply-folder-plan data/reports/plan.json --apply`
9. Add tests using temporary directories only.
10. Do not add deletion, renaming, or move operations.
```

## Acceptance criteria

- Folder creation requires explicit apply.
- Existing folders are not overwritten.
- Tests use temporary directories only.

## Suggested verification commands

```bash
pytest tests/test_project_folder_creation.py
```
