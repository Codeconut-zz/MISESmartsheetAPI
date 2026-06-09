# MISE Codex Prompt Package — Pilot API Development

Prepared for: Ministry of Infrastructure and Sustainable Energy (MISE)  
Purpose: VS Code Codex prompt package for building the MISE-hosted Smartsheet pilot API and integration service.  
Date: 09 June 2026

## How to use this package

1. Create a private Git repository named `mise-smartsheet-integration`.
2. Open the repository in VS Code.
3. Install and sign in to the Codex IDE extension.
4. Copy `codex/AGENTS.md` into the root of the repository before running the prompts.
5. Work through `prompts/` in numerical order.
6. After each prompt, run tests, review the diff, and commit the working state.
7. Keep the first build read-only until the discovery and reconciliation reports are proven.
8. Do not add production credentials to prompts, commits, screenshots, or issue tickets.

## Application target

Build a MISE-hosted integration and execution service that connects to the Smartsheet API, reads the current Technical Intake Request register, scans MISE project folders, reconciles project records, exports reporting datasets, and later performs controlled write-back operations only after dry-run approval.

## Safety rule

The first production-facing milestone is read-only. Folder creation, Smartsheet row updates, webhook processing, and write-back operations are introduced only after the dry-run planner, audit logging, and explicit `--apply` controls are implemented.

## Main deliverables produced by the prompts

- Python + FastAPI application.
- Typer-based administrative CLI.
- Smartsheet API client.
- MISE filesystem discovery module.
- TIR column mapping and validation layer.
- PostgreSQL persistence layer.
- Reconciliation engine.
- CSV, JSON, and Excel report exporters.
- Dry-run deployment planner.
- Optional webhook or polling service.
- Docker deployment assets.
- Test suite and pilot runbook.

## Recommended execution order

Start with `00_MASTER_SEQUENCE.md`, then run prompts `01` through `29` in order.
