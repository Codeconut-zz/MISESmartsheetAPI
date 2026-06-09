# Codex Usage Guide

Open the repository in VS Code, install the Codex IDE extension, copy `codex/AGENTS.md` into the repository root, and run the prompt files in numerical order.

Use one prompt per Codex task. Review the diff after every prompt. Run tests before committing.

Do not paste real tokens, passwords, file-server credentials, private server paths, or production screenshots into Codex prompts. Use placeholder values in examples and configure real values only in the local `.env` or server secret store.

Recommended Codex mode: Agent mode for coding inside the repository. Use full-access mode only when deliberately running local commands you have reviewed.
