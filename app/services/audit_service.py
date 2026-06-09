"""Audit event creation and in-memory storage."""

from typing import Any

import structlog

from app.config import Environment, get_settings
from app.domain.audit import AuditEvent, AuditStatus


class InMemoryAuditSink:
    """Simple in-memory audit sink for early development and tests."""

    def __init__(self) -> None:
        self._events: list[AuditEvent] = []

    def append(self, event: AuditEvent) -> None:
        """Store an audit event."""
        self._events.append(event)

    def list_events(self) -> list[AuditEvent]:
        """Return audit events in insertion order."""
        return list(self._events)

    def clear(self) -> None:
        """Remove all stored audit events."""
        self._events.clear()


class AuditService:
    """Create audit events and emit redacted structured audit logs."""

    def __init__(self, sink: InMemoryAuditSink | None = None, *, emit_logs: bool = True) -> None:
        self._sink = sink or InMemoryAuditSink()
        self._emit_logs = emit_logs
        self._logger = structlog.get_logger("audit")

    @property
    def sink(self) -> InMemoryAuditSink:
        """Return the backing audit sink."""
        return self._sink

    def record(
        self,
        *,
        actor: str,
        action: str,
        target_type: str,
        target_id: str,
        status: AuditStatus,
        message: str,
        metadata: dict[str, Any] | None = None,
        environment: Environment | None = None,
        dry_run: bool = True,
    ) -> AuditEvent:
        """Create, store, and log a redacted audit event."""
        event = AuditEvent(
            actor=actor,
            action=action,
            target_type=target_type,
            target_id=target_id,
            environment=environment or get_settings().environment,
            dry_run=dry_run,
            status=status,
            message=message,
            metadata=metadata or {},
        )
        self._sink.append(event)
        if self._emit_logs:
            self._logger.info(
                "audit_event",
                actor=event.actor,
                action=event.action,
                target_type=event.target_type,
                target_id=event.target_id,
                environment=event.environment,
                dry_run=event.dry_run,
                status=event.status,
                message=event.message,
                metadata=event.metadata,
            )
        return event

    def list_events(self) -> list[AuditEvent]:
        """Return audit events in insertion order."""
        return self._sink.list_events()


audit_service = AuditService()
