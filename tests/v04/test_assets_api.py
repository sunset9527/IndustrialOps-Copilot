from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from industrialops.api import create_app
from industrialops.config import Settings
from industrialops.database import Base
from industrialops.models.assets import EquipmentModel
from industrialops.models.audit import AuditEvent
from industrialops.models.user import User
from industrialops.services.auth_sessions import create_auth_session


def _prepared_client() -> tuple[TestClient, str, str, sessionmaker[Session]]:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine)
    db = sessions()
    db.add(EquipmentModel(equipment_model_id="haas-vf2-ngc", pack_id="cnc_pack_v1.0.0", manufacturer="Haas", model_name="VF-2"))
    admin = User(username="admin", email="admin@example.com", password_hash="hash", role="admin")
    user = User(username="user", email="user@example.com", password_hash="hash", role="user")
    db.add_all((admin, user))
    db.flush()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    admin_token, _ = create_auth_session(db, admin, expires_at=expires_at)
    user_token, _ = create_auth_session(db, user, expires_at=expires_at)
    db.commit()
    return TestClient(create_app(Settings.from_environment({}), session_factory=sessions)), admin_token, user_token, sessions


def test_assets_api_enforces_admin_writes_and_exposes_versioned_soft_retirement() -> None:
    client, admin_token, user_token, sessions = _prepared_client()
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    user_headers = {"Authorization": f"Bearer {user_token}"}
    payload = {"asset_id": "cnc-demo-001", "equipment_model_id": "haas-vf2-ngc", "display_name": "CNC 001"}

    forbidden = client.post("/api/equipment/assets", headers=user_headers, json=payload)
    created = client.post("/api/equipment/assets", headers=admin_headers, json=payload)
    listed = client.get("/api/equipment/assets?pack_id=cnc_pack_v1.0.0", headers=user_headers)
    retired = client.patch(
        "/api/equipment/assets/cnc-demo-001", headers=admin_headers,
        json={"expected_version": 1, "status": "out_of_service"},
    )

    assert forbidden.status_code == 403
    assert forbidden.json()["error"]["code"] == "forbidden"
    assert created.status_code == 201
    assert created.json()["synthetic"] is True
    assert listed.status_code == 200
    assert listed.json()["total"] == 1
    assert retired.status_code == 200
    assert retired.json()["status"] == "out_of_service"
    assert retired.json()["version"] == 2
    assert sessions().query(AuditEvent.action).all() == [("asset.created",), ("asset.updated",)]
