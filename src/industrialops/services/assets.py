"""Asset-ledger services with explicit model scope and optimistic versions."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from industrialops.models.assets import Asset, EquipmentModel


class AssetNotFoundError(LookupError):
    code = "asset_not_found"


class EquipmentModelNotFoundError(LookupError):
    code = "equipment_model_not_found"


class AssetVersionConflictError(ValueError):
    code = "stale_resource_version"


def create_asset(
    db: Session,
    *,
    asset_id: str,
    equipment_model_id: str,
    display_name: str,
    site: str | None = None,
    line: str | None = None,
    location: str | None = None,
    status: str = "available",
) -> Asset:
    """Create an explicitly synthetic asset under an existing equipment model."""

    _require_equipment_model(db, equipment_model_id)
    asset = Asset(
        asset_id=asset_id,
        equipment_model_id=equipment_model_id,
        display_name=display_name,
        site=site,
        line=line,
        location=location,
        status=status,
        synthetic=True,
    )
    db.add(asset)
    db.flush()
    return asset


def list_assets(
    db: Session,
    *,
    pack_id: str | None = None,
    equipment_model_id: str | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[Asset], int]:
    """List assets with deterministic ID ordering and an independently computed total."""

    filters = []
    if pack_id is not None:
        filters.append(EquipmentModel.pack_id == pack_id)
    if equipment_model_id is not None:
        filters.append(Asset.equipment_model_id == equipment_model_id)
    if status is not None:
        filters.append(Asset.status == status)
    total = db.scalar(select(func.count()).select_from(Asset).join(EquipmentModel).where(*filters)) or 0
    assets = list(
        db.scalars(
            select(Asset).join(EquipmentModel).where(*filters).order_by(Asset.asset_id).offset(offset).limit(limit)
        )
    )
    return assets, total


def update_asset(
    db: Session,
    asset_id: str,
    *,
    expected_version: int,
    display_name: str | None = None,
    site: str | None = None,
    line: str | None = None,
    location: str | None = None,
    status: str | None = None,
) -> Asset:
    """Update mutable ledger fields only when the caller holds the current version."""

    asset = db.scalar(select(Asset).where(Asset.asset_id == asset_id))
    if asset is None:
        raise AssetNotFoundError("Asset was not found")
    if asset.version != expected_version:
        raise AssetVersionConflictError("Asset has changed since it was read")
    for field, value in {
        "display_name": display_name,
        "site": site,
        "line": line,
        "location": location,
        "status": status,
    }.items():
        if value is not None:
            setattr(asset, field, value)
    asset.version += 1
    db.flush()
    return asset


def _require_equipment_model(db: Session, equipment_model_id: str) -> EquipmentModel:
    model = db.scalar(select(EquipmentModel).where(EquipmentModel.equipment_model_id == equipment_model_id))
    if model is None:
        raise EquipmentModelNotFoundError("Equipment model was not found")
    return model
