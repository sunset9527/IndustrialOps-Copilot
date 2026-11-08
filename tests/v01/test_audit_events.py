from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from industrialops.database import Base
from industrialops.models.audit import AuditEvent
from industrialops.services.audit import record_audit_event


def test_record_audit_event_persists_a_domain_neutral_event() -> None:
    engine = create_engine("sqlite://", poolclass=StaticPool)
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()

    event = record_audit_event(
        db,
        actor_user_id=None,
        action="system.health_checked",
        subject_type="service",
        subject_id="api",
        detail="readiness probe completed",
    )
    db.commit()

    persisted = db.get(AuditEvent, event.id)
    assert persisted is not None
    assert persisted.actor_user_id is None
    assert persisted.action == "system.health_checked"
    assert persisted.subject_type == "service"
    assert persisted.subject_id == "api"
    assert persisted.detail == "readiness probe completed"
