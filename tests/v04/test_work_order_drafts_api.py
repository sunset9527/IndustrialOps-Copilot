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


def test_work_order_draft_api_uses_persisted_diagnosis_instead_of_client_evidence() -> None:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine)
    db = sessions()
    user = User(username="operator", email="operator@example.com", password_hash="hash", role="user")
    db.add_all((
        user,
        EquipmentModel(equipment_model_id="haas-vf2-ngc", pack_id="cnc_pack_v1.0.0", manufacturer="Haas", model_name="VF-2"),
        Asset(asset_id="cnc-demo-001", equipment_model_id="haas-vf2-ngc", display_name="CNC 001", status="available", synthetic=True),
    ))
    db.flush()
    record_diagnosis(
        db, request_id="diagnosis-001", created_by_user_id=user.id, asset_id="cnc-demo-001", pack_id="cnc_pack_v1.0.0",
        model="VF-2", controller="NGC", status="answered", intent="fault_diagnosis", request_snapshot={},
        result_snapshot={"inspection_steps": ["检查主轴"]}, citations_snapshot=[{"source_id": "manual", "page_number": 42}],
        knowledge_pack_version="cnc_pack_v1.0.0",
    )
    token, _ = create_auth_session(db, user, expires_at=datetime.now(timezone.utc) + timedelta(hours=1))
    db.commit()
    client = TestClient(create_app(Settings.from_environment({}), session_factory=sessions))

    response = client.post("/api/work-orders/drafts", headers={"Authorization": f"Bearer {token}"}, json={
        "diagnosis_request_id": "diagnosis-001", "asset_id": "cnc-demo-001", "title": "检查主轴", "description": "用户描述", "priority": "high",
        "citations": [{"source_id": "forged"}],
    })

    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "draft"
    assert body["approval_status"] == "pending_approval"
    assert body["thread_id"]
    assert body["citations_snapshot"] == [{"source_id": "manual", "page_number": 42}]
