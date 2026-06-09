# Master Build Sequence

Run these prompts in VS Code Codex in the order listed below. Each prompt is written to be copied as a standalone instruction into Codex.

1. `01_repository_scaffold.md`
2. `02_environment_security_baseline.md`
3. `03_project_configuration_and_settings.md`
4. `04_logging_and_audit_foundation.md`
5. `05_smartsheet_client_read_only.md`
6. `06_cli_foundation.md`
7. `07_mise_organization_domain_model.md`
8. `08_tir_schema_and_column_mapping.md`
9. `09_database_models_and_migrations.md`
10. `10_smartsheet_tir_pull.md`
11. `11_filesystem_discovery.md`
12. `12_reconciliation_engine.md`
13. `13_export_reporting_outputs.md`
14. `14_fastapi_read_api.md`
15. `15_data_quality_and_validation.md`
16. `16_scheduler_polling_service.md`
17. `17_webhook_receiver_optional.md`
18. `18_dry_run_planner.md`
19. `19_safe_project_folder_creation.md`
20. `20_smartsheet_write_back_safe.md`
21. `21_attachment_handling.md`
22. `22_blueprint_parser.md`
23. `23_department_reporting_tables.md`
24. `24_authentication_authorization.md`
25. `25_docker_and_local_deployment.md`
26. `26_ci_testing_quality_gate.md`
27. `27_pilot_rollout_abed.md`
28. `28_operational_runbook.md`
29. `29_final_hardening_and_handover.md`
30. `99_common_follow_up_prompts.md`

## Working method

After each prompt:

```bash
pytest
ruff check .
python -m compileall app tests
```

Then review the diff and commit:

```bash
git status
git add .
git commit -m "step XX: short description"
```

Do not continue to the next prompt until the previous step is runnable.
