"""Create evidence-bound draft work orders from persisted diagnosis records."""

from __future__ import annotations

from copy import deepcopy

from sqlalchemy import select
from sqlalchemy.orm import Session

from industrialops.models.diagnosis import DiagnosisRecord
from industrialops.models.work_order import WorkOrder
from industrialops.services.diagnosis_records import _validate_asset_pack


class WorkOrderDraftNotAllowedError(ValueError):
    code = "work_order_draft_not_allowed"


def create_work_order_draft(
    db: Session,
    *,
    diagnosis_request_id: str,
    asset_id: str,
    created_by_user_id: int,
    work_order_id: str,
    thread_id: str,
    title: str,
    description: str,
    priority: str,
) -> WorkOrder:
    """Create a draft only from an answered diagnosis compatible with the target asset."""

    diagnosis = db.scalar(select(DiagnosisRecord).where(DiagnosisRecord.request_id == diagnosis_request_id))
    if diagnosis is None or diagnosis.status != "answered":
        raise WorkOrderDraftNotAllowedError("Only answered diagnoses may create a work-order draft")
    if diagnosis.asset_id is not None and diagnosis.asset_id != asset_id:
        raise WorkOrderDraftNotAllowedError("The requested asset differs from the diagnosis asset")
    try:
        _validate_asset_pack(db, asset_id, diagnosis.pack_id)
    except ValueError as error:
        raise WorkOrderDraftNotAllowedError("The requested asset is not compatible with the diagnosis pack") from error
    result_snapshot = deepcopy(diagnosis.result_snapshot)
    work_order = WorkOrder(
        work_order_id=work_order_id,
        asset_id=asset_id,
        diagnosis_request_id=diagnosis.request_id,
        thread_id=thread_id,
        title=title,
        description=description,
        priority=priority,
        status="draft",
        diagnosis_snapshot=result_snapshot,
        inspection_steps_snapshot=_string_items(result_snapshot.get("inspection_steps")),
        safety_prerequisites_snapshot=_string_items(result_snapshot.get("safety_prerequisites")),
        citations_snapshot=deepcopy(diagnosis.citations_snapshot),
        created_by_user_id=created_by_user_id,
    )
    db.add(work_order)
    db.flush()
    return work_order


def _string_items(value: object) -> list[str]:
    return [item for item in value if isinstance(item, str)] if isinstance(value, list) else []
