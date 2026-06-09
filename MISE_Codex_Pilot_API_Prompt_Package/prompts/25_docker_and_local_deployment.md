# 25 — Docker and Local Deployment

## Objective

Containerize the application so it can run consistently on the MISE server or local development machines.

## Prompt to paste into VS Code Codex

```text
Add Docker and local deployment assets.

Requirements:
1. Create `Dockerfile` for the FastAPI app.
2. Create `docker-compose.yml` with:
   - app
   - PostgreSQL
   - optional adminer or pgadmin disabled by default
3. Add healthcheck.
4. Mount `data/exports` and `data/reports` as volumes.
5. Use environment variables, not hard-coded secrets.
6. Add `scripts/run_local.sh` and `scripts/test_local.sh`.
7. Update README with local development deployment steps.
8. Add a simple smoke test script that calls `/health`.
```

## Acceptance criteria

- Docker build succeeds.
- Compose starts app and database.
- No secrets are embedded in Docker files.

## Suggested verification commands

```bash
docker compose config
pytest
```
