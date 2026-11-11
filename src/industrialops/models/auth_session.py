"""Opaque, database-backed authentication session persistence."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from industrialops.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AuthSession(Base):
    """Stores only a SHA-256 token digest, never a reusable bearer token."""

    __tablename__ = "auth_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utcnow)
