from __future__ import annotations

from fastapi.testclient import TestClient

from industrialops.app_metadata import PRODUCT_NAME
from industrialops.config import Settings
from industrialops.api import create_app
from industrialops.readiness import DependencyStatus, ReadinessReport


def test_health_route_reports_the_industrialops_product_identity() -> None:
    client = TestClient(create_app(Settings.from_environment({})))

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "product": PRODUCT_NAME}


def test_ready_route_reports_the_injected_delivery_dependency_state() -> None:
    client = TestClient(create_app(
        Settings.from_environment({}),
        readiness_checker=lambda: ReadinessReport((
            DependencyStatus("database", "ready", None, "Database connection verified"),
        )),
    ))

    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "dependencies": [
            {"name": "database", "status": "ready", "code": None, "detail": "Database connection verified"},
        ],
    }


def test_unknown_route_uses_a_stable_non_leaking_error_contract() -> None:
    client = TestClient(create_app(Settings.from_environment({})))

    response = client.get("/missing-route")

    assert response.status_code == 404
    assert response.json() == {
        "error": {"code": "not_found", "message": "Resource not found"}
    }


def test_application_rejects_oversized_requests_before_route_handling() -> None:
    settings = Settings(
        api_port=8100,
        frontend_port=5174,
        database_url="sqlite:///./test.db",
        redis_key_prefix="industrialops:",
        request_max_bytes=10,
    )
    client = TestClient(create_app(settings))

    response = client.post("/health", content=b"12345678901")

    assert response.status_code == 413
    assert response.json() == {
        "error": {"code": "request_too_large", "message": "Request body exceeds the server limit"}
    }
