# Handover Notes

## What Was Hardened

- JWT bearer authentication protects `/api/v1/*`; `/health` remains public.
- Production mode rejects `AUTH_DISABLED=true` and requires `JWT_SECRET`.
- Smartsheet write-back requires feature flag, reviewed plan operation, explicit `--apply`, and audit events.
- Folder creation requires feature flag, reviewed plan file, explicit `--apply`, duplicate detection, and no overwrite.
- Attachment downloads require `ENABLE_ATTACHMENT_DOWNLOADS=true`, `--apply-download`, and a safe target root.
- Secretary approval and contact email write-back are blocked in v1.
- Docker/Compose deployment assets avoid embedded production secrets.
- CI runs Ruff, pytest with coverage, and compileall.

## Handover Artifacts

- `README.md`: quickstart, auth, Docker, ABED pilot, and verification notes.
- `docs/OPERATIONS_RUNBOOK.md`: operator workflow and incident response.
- `docs/SECURITY_REVIEW_CHECKLIST.md`: pre-pilot security checklist.
- `docs/PILOT_ACCEPTANCE_TEST_PLAN.md`: acceptance tests for ABED pilot.
- `config/architecture/abed_pilot_blueprint.yaml`: ABED-only pilot configuration.

## Intentional V1 Out Of Scope

- Folder deletion, renaming, or moving.
- Automatic Secretary approval updates.
- Automatic contact email updates.
- Automatic attachment content downloads.
- Unreviewed Smartsheet writes.
- Public unauthenticated internal API access.

## Recommended Pilot Sequence

1. Configure host `.env`.
2. Run database migrations.
3. Validate ABED pilot blueprint.
4. Pull TIR rows.
5. Scan folders.
6. Run reconciliation and data-quality checks.
7. Export reports.
8. Generate dry-run plan.
9. Review and approve any apply operation.
10. Disable write/download flags after the apply window.

## Remaining Follow-Up Items

- Replace in-memory audit sink with a persistent audit table writer for production audit retention.
- Add centralized log shipping once MISE server logging target is selected.
- Add real deployment secret management once the hosting environment is finalized.
- Add operational dashboards for webhook queue depth and polling freshness.
