# Risk Gates

## Gate 1 — Repository created
Proceed only when the scaffold runs and tests pass.

## Gate 2 — Read-only Smartsheet connection
Proceed only when `whoami`, workspace listing, and sheet listing are proven with no write methods implemented.

## Gate 3 — TIR import
Proceed only when current TIR rows can be normalized and invalid rows are reported.

## Gate 4 — Filesystem discovery
Proceed only when folder scanning is proven read-only using test folders first.

## Gate 5 — Reconciliation
Proceed only when matched, missing, duplicate, and manual-review categories are exported clearly.

## Gate 6 — Dry-run plan
Proceed only when proposed changes are visible before execution.

## Gate 7 — Write-back pilot
Proceed only with approved feature flags, plan file, `--apply`, and audit records.
