# 05 — Smartsheet Client: Read-Only Connectivity

## Objective

Build the first safe Smartsheet API client with only read operations.

## Prompt to paste into VS Code Codex

```text
Build a read-only Smartsheet API client.

Requirements:
1. Create `app/connectors/smartsheet_client.py`.
2. Use `httpx.Client` or `httpx.AsyncClient` with:
   - base URL from settings
   - Authorization header using `SMARTSHEET_ACCESS_TOKEN`
   - JSON accept headers
   - request timeout
   - retry/backoff for 429 and transient 5xx responses
3. Implement read-only methods:
   - `whoami()` using `/users/me`
   - `list_workspaces()` using `/workspaces`
   - `list_sheets()` using `/sheets`
   - `get_sheet(sheet_id, include=None, page_size=None, page=None)`
4. Add pagination helper logic.
5. Add a custom exception class for Smartsheet errors.
6. Add tests using `respx` mocks.
7. Do not implement POST, PUT, PATCH, or DELETE yet.
8. Ensure logs never expose the token.
```

## Acceptance criteria

- Client supports only read operations.
- Mock tests cover successful calls, 401, 403, 429, and 500.
- Token is never logged.

## Suggested verification commands

```bash
pytest tests/test_smartsheet_client.py
ruff check app tests
```
