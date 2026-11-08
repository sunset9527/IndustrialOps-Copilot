from __future__ import annotations

from fastapi.testclient import TestClient

from industrialops.app_metadata import PRODUCT_NAME
from industrialops.config import Settings
from industrialops.api import create_app


def test_health_route_reports_the_industrialops_product_identity() -> None:
    client = TestClient(create_app(Settings.from_environment({})))

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "product": PRODUCT_NAME}


def test_ready_route_has_no_implicit_dependency_on_heritagemind_services() -> None:
    client = TestClient(create_app(Settings.from_environment({})))

    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready", "dependencies": []}


def test_unknown_route_uses_a_stable_non_leaking_error_contract() -> None:
    client = TestClient(create_app(Settings.from_environment({})))

    response = client.get("/missing-route")

    assert response.status_code == 404
    assert response.json() == {
        "error": {"code": "not_found", "message": "Resource not found"}
    }
