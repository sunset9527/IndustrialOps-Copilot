from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from industrialops.database import Base
from industrialops.models.assets import Asset, EquipmentModel
from industrialops.models.auth_session import AuthSession
from industrialops.models.checkpoint import LangGraphCheckpoint, LangGraphCheckpointWrite
from industrialops.models.diagnosis import DiagnosisRecord
from industrialops.models.user import User
from industrialops.models.work_order import ApprovalDecision, WorkOrder, WorkOrderTransition


def _session() -> Session:
    engine = create_engine("sqlite://", poolclass=StaticPool)
    Base.metadata.create_all(engine)
    return Session(engine)


def test_asset_uses_a_distinct_concrete_asset_id_and_equipment_model_id() -> None:
    db = _session()
    model = EquipmentModel(
        equipment_model_id="haas-vf2-ngc",
        pack_id="cnc_pack_v1.0.0",
        manufacturer="Haas",
        model_name="VF-2",
        controller_or_firmware_scope="NGC",
    )
    asset = Asset(
        asset_id="cnc-demo-001",
        equipment_model_id="haas-vf2-ngc",
        display_name="CNC 演示机 001",
        site="Demo Factory",
        status="available",
        synthetic=True,
    )
    db.add_all((model, asset))
    db.commit()

    loaded = db.get(Asset, asset.id)

    assert loaded is not None
    assert loaded.asset_id == "cnc-demo-001"
    assert loaded.equipment_model_id == "haas-vf2-ngc"
    assert loaded.equipment_model.model_name == "VF-2"
    assert loaded.synthetic is True


def test_work_order_preserves_diagnosis_and_citation_snapshots() -> None:
    db = _session()
    user = User(username="operator", email="operator@example.com", password_hash="hash", role="user")
    model = EquipmentModel(
        equipment_model_id="edwards-nxds-standard",
        pack_id="dry_vacuum_pump_pack_v1.0.0",
        manufacturer="Edwards",
        model_name="nXDS",
    )
    asset = Asset(
        asset_id="pump-demo-001",
        equipment_model_id="edwards-nxds-standard",
        display_name="真空泵演示机 001",
        status="available",
        synthetic=True,
    )
    diagnosis = DiagnosisRecord(
        request_id="diagnosis-001",
        asset_id="pump-demo-001",
        pack_id="dry_vacuum_pump_pack_v1.0.0",
        status="answered",
        intent="fault_diagnosis",
        request_snapshot={"question": "真空度不足"},
        result_snapshot={"inspection_steps": ["检查密封"]},
        citations_snapshot=[{"source_id": "pump-manual", "page_number": 12}],
        knowledge_pack_version="dry_vacuum_pump_pack_v1.0.0",
    )
    db.add_all((user, model, asset, diagnosis))
    db.flush()
    work_order = WorkOrder(
        work_order_id="wo-001",
        asset_id="pump-demo-001",
        diagnosis_request_id="diagnosis-001",
        thread_id="approval-001",
        title="处理真空度不足",
        description="基于诊断记录创建的草稿",
        priority="medium",
        status="draft",
        diagnosis_snapshot={"request_id": "diagnosis-001"},
        inspection_steps_snapshot=["检查密封"],
        safety_prerequisites_snapshot=["确认系统已隔离"],
        citations_snapshot=[{"source_id": "pump-manual", "page_number": 12}],
        created_by_user_id=user.id,
    )
    db.add(work_order)
    db.commit()

    loaded = db.get(WorkOrder, work_order.id)

    assert loaded is not None
    assert loaded.diagnosis_record.request_id == "diagnosis-001"
    assert loaded.inspection_steps_snapshot == ["检查密封"]
    assert loaded.citations_snapshot == [{"source_id": "pump-manual", "page_number": 12}]
    assert loaded.version == 1


def test_decision_and_transition_are_append_only_records_for_one_work_order() -> None:
    db = _session()
    requester = User(username="requester", email="requester@example.com", password_hash="hash", role="user")
    approver = User(username="approver", email="approver@example.com", password_hash="hash", role="approver")
    model = EquipmentModel(
        equipment_model_id="haas-vf2-ngc",
        pack_id="cnc_pack_v1.0.0",
        manufacturer="Haas",
        model_name="VF-2",
    )
    asset = Asset(asset_id="cnc-demo-001", equipment_model_id="haas-vf2-ngc", display_name="CNC", status="available", synthetic=True)
    diagnosis = DiagnosisRecord(
        request_id="diagnosis-002", asset_id="cnc-demo-001", pack_id="cnc_pack_v1.0.0", status="answered", intent="fault_diagnosis",
        request_snapshot={}, result_snapshot={}, citations_snapshot=[], knowledge_pack_version="cnc_pack_v1.0.0",
    )
    work_order = WorkOrder(
        work_order_id="wo-002", asset_id="cnc-demo-001", diagnosis_request_id="diagnosis-002", thread_id="approval-002",
        title="检查主轴", description="草稿", priority="high", status="draft", diagnosis_snapshot={}, inspection_steps_snapshot=[],
        safety_prerequisites_snapshot=[], citations_snapshot=[], created_by_user_id=1,
    )
    db.add_all((requester, approver, model, asset, diagnosis))
    db.flush()
    work_order.created_by_user_id = requester.id
    db.add(work_order)
    db.flush()
    db.add_all((
        ApprovalDecision(work_order_id="wo-002", thread_id="approval-002", decision="approved", reason="evidence reviewed", decided_by_user_id=approver.id),
        WorkOrderTransition(work_order_id="wo-002", action="approve", from_status="draft", to_status="approved", actor_user_id=approver.id, reason="evidence reviewed"),
    ))
    db.commit()

    assert db.query(ApprovalDecision).one().decided_by_user_id == approver.id
    assert db.query(WorkOrderTransition).one().to_status == "approved"


def test_unique_thread_id_and_token_hash_prevent_ambiguous_resume_or_login() -> None:
    db = _session()
    user = User(username="admin", email="admin@example.com", password_hash="hash", role="admin")
    db.add(user)
    db.flush()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    db.add(AuthSession(token_hash="a" * 64, user_id=user.id, expires_at=expires_at))
    db.commit()

    db.add(AuthSession(token_hash="a" * 64, user_id=user.id, expires_at=expires_at))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


def test_checkpoint_rows_use_thread_namespace_and_checkpoint_as_their_identity() -> None:
    db = _session()
    checkpoint = LangGraphCheckpoint(
        thread_id="approval-001",
        checkpoint_ns="",
        checkpoint_id="checkpoint-001",
        parent_checkpoint_id=None,
        checkpoint_type="json",
        checkpoint_blob=b"checkpoint",
        metadata_type="json",
        metadata_blob=b"metadata",
    )
    write = LangGraphCheckpointWrite(
        thread_id="approval-001",
        checkpoint_ns="",
        checkpoint_id="checkpoint-001",
        task_id="task-001",
        write_index=0,
        channel="approval",
        value_type="json",
        value_blob=b"decision",
        task_path="approval_graph",
    )
    db.add_all((checkpoint, write))
    db.commit()

    assert db.get(LangGraphCheckpoint, ("approval-001", "", "checkpoint-001")) is not None
    assert db.get(LangGraphCheckpointWrite, ("approval-001", "", "checkpoint-001", "task-001", 0)) is not None
