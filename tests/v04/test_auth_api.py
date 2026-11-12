from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from industrialops.api import create_app
from industrialops.config import Settings
from industrialops.database import Base
from industrialops.models.auth_session import AuthSession
from industrialops.models.audit import AuditEvent
from industrialops.services.auth import create_user


def _session_factory() -> sessionmaker[Session]:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    db = factory()
    user, error = create_user(db, "approver", "approver@example.com", "a long enough password")
    assert user is not None
    assert error is None
    user.role = "approver"
    db.commit()
    return factory


def test_login_returns_one_time_token_and_me_resolves_server_side_role() -> None:
    sessions = _session_factory()
    client = TestClient(create_app(Settings.from_environment({}), session_factory=sessions))

    login = client.post("/api/auth/login", json={"username": "approver", "password": "a long enough password"})

    assert login.status_code == 200
    body = login.json()
    token = body["access_token"]
    assert body["token_type"] == "bearer"
    assert body["user"] == {"username": "approver", "role": "approver"}
    db = sessions()
    assert token not in db.query(AuthSession).one().token_hash
    assert db.query(AuditEvent.action).all() == [("auth.login_succeeded",)]

    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json() == {"username": "approver", "role": "approver"}


def test_login_and_protected_route_use_stable_non_leaking_auth_errors() -> None:
    sessions = _session_factory()
    client = TestClient(create_app(Settings.from_environment({}), session_factory=sessions))

    failed_login = client.post("/api/auth/login", json={"username": "approver", "password": "wrong password"})
    missing_token = client.get("/api/auth/me")

    assert failed_login.status_code == 401
    assert failed_login.json() == {"error": {"code": "invalid_credentials", "message": "Invalid username or password"}}
    assert missing_token.status_code == 401
    assert missing_token.json() == {"error": {"code": "unauthorized", "message": "Authentication is required"}}
    db = sessions()
    assert db.query(AuditEvent.action).all() == [("auth.login_failed",)]
