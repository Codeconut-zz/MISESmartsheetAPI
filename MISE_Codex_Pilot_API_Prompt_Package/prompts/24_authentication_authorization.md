# 24 — API Authentication and Authorization

## Objective

Protect the internal read API using a simple, production-ready authentication pattern.

## Prompt to paste into VS Code Codex

```text
Add authentication and authorization for the FastAPI service.

Requirements:
1. Implement JWT bearer authentication for internal API access.
2. Support roles:
   - admin
   - reporting
   - read_only
   - integration_service
3. Add dependency functions under `app/security/auth.py`.
4. Protect all `/api/v1/*` endpoints except health.
5. Add local development bypass only when `ENVIRONMENT=development` and `AUTH_DISABLED=true`.
6. Do not enable bypass in production.
7. Add tests for authorized, unauthorized, and insufficient-role requests.
8. Update README with auth configuration and examples.
```

## Acceptance criteria

- API endpoints require auth by default.
- Development bypass is impossible in production.
- Role checks are tested.

## Suggested verification commands

```bash
pytest tests/test_auth.py
```
