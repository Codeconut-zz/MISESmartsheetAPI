from app.domain.audit import AuditEvent
from app.services.audit_service import AuditService, InMemoryAuditSink
from app.utils.logging import redact_event_dict, setup_logging
from app.utils.redaction import MASK


def test_audit_event_redacts_sensitive_metadata() -> None:
    event = AuditEvent(
        actor="tester@example.com",
        action="sync",
        target_type="tir",
        target_id="row-123",
        environment="test",
        dry_run=True,
        status="success",
        message="completed with token=abc123",
        metadata={
            "access_token": "secret-token",
            "contact": "person@example.com",
            "sheet_id": "12345678901234567890",
        },
    )

    assert event.message == "completed with token=[REDACTED]"
    assert event.metadata["access_token"] == MASK
    assert event.metadata["contact"] == MASK
    assert event.metadata["sheet_id"] == MASK


def test_audit_service_records_redacted_events() -> None:
    sink = InMemoryAuditSink()
    service = AuditService(sink=sink)

    event = service.record(
        actor="system",
        action="pull",
        target_type="sheet",
        target_id="tir",
        environment="test",
        dry_run=True,
        status="pending",
        message="starting",
        metadata={"password": "database-password", "note": "safe"},
    )

    assert sink.list_events() == [event]
    assert event.metadata == {"password": MASK, "note": "safe"}


def test_structured_logging_redacts_event_payload() -> None:
    setup_logging("INFO")

    event_dict = redact_event_dict(
        logger=None,
        method_name="info",
        event_dict={"event": "called token=abc123", "email": "person@example.com"},
    )

    assert event_dict["event"] == "called token=[REDACTED]"
    assert event_dict["email"] == MASK
