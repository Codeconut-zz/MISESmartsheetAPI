# Security Review Checklist

## Configuration

- [ ] `.env` is present only on the deployment host and is not committed.
- [ ] `ENVIRONMENT=production` is set for production.
- [ ] `AUTH_DISABLED=false` in production.
- [ ] `JWT_SECRET` is set from a managed secret source.
- [ ] `SMARTSHEET_ACCESS_TOKEN` is set from a managed secret source.
- [ ] `DATABASE_URL` does not use placeholder credentials.
- [ ] `MISE_PROJECT_ROOT` and `MISE_REGISTRY_ROOT` point to approved MISE paths.

## Authentication And Authorization

- [ ] `/health` is public.
- [ ] `/api/v1/*` endpoints require JWT bearer auth.
- [ ] Roles are assigned only as needed: `admin`, `reporting`, `read_only`, `integration_service`.
- [ ] Production settings reject auth bypass.

## Write Safety

- [ ] `ENABLE_WRITE_OPERATIONS=false` by default.
- [ ] Folder creation requires a plan file and `--apply`.
- [ ] Smartsheet write-back requires a plan file and `--apply`.
- [ ] Smartsheet write-back blocks `SECRETARY APPROVAL` and `CONTACT EMAIL`.
- [ ] Attachment download requires `ENABLE_ATTACHMENT_DOWNLOADS=true` and `--apply-download`.
- [ ] Apply operations record audit events before and after the external action.

## Prohibited V1 Operations

- [ ] No folder deletion operation exists.
- [ ] No folder rename operation exists.
- [ ] No folder move operation exists.
- [ ] No automatic Secretary approval update exists.
- [ ] No automatic contact email update exists.

## Verification Commands

```bash
pytest
ruff check .
python -m compileall app tests scripts
git grep -n "DELETE\|remove\|rmtree\|unlink" -- app tests || true
```

## Handover Sign-Off

- [ ] Security reviewer:
- [ ] MISE IT owner:
- [ ] Pilot director/department owner:
- [ ] Date:
