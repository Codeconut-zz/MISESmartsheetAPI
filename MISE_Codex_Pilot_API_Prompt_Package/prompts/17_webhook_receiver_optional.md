# 17 — Optional Webhook Receiver

## Objective

Prepare a webhook receiver for future event-driven integration if MICT/MISE approve inbound HTTPS routing.

## Prompt to paste into VS Code Codex

```text
Add an optional Smartsheet webhook receiver.

Requirements:
1. Create `app/api/webhooks.py`.
2. Add endpoint POST `/api/v1/webhooks/smartsheet`.
3. Validate a shared secret header from settings.
4. Accept webhook callback payloads and store events in an event table or audit table.
5. Do not process writes in the webhook handler directly.
6. Queue or mark events for background processing.
7. Add tests for accepted payloads, missing secret, invalid secret, and idempotent duplicate event handling.
8. The webhook feature must be disabled unless `ENABLE_WEBHOOKS=true`.
```

## Acceptance criteria

- Webhook endpoint is feature-flagged.
- Shared secret is required.
- Handler is idempotent and does not perform write operations directly.

## Suggested verification commands

```bash
pytest tests/test_webhooks.py
```
