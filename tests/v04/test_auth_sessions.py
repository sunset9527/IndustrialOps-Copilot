from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from industrialops.database import Base
from industrialops.models.auth_session import AuthSession
from industrialops.models.user import User
from industrialops.services.auth_sessions import create_auth_session, resolve_active_session, revoke_auth_session


def _session() -> Session:
    engine = create_engine("sqlite://", poolclass=StaticPool)
    Base.metadata.create_all(engine)
    return Session(engine)


def test_created_bearer_token_is_returned_once_but_only_its_hash_is_persisted() -> None:
    db = _session()
    user = User(username="approver", email="approver@example.com", password_hash="hash", role="approver")
    db.add(user)
    db.flush()

    token, session = create_auth_session(db, user, expires_at=datetime(2026, 11, 12, tzinfo=timezone.utc))
    db.commit()

    stored = db.get(AuthSession, session.id)
    assert stored is not None
    assert token not in stored.token_hash
    assert len(stored.token_hash) == 64
    assert resolve_active_session(db, token, now=datetime(2026, 11, 11, tzinfo=timezone.utc)).user_id == user.id


def test_expired_or_revoked_tokens_do_not_resolve_to_a_user() -> None:
    db = _session()
    user = User(username="admin", email="admin@example.com", password_hash="hash", role="admin")
    db.add(user)
    db.flush()
    token, session = create_auth_session(db, user, expires_at=datetime(2026, 11, 11, 1, tzinfo=timezone.utc))
    db.commit()

    assert resolve_active_session(db, token, now=datetime(2026, 11, 11, 2, tzinfo=timezone.utc)) is None

    fresh_token, fresh_session = create_auth_session(
        db, user, expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
    )
    revoke_auth_session(db, fresh_session, now=datetime.now(timezone.utc))
    db.commit()

    assert resolve_active_session(db, fresh_token, now=datetime.now(timezone.utc)) is None
