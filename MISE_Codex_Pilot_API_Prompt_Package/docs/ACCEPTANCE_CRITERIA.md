# Pilot Acceptance Criteria

The pilot is acceptable when the application can:

1. Start locally and on the approved MISE server runtime.
2. Authenticate to Smartsheet using a secure token provided through environment variables.
3. Read the current Technical Intake Request sheet without writing to Smartsheet.
4. Normalize TIR rows into typed project records.
5. Scan configured MISE project folders in read-only mode.
6. Reconcile TIR records against folders.
7. Export JSON, CSV, and Excel reports.
8. Produce data quality findings for incomplete project records.
9. Serve read-only internal API endpoints.
10. Produce a dry-run plan before any write action.
11. Require explicit `--apply` and feature flags for write operations.
12. Produce audit logs for all integration actions.
13. Pass the test suite.
14. Avoid deletion operations in v1.
