# 27 — ABED Pilot Rollout

## Objective

Prepare a controlled ABED pilot scenario before full Ministry rollout.

## Prompt to paste into VS Code Codex

```text
Create the ABED pilot rollout configuration.

Requirements:
1. Create `config/architecture/abed_pilot_blueprint.yaml`.
2. Include ABED and four divisions:
   - ADD
   - CPD
   - QCID
   - BMD
3. Include pilot folders:
   - 01 - Intake
   - 02 - Active Projects
   - 03 - Project Files
   - 04 - Reports
   - 05 - Archive
4. Include pilot reporting snapshots for Director ABED and division heads.
5. Include dry-run rules only; no write operations by default.
6. Add CLI examples:
   - validate blueprint
   - generate plan
   - export dry-run report
7. Add tests that validate the ABED pilot blueprint.
```

## Acceptance criteria

- ABED pilot blueprint exists.
- Blueprint validates.
- No writes are enabled by default.

## Suggested verification commands

```bash
pytest tests/test_abed_pilot_blueprint.py
```
