# 29 — Final Hardening and Handover

## Objective

Perform final hardening before the application is handed over for pilot execution.

## Prompt to paste into VS Code Codex

```text
Perform final hardening and handover preparation.

Requirements:
1. Review the whole repository for secrets and unsafe defaults.
2. Add `docs/SECURITY_REVIEW_CHECKLIST.md`.
3. Add `docs/PILOT_ACCEPTANCE_TEST_PLAN.md`.
4. Add `docs/HANDOVER_NOTES.md`.
5. Ensure README has a clean quickstart.
6. Confirm all write operations require:
   - feature flag
   - plan file
   - explicit apply flag
   - audit logging
7. Confirm deletion operations do not exist.
8. Confirm production mode does not allow auth bypass.
9. Confirm tests pass.
10. Produce a final summary of what was hardened and what remains intentionally out of scope.
```

## Acceptance criteria

- Security checklist exists.
- Pilot acceptance test plan exists.
- All tests pass.
- No deletion operations are implemented.

## Suggested verification commands

```bash
pytest
ruff check .
python -m compileall app tests
git grep -n "DELETE\|remove\|rmtree\|unlink" -- app tests || true
```
