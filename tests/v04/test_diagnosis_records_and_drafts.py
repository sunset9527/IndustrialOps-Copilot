from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from industrialops.database import Base
from industrialops.models.assets import Asset, EquipmentModel
from industrialops.models.user import User
from industrialops.services.diagnosis_records import DiagnosisAssetMismatchError, record_diagnosis
from industrialops.services.work_order_drafts import WorkOrderDraftNotAllowedError, create_work_order_draft


def _session() -> tuple[Session, User]:
    engine = create_engine("sqlite://", poolclass=StaticPool)
    Base.metadata.create_all(engine)
    db = Session(engine)
    user = User(username="operator", email="operator@example.com", password_hash="hash", role="user")
    model = EquipmentModel(equipment_model_id="haas-vf2-ngc", pack_id="cnc_pack_v1.0.0", manufacturer="Haas", model_name="VF-2")
    asset = Asset(asset_id="cnc-demo-001", equipment_model_id="haas-vf2-ngc", display_name="CNC 001", status="available", synthetic=True)
    db.add_all((user, model, asset))
    db.commit()
    return db, user


def test_record_diagnosis_rejects_an_asset_from_a_different_knowledge_pack() -> None:
    db, user = _session()

    with pytest.raises(DiagnosisAssetMismatchError) as error:
        record_diagnosis(
            db, request_id="diagnosis-001", created_by_user_id=user.id, asset_id="cnc-demo-001",
            pack_id="dry_vacuum_pump_pack_v1.0.0", model="VF-2", controller="NGC", status="answered",
            intent="fault_diagnosis", request_snapshot={"question": "主轴异响"}, result_snapshot={}, citations_snapshot=[],
            knowledge_pack_version="dry_vacuum_pump_pack_v1.0.0",
        )

    assert error.value.code == "diagnosis_asset_pack_mismatch"


def test_create_draft_copies_evidence_snapshots_only_from_a_compatible_answered_diagnosis() -> None:
    db, user = _session()
    diagnosis = record_diagnosis(
        db, request_id="diagnosis-002", created_by_user_id=user.id, asset_id="cnc-demo-001", pack_id="cnc_pack_v1.0.0",
        model="VF-2", controller="NGC", status="answered", intent="fault_diagnosis", request_snapshot={"question": "主轴异响"},
        result_snapshot={"inspection_steps": ["隔离能量后检查主轴"], "safety_prerequisites": ["挂牌上锁"]},
        citations_snapshot=[{"source_id": "haas-manual", "page_number": 42}], knowledge_pack_version="cnc_pack_v1.0.0",
    )
    db.commit()

    draft = create_work_order_draft(
        db, diagnosis_request_id=diagnosis.request_id, asset_id="cnc-demo-001", created_by_user_id=user.id,
        work_order_id="wo-001", thread_id="approval-001", title="检查主轴", description="依据诊断创建", priority="high",
    )

    assert draft.status == "draft"
    assert draft.thread_id == "approval-001"
    assert draft.inspection_steps_snapshot == ["隔离能量后检查主轴"]
    assert draft.citations_snapshot == [{"source_id": "haas-manual", "page_number": 42}]

    diagnosis.status = "blocked"
    with pytest.raises(WorkOrderDraftNotAllowedError) as error:
        create_work_order_draft(
            db, diagnosis_request_id=diagnosis.request_id, asset_id="cnc-demo-001", created_by_user_id=user.id,
            work_order_id="wo-002", thread_id="approval-002", title="不得创建", description="blocked", priority="high",
        )
    assert error.value.code == "work_order_draft_not_allowed"
