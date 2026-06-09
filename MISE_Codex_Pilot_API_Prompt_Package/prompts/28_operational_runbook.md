# 28 — Operational Runbook

## Objective

Generate the technical runbook for MISE IT to operate the pilot API.

## Prompt to paste into VS Code Codex

```text
Create an operational runbook.

Requirements:
1. Create `docs/OPERATIONS_RUNBOOK.md`.
2. Include sections:
   - system purpose
   - environment variables
   - first-time setup
   - daily operations
   - running read-only discovery
   - running reconciliation
   - exporting reports
   - dry-run planning
   - applying approved folder creation
   - applying approved Smartsheet write-back
   - log locations
   - audit checks
   - backup and restore
   - troubleshooting
   - incident response
3. Add exact command examples.
4. Include a “do not do” section listing prohibited v1 operations.
5. Add a checklist for before, during, and after pilot run.
```

## Acceptance criteria

- Runbook exists.
- Runbook contains operational command examples.
- Prohibited operations are explicit.

## Suggested verification commands

```bash
test -f docs/OPERATIONS_RUNBOOK.md
```
