from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from industrialops.api import create_app
from industrialops.config import Settings
from industrialops.database import Base
from industrialops.diagnosis.schemas import DiagnosisResult


class RecordingWorkflow:
    def __init__(self) -> None:
        self.request: dict[str, object] | None = None

    def invoke(self, request: dict[str, object]) -> DiagnosisResult:
        self.request = request
        return DiagnosisResult(
            request_id=str(request["request_id"]),
            status="answered",
            intent="manual_query",
            confirmed_facts=("Evidence-backed fact",),
            generation={"provider": "evidence_fallback", "fallback_used": True},
            workflow_trace=("intent_router", "answer_composer"),
        )


def _session_factory() -> sessionmaker[Session]:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)


def test_diagnosis_query_route_invokes_the_injected_workflow_and_returns_the_stable_contract() -> None:
    workflow = RecordingWorkflow()
    client = TestClient(create_app(Settings.from_environment({}), diagnosis_workflow=workflow, session_factory=_session_factory()))

    response = client.post(
        "/api/diagnosis/query",
        json={"question": "查询 VF-2 手册", "pack_id": "cnc_pack_v1.0.0", "model": "VF-2"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "answered"
    assert body["confirmed_facts"] == ["Evidence-backed fact"]
    assert body["generation"] == {"provider": "evidence_fallback", "fallback_used": True}
    assert workflow.request is not None
    assert isinstance(workflow.request["request_id"], str)
    assert workflow.request["pack_id"] == "cnc_pack_v1.0.0"
