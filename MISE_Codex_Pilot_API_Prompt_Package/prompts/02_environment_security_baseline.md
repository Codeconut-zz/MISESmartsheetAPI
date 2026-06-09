# 02 — Environment and Security Baseline

## Objective

Add environment handling, secret boundaries, and secure configuration practices before API connectivity is introduced.

## Prompt to paste into VS Code Codex

```text
Add the environment and security baseline.

Requirements:
1. Create `.env.example` with placeholders only:
   - ENVIRONMENT=development
   - LOG_LEVEL=INFO
   - SMARTSHEET_BASE_URL=https://api.smartsheet.com/2.0
   - SMARTSHEET_ACCESS_TOKEN=
   - SMARTSHEET_TIR_SHEET_ID=
   - DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/mise_smartsheet
   - MISE_PROJECT_ROOT=
   - MISE_REGISTRY_ROOT=
   - REPORT_EXPORT_ROOT=data/reports
   - ENABLE_WRITE_OPERATIONS=false
   - REQUIRE_APPLY_FLAG=true
2. Create `app/config.py` using pydantic-settings.
3. Add validation that production mode cannot start without required variables.
4. Add a secrets redaction utility that masks tokens, passwords, emails, and long IDs in logs.
5. Add tests for settings loading and redaction.
6. Add README notes explaining that real secrets must never be committed.
7. Do not create any real `.env` file.
```

## Acceptance criteria

- `.env.example` exists and contains placeholders only.
- Settings load in test mode.
- Redaction utility masks sensitive values.

## Suggested verification commands

```bash
pytest tests/test_config.py
ruff check app tests
```
