"""Persist sanitized diagnosis outcomes with explicit asset/pack compatibility."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from industrialops.models.assets import Asset, EquipmentModel
from industrialops.models.diagnosis import DiagnosisRecord


class DiagnosisAssetMismatchError(ValueError):
    code = "diagnosis_asset_pack_mismatch"


def record_diagnosis(
    db: Session,
    *,
    request_id: str,
    created_by_user_id: int | None,
    asset_id: str | None,
    pack_id: str,
    model: str | None,
    controller: str | None,
    status: str,
    intent: str,
    request_snapshot: dict[str, object],
    result_snapshot: dict[str, object],
    citations_snapshot: list[dict[str, object]],
    knowledge_pack_version: str,
) -> DiagnosisRecord:
    """Store a diagnosis only when its optional concrete asset belongs to the selected pack."""

    if asset_id is not None:
        _validate_asset_pack(db, asset_id, pack_id)
    record = DiagnosisRecord(
        request_id=request_id,
        created_by_user_id=created_by_user_id,
        asset_id=asset_id,
        pack_id=pack_id,
        model=model,
        controller=controller,
        status=status,
        intent=intent,
        request_snapshot=request_snapshot,
        result_snapshot=result_snapshot,
        citations_snapshot=citations_snapshot,
        knowledge_pack_version=knowledge_pack_version,
    )
    db.add(record)
    db.flush()
    return record


def _validate_asset_pack(db: Session, asset_id: str, pack_id: str) -> Asset:
    asset = db.scalar(select(Asset).where(Asset.asset_id == asset_id))
    if asset is None:
        raise DiagnosisAssetMismatchError("The diagnosis asset does not exist")
    equipment_model = db.scalar(
        select(EquipmentModel).where(EquipmentModel.equipment_model_id == asset.equipment_model_id)
    )
    if equipment_model is None or equipment_model.pack_id != pack_id:
        raise DiagnosisAssetMismatchError("The diagnosis asset is not compatible with the selected knowledge pack")
    return asset
