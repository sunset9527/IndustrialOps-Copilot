"""Persisted, evidence-bound diagnosis snapshots for downstream work orders."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from industrialops.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class DiagnosisRecord(Base):
    """A sanitized immutable result of one diagnosis request."""

    __tablename__ = "diagnosis_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    request_id: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    created_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    asset_id: Mapped[str | None] = mapped_column(ForeignKey("assets.asset_id", ondelete="SET NULL"), nullable=True, index=True)
    pack_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    model: Mapped[str | None] = mapped_column(String(120), nullable=True)
    controller: Mapped[str | None] = mapped_column(String(120), nullable=True)
    status: Mapped[str] = mapped_column(String(48), nullable=False, index=True)
    intent: Mapped[str] = mapped_column(String(48), nullable=False)
    request_snapshot: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    result_snapshot: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    citations_snapshot: Mapped[list[dict[str, object]]] = mapped_column(JSON, nullable=False)
    knowledge_pack_version: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utcnow)

    asset: Mapped["Asset | None"] = relationship()
