# 16 — Scheduler / Polling Service

## Objective

Add a safe polling path for environments where inbound webhooks are not yet approved.

## Prompt to paste into VS Code Codex

```text
Implement a polling service for scheduled read-only synchronization.

Requirements:
1. Create `app/services/polling_service.py`.
2. The polling service should:
   - pull the TIR sheet
   - normalize rows
   - persist new or changed rows
   - update last sync timestamp
   - write audit events
3. Add idempotency using Smartsheet row ID and modified timestamp if available.
4. Add CLI command:
   `mise-smartsheet sync poll-once`
5. Add a loop command for development only:
   `mise-smartsheet sync poll --interval-seconds 300`
6. Make polling read-only against Smartsheet.
7. Add tests for idempotent repeat polling.
```

## Acceptance criteria

- Polling does not create duplicate DB rows.
- Polling remains read-only against Smartsheet.
- Audit events are created.

## Suggested verification commands

```bash
pytest tests/test_polling_service.py
```
