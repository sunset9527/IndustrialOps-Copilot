"""Work-order, approval, and immutable transition persistence models."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from industrialops.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class WorkOrder(Base):
    """A repair work order whose execution starts only after approval."""

    __tablename__ = "work_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    work_order_id: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    asset_id: Mapped[str] = mapped_column(ForeignKey("assets.asset_id", ondelete="RESTRICT"), nullable=False, index=True)
    diagnosis_request_id: Mapped[str] = mapped_column(
        ForeignKey("diagnosis_records.request_id", ondelete="RESTRICT"), nullable=False, index=True
    )
    thread_id: Mapped[str] = mapped_column(String(160), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    description: Mapped[str] = mapped_column(String(4000), nullable=False)
    priority: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft", index=True)
    assigned_to_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    diagnosis_snapshot: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    inspection_steps_snapshot: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    safety_prerequisites_snapshot: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    citations_snapshot: Mapped[list[dict[str, object]]] = mapped_column(JSON, nullable=False)
    created_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    asset: Mapped["Asset"] = relationship()
    diagnosis_record: Mapped["DiagnosisRecord"] = relationship()


class ApprovalDecision(Base):
    """The one final human decision associated with a work-order approval thread."""

    __tablename__ = "approval_decisions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    work_order_id: Mapped[str] = mapped_column(
        ForeignKey("work_orders.work_order_id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )
    thread_id: Mapped[str] = mapped_column(String(160), unique=True, nullable=False, index=True)
    decision: Mapped[str] = mapped_column(String(16), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    decided_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    decided_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utcnow)


class WorkOrderTransition(Base):
    """Append-only evidence of a completed lifecycle transition."""

    __tablename__ = "work_order_transitions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    work_order_id: Mapped[str] = mapped_column(
        ForeignKey("work_orders.work_order_id", ondelete="CASCADE"), nullable=False, index=True
    )
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    from_status: Mapped[str] = mapped_column(String(32), nullable=False)
    to_status: Mapped[str] = mapped_column(String(32), nullable=False)
    actor_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    reason: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utcnow)
