from app.utils.redaction import MASK, redact, redact_text


def test_redact_masks_sensitive_mapping_values() -> None:
    payload = {
        "access_token": "super-secret-token",
        "nested": {"password": "database-password", "name": "project alpha"},
    }

    assert redact(payload) == {
        "access_token": MASK,
        "nested": {"password": MASK, "name": "project alpha"},
    }


def test_redact_text_masks_emails_tokens_passwords_and_long_ids() -> None:
    text = (
        "user person@example.com token=abc123 password=swordfish "
        "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ sheet 12345678901234567890"
    )

    redacted = redact_text(text)

    assert "person@example.com" not in redacted
    assert "abc123" not in redacted
    assert "swordfish" not in redacted
    assert "eyJhbGci" not in redacted
    assert "12345678901234567890" not in redacted


def test_redact_text_masks_url_password() -> None:
    text = "postgresql+psycopg2://user:password@localhost:5432/mise_smartsheet"

    assert redact_text(text) == "postgresql+psycopg2://user:[REDACTED]@localhost:5432/mise_smartsheet"
