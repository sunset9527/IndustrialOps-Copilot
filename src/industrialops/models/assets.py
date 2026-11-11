"""Equipment-model and concrete-asset persistence models."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from industrialops.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class EquipmentModel(Base):
    """A declared equipment-model scope linked to one frozen knowledge pack."""

    __tablename__ = "equipment_models"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    equipment_model_id: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    pack_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    manufacturer: Mapped[str] = mapped_column(String(120), nullable=False)
    model_name: Mapped[str] = mapped_column(String(120), nullable=False)
    controller_or_firmware_scope: Mapped[str | None] = mapped_column(String(160), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow
    )

    assets: Mapped[list["Asset"]] = relationship(back_populates="equipment_model")


class Asset(Base):
    """A concrete, explicitly synthetic or real-world equipment asset."""

    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    asset_id: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    equipment_model_id: Mapped[str] = mapped_column(
        ForeignKey("equipment_models.equipment_model_id", ondelete="RESTRICT"), nullable=False, index=True
    )
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    site: Mapped[str | None] = mapped_column(String(160), nullable=True)
    line: Mapped[str | None] = mapped_column(String(160), nullable=True)
    location: Mapped[str | None] = mapped_column(String(160), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="available", index=True)
    synthetic: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow
    )

    equipment_model: Mapped[EquipmentModel] = relationship(back_populates="assets")
