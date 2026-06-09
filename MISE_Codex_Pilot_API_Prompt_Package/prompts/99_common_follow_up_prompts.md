# 99 — Common Follow-Up Prompts for VS Code Codex

Use these when Codex needs correction, debugging, or refinement.

## Fix failing tests

```text
Review the failing tests and fix the implementation, not the tests, unless the tests clearly contradict the documented requirements. Explain the root cause, update only the necessary files, and keep all safety controls intact.
```

## Add missing tests

```text
Inspect the last feature you implemented and add tests for the main success path, at least two failure paths, and one edge case. Do not reduce existing coverage. Do not weaken safety checks.
```

## Security review

```text
Review the repository for unsafe secret handling, hard-coded credentials, logging of tokens, production auth bypass, and write operations that do not require `--apply`. Patch any issues found and add regression tests.
```

## Refactor without changing behavior

```text
Refactor the selected module for readability and maintainability without changing behavior. Preserve public APIs, CLI commands, tests, and safety controls. Add or update tests only if needed.
```

## Improve error messages

```text
Improve user-facing CLI and API error messages for the selected module. Errors must explain what failed, what input was affected, and what action the operator should take. Do not expose secrets or full tokens.
```

## Add documentation for a command

```text
Document the selected CLI command in README and the operations runbook. Include purpose, required environment variables, example command, expected output, and common errors.
```

## Verify no production writes

```text
Trace all code paths that can write to Smartsheet, create folders, or update the database. Confirm that production-impacting operations require feature flag, plan file, explicit `--apply`, and audit logging. Patch any gaps.
```

## Prepare commit summary

```text
Summarize the changes in this branch as a commit message and a short reviewer note. Include tests run and any known limitations.
```
