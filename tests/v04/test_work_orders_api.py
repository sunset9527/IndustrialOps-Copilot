from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from industrialops.api import create_app
from industrialops.config import Settings
from industrialops.database import Base
from industrialops.models.assets import Asset, EquipmentModel
from industrialops.models.user import User
from industrialops.services.auth_sessions import create_auth_session
from industrialops.services.diagnosis_records import record_diagnosis


def _prepared_client() -> tuple[TestClient, dict[str, dict[str, str]]]:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine)
    db = sessions()
    operator = User(username="operator", email="operator@example.com", password_hash="hash", role="user")
    approver = User(username="approver", email="approver@example.com", password_hash="hash", role="approver")
    admin = User(username="admin", email="admin@example.com", password_hash="hash", role="admin")
    technician = User(username="technician", email="technician@example.com", password_hash="hash", role="user")
    db.add_all((
        operator, approver, admin, technician,
        EquipmentModel(equipment_model_id="haas-vf2-ngc", pack_id="cnc_pack_v1.0.0", manufacturer="Haas", model_name="VF-2"),
        Asset(asset_id="cnc-demo-001", equipment_model_id="haas-vf2-ngc", display_name="CNC 001", status="available", synthetic=True),
    ))
    db.flush()
    record_diagnosis(
        db, request_id="diagnosis-001", created_by_user_id=operator.id, asset_id="cnc-demo-001", pack_id="cnc_pack_v1.0.0",
        model="VF-2", controller="NGC", status="answered", intent="fault_diagnosis", request_snapshot={},
        result_snapshot={"inspection_steps": ["隔离能量后检查主轴"], "safety_prerequisites": ["挂牌上锁"]},
        citations_snapshot=[{"source_id": "haas-manual", "page_number": 42}], knowledge_pack_version="cnc_pack_v1.0.0",
    )
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    tokens = {
        user.username: {"Authorization": f"Bearer {create_auth_session(db, user, expires_at=expires_at)[0]}"}
        for user in (operator, approver, admin, technician)
    }
    db.commit()
    return TestClient(create_app(Settings.from_environment({}), session_factory=sessions)), tokens


def _create_draft(client: TestClient, headers: dict[str, str]) -> dict[str, object]:
    response = client.post("/api/work-orders/drafts", headers=headers, json={
        "diagnosis_request_id": "diagnosis-001", "asset_id": "cnc-demo-001", "title": "检查主轴", "description": "依据诊断创建", "priority": "high",
    })
    assert response.status_code == 202
    return response.json()


def test_work_order_approval_is_role_protected_idempotent_and_audited() -> None:
    client, tokens = _prepared_client()
    draft = _create_draft(client, tokens["operator"])
    work_order_id = draft["work_order_id"]

    forbidden = client.post(f"/api/work-orders/{work_order_id}/approve", headers=tokens["operator"], json={"reason": "reviewed"})
    approved = client.post(f"/api/work-orders/{work_order_id}/approve", headers=tokens["approver"], json={"reason": "evidence reviewed"})
    repeated = client.post(f"/api/work-orders/{work_order_id}/approve", headers=tokens["approver"], json={"reason": "retry"})
    conflicting = client.post(f"/api/work-orders/{work_order_id}/reject", headers=tokens["admin"], json={"reason": "too late"})
    detail = client.get(f"/api/work-orders/{work_order_id}", headers=tokens["operator"])

    assert forbidden.status_code == 403
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"
    assert repeated.status_code == 200
    assert repeated.json()["status"] == "approved"
    assert conflicting.status_code == 409
    assert conflicting.json()["error"]["code"] == "approval_already_decided"
    assert detail.status_code == 200
    assert detail.json()["approval"]["decision"] == "approved"
    assert [item["action"] for item in detail.json()["transitions"]] == ["approve"]
    assert detail.json()["audit_actions"] == [
        "work_order.draft_created", "work_order.approval_requested", "workflow.interrupted", "workflow.resumed", "work_order.approved",
    ]


def test_work_order_lifecycle_requires_versions_roles_and_assignee() -> None:
    client, tokens = _prepared_client()
    draft = _create_draft(client, tokens["operator"])
    work_order_id = draft["work_order_id"]
    assert client.post(f"/api/work-orders/{work_order_id}/approve", headers=tokens["admin"], json={"reason": "approved"}).status_code == 200

    assigned = client.post(f"/api/work-orders/{work_order_id}/transitions", headers=tokens["admin"], json={
        "action": "assign", "expected_version": 2, "assignee_username": "technician", "reason": "assigned",
    })
    forbidden_start = client.post(f"/api/work-orders/{work_order_id}/transitions", headers=tokens["operator"], json={
        "action": "start", "expected_version": 3,
    })
    started = client.post(f"/api/work-orders/{work_order_id}/transitions", headers=tokens["technician"], json={
        "action": "start", "expected_version": 3,
    })
    completed = client.post(f"/api/work-orders/{work_order_id}/transitions", headers=tokens["technician"], json={
        "action": "complete", "expected_version": 4,
    })
    stale_close = client.post(f"/api/work-orders/{work_order_id}/transitions", headers=tokens["approver"], json={
        "action": "close", "expected_version": 4,
    })
    closed = client.post(f"/api/work-orders/{work_order_id}/transitions", headers=tokens["approver"], json={
        "action": "close", "expected_version": 5,
    })
    listed = client.get("/api/work-orders?status=closed&asset_id=cnc-demo-001", headers=tokens["operator"])

    assert assigned.status_code == 200
    assert assigned.json()["status"] == "assigned"
    assert forbidden_start.status_code == 409
    assert forbidden_start.json()["error"]["code"] == "invalid_work_order_transition"
    assert started.json()["status"] == "in_progress"
    assert completed.json()["status"] == "completed"
    assert stale_close.status_code == 409
    assert stale_close.json()["error"]["code"] == "stale_resource_version"
    assert closed.json()["status"] == "closed"
    assert listed.json()["total"] == 1


def test_approver_can_reject_a_draft_only_with_a_reason() -> None:
    client, tokens = _prepared_client()
    draft = _create_draft(client, tokens["operator"])
    work_order_id = draft["work_order_id"]

    missing_reason = client.post(f"/api/work-orders/{work_order_id}/reject", headers=tokens["approver"], json={})
    rejected = client.post(f"/api/work-orders/{work_order_id}/reject", headers=tokens["approver"], json={"reason": "evidence needs clarification"})

    assert missing_reason.status_code == 422
    assert rejected.status_code == 200
    assert rejected.json()["status"] == "cancelled"
