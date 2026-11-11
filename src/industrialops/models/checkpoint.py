"""SQL persistence tables for durable LangGraph checkpoints and pending writes."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, LargeBinary, String
from sqlalchemy.orm import Mapped, mapped_column

from industrialops.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class LangGraphCheckpoint(Base):
    """One typed LangGraph checkpoint for a durable thread and namespace."""

    __tablename__ = "langgraph_checkpoints"

    thread_id: Mapped[str] = mapped_column(String(160), primary_key=True)
    checkpoint_ns: Mapped[str] = mapped_column(String(255), primary_key=True, default="")
    checkpoint_id: Mapped[str] = mapped_column(String(160), primary_key=True)
    parent_checkpoint_id: Mapped[str | None] = mapped_column(String(160), nullable=True)
    checkpoint_type: Mapped[str] = mapped_column(String(64), nullable=False)
    checkpoint_blob: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    metadata_type: Mapped[str] = mapped_column(String(64), nullable=False)
    metadata_blob: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utcnow)


class LangGraphCheckpointWrite(Base):
    """A typed pending write associated with a checkpoint task."""

    __tablename__ = "langgraph_checkpoint_writes"

    thread_id: Mapped[str] = mapped_column(String(160), primary_key=True)
    checkpoint_ns: Mapped[str] = mapped_column(String(255), primary_key=True, default="")
    checkpoint_id: Mapped[str] = mapped_column(String(160), primary_key=True)
    task_id: Mapped[str] = mapped_column(String(160), primary_key=True)
    write_index: Mapped[int] = mapped_column(Integer, primary_key=True)
    channel: Mapped[str] = mapped_column(String(160), nullable=False)
    value_type: Mapped[str] = mapped_column(String(64), nullable=False)
    value_blob: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    task_path: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utcnow)
