# 03 — Project Configuration and Settings

## Objective

Harden application configuration, local paths, feature flags, and application constants.

## Prompt to paste into VS Code Codex

```text
Improve project configuration and settings.

Requirements:
1. Extend `app/config.py` with typed settings grouped by:
   - AppSettings
   - SmartsheetSettings
   - DatabaseSettings
   - FilesystemSettings
   - SecuritySettings
   - FeatureFlags
2. Add a `settings = get_settings()` factory with caching.
3. Add clear validation errors for missing required variables.
4. Add constants for default report folders and allowed export formats.
5. Add test cases for development, test, and production-like configurations.
6. Update README with configuration examples.

Do not make any network calls.
```

## Acceptance criteria

- Typed settings exist.
- Test configuration works without secrets.
- Production validation fails safely when required variables are absent.

## Suggested verification commands

```bash
pytest tests/test_config.py
mypy app || true
```
