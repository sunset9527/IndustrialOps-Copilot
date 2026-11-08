"""Services for recording domain-neutral audit events."""

from __future__ import annotations

from sqlalchemy.orm import Session

from industrialops.models.audit import AuditEvent


def record_audit_event(
    db: Session,
    *,
    actor_user_id: int | None,
    action: str,
    subject_type: str,
    subject_id: str,
    detail: str = "",
) -> AuditEvent:
    """Add an audit event to the current database transaction."""

    event = AuditEvent(
        actor_user_id=actor_user_id,
        action=action,
        subject_type=subject_type,
        subject_id=subject_id,
        detail=detail,
    )
    db.add(event)
    db.flush()
    return event
