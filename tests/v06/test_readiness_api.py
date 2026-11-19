from __future__ import annotations

import json

from industrialops.api import create_app
from industrialops.config import Settings
from industrialops.readiness import DependencyStatus, ReadinessReport


def _ready_response(report: ReadinessReport):
    app = create_app(Settings.from_environment({}), readiness_checker=lambda: report)
    route = next(route for route in app.routes if getattr(route, "path", None) == "/ready")
    return route.endpoint()


def test_ready_returns_a_sanitized_503_report_when_a_required_dependency_is_unavailable() -> None:
    report = ReadinessReport(
        dependencies=(
            DependencyStatus("database", "not_ready", "DATABASE_UNAVAILABLE", "Database connection failed"),
            DependencyStatus("knowledge_packs", "ready", None, "Two frozen packs verified"),
        )
    )
    response = _ready_response(report)

    assert response.status_code == 503
    assert json.loads(response.body) == {
        "status": "not_ready",
        "dependencies": [
            {"name": "database", "status": "not_ready", "code": "DATABASE_UNAVAILABLE", "detail": "Database connection failed"},
            {"name": "knowledge_packs", "status": "ready", "code": None, "detail": "Two frozen packs verified"},
        ],
    }


def test_ready_returns_200_only_when_every_required_dependency_is_ready() -> None:
    report = ReadinessReport(
        dependencies=(DependencyStatus("database", "ready", None, "Database connection verified"),)
    )
    response = _ready_response(report)

    assert response.status_code == 200
    assert json.loads(response.body)["status"] == "ready"
