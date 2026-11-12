"""Opaque bearer-session creation, resolution, and revocation."""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from secrets import token_urlsafe

from sqlalchemy import select
from sqlalchemy.orm import Session

from industrialops.models.auth_session import AuthSession
from industrialops.models.user import User


def create_auth_session(db: Session, user: User, *, expires_at: datetime) -> tuple[str, AuthSession]:
    """Return a bearer token once while persisting only its SHA-256 digest."""

    token = token_urlsafe(32)
    session = AuthSession(token_hash=_token_hash(token), user_id=user.id, expires_at=_as_utc(expires_at))
    db.add(session)
    db.flush()
    return token, session


def resolve_active_session(db: Session, token: str, *, now: datetime | None = None) -> AuthSession | None:
    """Return the matching session only when it is unrevoked and unexpired."""

    if not token:
        return None
    session = db.scalar(select(AuthSession).where(AuthSession.token_hash == _token_hash(token)))
    if session is None or session.revoked_at is not None or _as_utc(session.expires_at) <= _as_utc(now or datetime.now(timezone.utc)):
        return None
    return session


def revoke_auth_session(db: Session, session: AuthSession, *, now: datetime | None = None) -> None:
    """Revoke once without overwriting the original revocation timestamp."""

    if session.revoked_at is None:
        session.revoked_at = _as_utc(now or datetime.now(timezone.utc))
        db.flush()


def _token_hash(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()


def _as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)
