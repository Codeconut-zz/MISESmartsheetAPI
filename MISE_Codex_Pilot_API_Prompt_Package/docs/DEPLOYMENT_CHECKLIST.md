# Deployment Checklist

## Before deployment

- Confirm Smartsheet service account.
- Generate API token and store it securely.
- Confirm sheet ID for the TIR database.
- Confirm MISE project folder root.
- Confirm MISE registry folder root.
- Confirm database URL.
- Confirm server runtime: Docker, Linux systemd, or Windows service.
- Confirm backup location.

## First run

1. Run health check.
2. Run Smartsheet `whoami`.
3. List workspaces.
4. Pull TIR sheet in read-only mode.
5. Scan test folder root first.
6. Scan production folder root in read-only mode.
7. Run reconciliation.
8. Export report.
9. Review findings.

## Before enabling write operations

- Confirm dry-run plan is reviewed.
- Confirm pilot approval.
- Confirm `ENABLE_WRITE_OPERATIONS=true` only on approved environment.
- Confirm `--apply` is used only with a reviewed plan file.
- Confirm audit logging destination.
