# 04 — Logging and Audit Foundation

## Objective

Add structured logging and an audit event model before any external integration is implemented.

## Prompt to paste into VS Code Codex

```text
Add structured logging and audit event support.

Requirements:
1. Configure structured logging using `structlog`.
2. Create `app/utils/logging.py` with a setup function.
3. Create `app/domain/audit.py` with an AuditEvent model.
4. Audit events must include:
   - timestamp
   - actor
   - action
   - target_type
   - target_id
   - environment
   - dry_run boolean
   - status
   - message
   - metadata dictionary
5. Create `app/services/audit_service.py` with an in-memory sink for now.
6. Ensure secrets are redacted before logs and audit metadata are emitted.
7. Add tests that verify audit events are created and redacted.
```

## Acceptance criteria

- Audit model exists.
- Structured logging is configured.
- Sensitive values are redacted from audit metadata.

## Suggested verification commands

```bash
pytest tests/test_audit.py
ruff check app tests
```
