# 11 — MISE Filesystem Discovery

## Objective

Scan current MISE project and registry folders without changing files.

## Prompt to paste into VS Code Codex

```text
Implement read-only MISE filesystem discovery.

Requirements:
1. Create `app/connectors/mise_filesystem.py`.
2. Create `app/services/filesystem_discovery_service.py`.
3. Read roots from:
   - MISE_PROJECT_ROOT
   - MISE_REGISTRY_ROOT
4. Support Windows UNC paths and Linux-mounted paths.
5. Recursively scan folders up to configurable depth.
6. Extract candidate registry file references from folder names using safe regex patterns.
7. Capture:
   - folder path
   - folder name
   - parent path
   - modified time
   - inferred registry reference
   - inferred project name
   - file count if cheap to compute
8. Never create, rename, move, or delete any file or folder.
9. Add CLI command:
   `mise-smartsheet filesystem scan --root <path> --max-depth 4 --out data/exports/folder_inventory.json`
10. Add tests using temporary folders only.
```

## Acceptance criteria

- Filesystem scan is read-only.
- Works with temp directories in tests.
- Exports JSON and CSV inventories.

## Suggested verification commands

```bash
pytest tests/test_filesystem_discovery.py
```
