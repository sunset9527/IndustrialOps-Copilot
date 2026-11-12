from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from industrialops.api import create_app
from industrialops.config import Settings
from industrialops.database import Base
from industrialops.diagnosis.schemas import Citation, DiagnosisResult
from industrialops.models.assets import Asset, EquipmentModel
from industrialops.models.diagnosis import DiagnosisRecord


class AnsweredWorkflow:
    def invoke(self, request: dict[str, object]) -> DiagnosisResult:
        return DiagnosisResult(
            request_id=str(request["request_id"]), status="answered", intent="fault_diagnosis",
            inspection_steps=("隔离能量后检查主轴",), citations=(Citation(
                evidence_id="evidence-1", pack_id="cnc_pack_v1.0.0", source_id="haas-manual",
                document_revision="v1", page_number=42, evidence_locator="p42",
            ),), generation={"provider": "evidence_fallback", "fallback_used": True}, workflow_trace=("answer_composer",),
        )


def test_diagnosis_api_persists_the_returned_evidence_bound_snapshot() -> None:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine)
    db = sessions()
    db.add_all((
        EquipmentModel(equipment_model_id="haas-vf2-ngc", pack_id="cnc_pack_v1.0.0", manufacturer="Haas", model_name="VF-2"),
        Asset(asset_id="cnc-demo-001", equipment_model_id="haas-vf2-ngc", display_name="CNC 001", status="available", synthetic=True),
    ))
    db.commit()
    client = TestClient(create_app(Settings.from_environment({}), diagnosis_workflow=AnsweredWorkflow(), session_factory=sessions))

    response = client.post("/api/diagnosis/query", json={
        "question": "主轴异响", "pack_id": "cnc_pack_v1.0.0", "asset_id": "cnc-demo-001", "model": "VF-2",
    })

    assert response.status_code == 200
    record = db.get(DiagnosisRecord, 1)
    assert record is not None
    assert record.request_id == response.json()["request_id"]
    assert record.result_snapshot["inspection_steps"] == ["隔离能量后检查主轴"]
    assert record.citations_snapshot == [{
        "evidence_id": "evidence-1", "pack_id": "cnc_pack_v1.0.0", "source_id": "haas-manual",
        "document_revision": "v1", "page_number": 42, "evidence_locator": "p42",
    }]
