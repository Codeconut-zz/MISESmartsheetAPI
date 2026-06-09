# 21 — Attachment Handling

## Objective

Add read-only attachment metadata retrieval and prepare safe handling for official request letters.

## Prompt to paste into VS Code Codex

```text
Implement attachment handling.

Requirements:
1. Add read-only Smartsheet client methods to list row attachments and download attachment metadata.
2. Do not download attachment file contents by default.
3. Add CLI command:
   `mise-smartsheet tir attachments --sheet-id <id> --row-id <id> --metadata-only`
4. Add an optional download command that requires:
   - ENABLE_ATTACHMENT_DOWNLOADS=true
   - explicit `--apply-download`
   - target folder under configured safe root
5. Store only metadata in the database by default:
   - attachment ID
   - name
   - size
   - content type
   - source URL if available
   - linked TIR record
6. Add tests for metadata-only behavior.
7. Ensure filenames are sanitized before any future download.
```

## Acceptance criteria

- Metadata-only is the default.
- File download is feature-flagged and explicit.
- Tests verify safe filename handling.

## Suggested verification commands

```bash
pytest tests/test_attachment_handling.py
```
