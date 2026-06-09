# 06 — CLI Foundation

## Objective

Create the administrative CLI that MISE IT can use to run discovery, inventory, reconciliation, and future deployments.

## Prompt to paste into VS Code Codex

```text
Build the Typer CLI foundation.

Requirements:
1. Create a root command group named `mise-smartsheet`.
2. Add command groups:
   - `smartsheet`
   - `tir`
   - `filesystem`
   - `reconcile`
   - `report`
   - `plan`
   - `apply`
3. Implement:
   - `mise-smartsheet health`
   - `mise-smartsheet smartsheet whoami`
   - `mise-smartsheet smartsheet list-workspaces`
   - `mise-smartsheet smartsheet list-sheets`
4. Commands must output JSON by default and support `--pretty`.
5. Add graceful error messages for missing token or failed authentication.
6. Add CLI tests using Typer CliRunner and mocked Smartsheet client.
7. Update README with CLI usage.
```

## Acceptance criteria

- CLI groups exist.
- Read-only commands work with mocked client.
- JSON output is valid.

## Suggested verification commands

```bash
pytest tests/test_cli.py
python -m app.cli.main health
```
